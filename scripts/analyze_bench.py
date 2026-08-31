import json
from pathlib import Path
from collections import defaultdict
import statistics
import matplotlib.pyplot as plt




results_dir = Path("experiments/results")
run = "2026-08-30_21-15-42"

file_path = results_dir / run / "results.json"

with open(file_path, "r", encoding="utf-8") as file:
    results = json.load(file)
