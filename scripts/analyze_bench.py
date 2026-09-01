import json
from pathlib import Path
from collections import defaultdict
import statistics
import matplotlib.pyplot as plt




results_dir = Path("experiments/results")
run = "sblgnt_v001_2026-08-29_13-44-50"

file_path = results_dir / run / "results.json"

with open(file_path, "r", encoding="utf-8") as file:
    RESULTS = json.load(file)

def extract_values(RESULTS):
    for experiment in RESULTS:
        experiment_number = experiment["experiment_number"]
        embedding_model = experiment["embedding_model"]
        language_model = experiment["language_model"]
        chunk_size = experiment["chunk_size"]
        chunk_overlap = experiment["chunk_overlap"]
        top_n = experiment["top_n"]
        question = experiment["question"]
        retrieved = experiment["retrieved"]
        answer = experiment["answer"]

        print(
            experiment_number,
            chunk_size,
            chunk_overlap,
            top_n
        )

def main():
    extract_values(RESULTS)


if __name__ == "__main__":
    main()