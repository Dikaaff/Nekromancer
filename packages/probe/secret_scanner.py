#!/usr/bin/env python3
"""
packages/probe/secret_scanner.py
Scan file content for secrets / credentials before writing (S-9).
Used by guard-secrets hook (PreToolUse).

exit 0 = clean
exit 2 = secret found (hook blocks write)
"""
import json
import re
import sys

_SECRET_PATTERNS = {
    "GENERIC_API_KEY":   re.compile(r"(?i)(api[_\-]?key|api[_\-]?secret)\s*[=:]\s*['\"]?[a-zA-Z0-9_\-]{16,}"),
    "BEARER_TOKEN":      re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    "AWS_KEY":           re.compile(r"AKIA[0-9A-Z]{16}"),
    "GITHUB_TOKEN":      re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "PRIVATE_KEY_BLOCK": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "DB_PASSWORD":       re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{8,}"),
    "ENV_SECRET":        re.compile(r"(?i)(secret[_\-]?key|jwt[_\-]?secret)\s*[=:]\s*['\"]?[^\s'\"]{8,}"),
}


def scan(content: str) -> list[dict]:
    findings = []
    for name, pattern in _SECRET_PATTERNS.items():
        for m in pattern.finditer(content):
            snippet = m.group()[:60] + ("..." if len(m.group()) > 60 else "")
            # Mask middle
            masked = snippet[:8] + "****" + snippet[-4:] if len(snippet) > 12 else "****"
            findings.append({"type": name, "masked": masked, "line": content[:m.start()].count("\n") + 1})
    return findings


def main():
    # Accept content from --stdin flag (used by guard-secrets hook)
    if "--stdin" in sys.argv:
        # Hook passes JSON on stdin: {"tool": ..., "arguments": {"text": ...}}
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw)
            # Extract the text being written
            args = payload.get("arguments", {})
            content = args.get("text", "") or args.get("newStr", "") or str(args)
        except json.JSONDecodeError:
            content = raw
    elif len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    findings = scan(content)

    if findings:
        print(f"❌ SECRETS DETECTED — blocking write ({len(findings)} finding(s)):", file=sys.stderr)
        for f in findings:
            print(f"  [{f['type']}] line {f['line']}: {f['masked']}", file=sys.stderr)
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
