#!/usr/bin/env python3
"""
packages/parity/shrinker.py
Shrink a failing action sequence to the minimal counterexample.
Uses delta debugging (ddmin algorithm).
"""
from typing import Callable


def ddmin(sequence: list, predicate: Callable[[list], bool]) -> list:
    """
    Delta debugging: find minimal subsequence that still fails predicate.
    predicate(seq) returns True if seq triggers the failure.
    """
    if not predicate(sequence):
        return sequence  # Precondition: original must fail

    n = 2
    while len(sequence) >= 2:
        subsets = _partition(sequence, n)
        reduced = False

        for subset in subsets:
            complement = [x for x in sequence if x not in subset]
            if predicate(complement):
                sequence = complement
                n = max(n - 1, 2)
                reduced = True
                break

        if not reduced:
            if n == len(sequence):
                break
            n = min(n * 2, len(sequence))

    # Final: try removing one element at a time
    changed = True
    while changed:
        changed = False
        for i in range(len(sequence)):
            candidate = sequence[:i] + sequence[i+1:]
            if candidate and predicate(candidate):
                sequence = candidate
                changed = True
                break

    return sequence


def _partition(lst: list, n: int) -> list[list]:
    """Partition list into n roughly equal parts."""
    size = max(1, len(lst) // n)
    return [lst[i:i+size] for i in range(0, len(lst), size)]


def shrink_sequence(
    failing_sequence: list[dict],
    run_sequence_fn: Callable[[list[dict]], dict],
    is_failure_fn: Callable[[dict], bool],
) -> list[dict]:
    """
    Shrink a failing action sequence to minimum.

    Args:
        failing_sequence: The sequence that triggers a parity failure.
        run_sequence_fn: Function that executes a sequence and returns comparison result.
        is_failure_fn: Function that checks if a comparison result is still a failure.

    Returns:
        Minimal sequence that still triggers the failure.
    """
    def predicate(seq: list) -> bool:
        if not seq:
            return False
        result = run_sequence_fn(seq)
        return is_failure_fn(result)

    if not predicate(failing_sequence):
        return failing_sequence  # Can't reproduce — return original

    minimal = ddmin(failing_sequence, predicate)
    return minimal


if __name__ == "__main__":
    # Demo: shrink a list of numbers to those that cause sum > 10
    example = [1, 2, 3, 4, 5, 6]

    def demo_predicate(seq):
        return sum(seq) > 10

    result = ddmin(example, demo_predicate)
    print(f"Original: {example} (sum={sum(example)})")
    print(f"Minimal:  {result} (sum={sum(result)})")
