#!/usr/bin/env bash
# packages/probe/sandbox.sh
# Docker sandbox wrapper for artifact execution (S-1, S-3, S-4).
#
# Usage: sandbox.sh <artifact_path> <output_dir> <codec_command>
# Example: sandbox.sh /input/data.csv /output python /app/codec/csv_codec.py /input/data.csv
#
# Security config:
#   --network none          No network access from artifact
#   --read-only             Root FS is read-only
#   --tmpfs /tmp:size=64m   Only /tmp is writable, 64MB max
#   --cap-drop ALL          Drop all Linux capabilities
#   --security-opt no-new-privileges  Prevent privilege escalation
#   --pids-limit 128        Limit process spawning
#   --memory 512m           Hard memory limit
#   --cpus 1                Single CPU
#   --user nobody           Non-root user

set -euo pipefail

ARTIFACT_PATH="${1:?Usage: sandbox.sh <artifact_path> <output_dir> <codec...>}"
OUTPUT_DIR="${2:?Missing output_dir}"
shift 2
CODEC_CMD=("$@")

TIMEOUT_SECONDS=120  # Hard limit (NF-1)
IMAGE="nekromancer-probe:latest"  # Build this image separately

# Canonicalize output dir (S-4)
OUTPUT_DIR="$(realpath "$OUTPUT_DIR")"
ARTIFACT_PATH="$(realpath "$ARTIFACT_PATH")"

# Verify artifact is not outside allowed input directories
INPUT_BASE="$(realpath "$(dirname "$0")/../../fixtures")"
if [[ "$ARTIFACT_PATH" != "$INPUT_BASE"* ]]; then
    # Also allow dossiers input path
    DOSSIERS_BASE="$(realpath "$(dirname "$0")/../../dossiers")"
    if [[ "$ARTIFACT_PATH" != "$DOSSIERS_BASE"* ]]; then
        echo "ERROR: Artifact path not within allowed input directories: $ARTIFACT_PATH" >&2
        exit 1
    fi
fi

mkdir -p "$OUTPUT_DIR"

echo "[sandbox] Starting probe: $(basename "$ARTIFACT_PATH")" >&2
echo "[sandbox] Timeout: ${TIMEOUT_SECONDS}s" >&2

timeout "$TIMEOUT_SECONDS" docker run \
    --rm \
    --network none \
    --read-only \
    --tmpfs /tmp:size=64m,exec \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --pids-limit 128 \
    --memory 512m \
    --cpus 1 \
    --user nobody \
    --volume "$ARTIFACT_PATH":/input/artifact:ro \
    --volume "$OUTPUT_DIR":/output:rw \
    --workdir /app \
    "$IMAGE" \
    "${CODEC_CMD[@]}" \
    2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "ERROR: PROBE_TIMEOUT — exceeded ${TIMEOUT_SECONDS}s" >&2
    exit 124
fi

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Sandbox exited with code $EXIT_CODE" >&2
    exit $EXIT_CODE
fi

echo "[sandbox] ✅ Probe complete" >&2
