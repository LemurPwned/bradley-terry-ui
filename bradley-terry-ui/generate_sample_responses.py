import json
from itertools import combinations

N = 10

ids = [f"ID_{i}" for i in range(N)]
# randomly sample pairs
pairs = list(combinations(ids, 2))
# make sure pairs are unique
assert len(pairs) == N * (N - 1) / 2

with open("sample_responses.jsonl", "w") as f:
    for A, B in pairs:
        f.write(
            json.dumps(
                {
                    "prompt": "Which excerpt is more readable?",
                    "responseA": A,
                    "responseB": B,
                    "idA": A,
                    "idB": B,
                }
            )
            + "\n"
        )
