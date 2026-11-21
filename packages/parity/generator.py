#!/usr/bin/env python3
"""
packages/parity/generator.py
Generate random action sequences from grammar.
Deterministic given the same seed — sequences can be reproduced.
"""
import json
import pathlib
import random
import sys
from dataclasses import dataclass, field

import yaml

ROOT = pathlib.Path(__file__).parent.parent.parent
GRAMMAR_DIR = pathlib.Path(__file__).parent / "grammar"


@dataclass
class Action:
    name: str
    params: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"action": self.name, "params": self.params}


def load_grammar(format_family: str) -> dict:
    grammar_path = GRAMMAR_DIR / f"{format_family}.yaml"
    if not grammar_path.exists():
        raise FileNotFoundError(f"No grammar for format '{format_family}': {grammar_path}")
    with open(grammar_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _sample_param(param_def: dict, rng: random.Random, context: dict) -> object:
    """Generate a random value for a parameter definition."""
    ptype = param_def.get("type", "string")

    if ptype == "integer":
        lo, hi = param_def.get("range", [0, 10])
        return rng.randint(lo, hi)

    elif ptype == "enum":
        return rng.choice(param_def.get("values", ["default"]))

    elif ptype == "string":
        source = param_def.get("from", "")
        if source == "sample_values" and context.get("sample_values"):
            return rng.choice(context["sample_values"])
        if source == "field_names" and context.get("field_names"):
            return rng.choice(context["field_names"])
        return f"value_{rng.randint(0, 999)}"

    return None


def generate_sequences(
    format_family: str,
    n: int = 1000,
    seed: int | None = None,
    context: dict | None = None,
    min_length: int = 1,
    max_length: int = 10,
) -> tuple[list[list[dict]], int]:
    """
    Generate n random action sequences.
    Returns (sequences, seed_used).
    seed_used lets REVENANT reproduce the exact sequences.
    """
    if seed is None:
        seed = random.randint(0, 2**32 - 1)

    rng = random.Random(seed)
    grammar = load_grammar(format_family)
    actions_def = grammar.get("actions", [])
    ctx = context or {}

    sequences = []
    for _ in range(n):
        length = rng.randint(min_length, max_length)
        sequence = []
        for _ in range(length):
            action_def = rng.choice(actions_def)
            params = {}
            for pname, pdef in action_def.get("params", {}).items():
                params[pname] = _sample_param(pdef, rng, ctx)
            sequence.append(Action(name=action_def["name"], params=params).to_dict())
        sequences.append(sequence)

    return sequences, seed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("format", choices=["csv", "dbf"])
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    seqs, used_seed = generate_sequences(args.format, n=args.n, seed=args.seed)
    out = {"seed": used_seed, "count": len(seqs), "sequences": seqs}

    if args.output == "-":
        print(json.dumps(out, indent=2))
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"[generator] {len(seqs)} sequences written to {args.output} (seed={used_seed})")
