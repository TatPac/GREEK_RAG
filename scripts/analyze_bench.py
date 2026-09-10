import json
from pathlib import Path
from collections import defaultdict
import statistics
from matplotlib.pylab import exp
import matplotlib.pyplot as plt




results_dir = Path("experiments/results")
run = "sblgnt_v001_2026-08-29_13-44-50"

file_path = results_dir / run / "results.json"

with open(file_path, "r", encoding="utf-8") as file:
    RESULTS = json.load(file)

experiment_number = []
embedding_model = []
language_model = []
chunk_size = []
chunk_overlap = []
top_n = []
question = []
retrieved = []
answer = []

class Experiment:
    def __init__(self, experiment_number, embedding_model, language_model, chunk_size, chunk_overlap, top_n, question, retrieved, answer):
        self.experiment_number = experiment_number
        self.embedding_model = embedding_model
        self.language_model = language_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_n = top_n
        self.question = question
        self.retrieved = retrieved
        self.answer = answer

divide_by = []
x_value = []
y_value = []


def extract_values(RESULTS):
    for experiment in RESULTS:
        experiment_number.append(experiment["experiment_number"])
        embedding_model.append(experiment["embedding_model"])
        language_model.append(experiment["language_model"])
        chunk_size.append(experiment["chunk_size"])
        chunk_overlap.append(experiment["chunk_overlap"])
        top_n.append(experiment["top_n"])
        question.append(experiment["question"])
        retrieved.append(experiment["retrieved"])
        answer.append(experiment["answer"])

    print(
        experiment_number,
        chunk_size,
        chunk_overlap,
        top_n
    )

def make_classes(RESULTS):

    experiments = []
    for experiment in RESULTS:
        exp = Experiment(
            experiment_number=experiment["experiment_number"],
            embedding_model=experiment["embedding_model"],
            language_model=experiment["language_model"],
            chunk_size=experiment["chunk_size"],
            chunk_overlap=experiment["chunk_overlap"],
            top_n=experiment["top_n"],
            question=experiment["question"],
            retrieved=experiment["retrieved"],
            answer=experiment["answer"]
        )
        experiments.append(exp)

    return experiments

# This function divides the experiments based on the specified attribute (divide_by) and returns a list of experiments sorted by that attribute.
# I haven't finished it yet, I believe I need to delete the if statements and just sort the experiments based on the attribute specified in divide_by. 
# I will also need to handle the case where divide_by is a list of values to filter by, rather than just a single attribute.

def divide_experimennts(experiments, divide_by):
    if divide_by(0) == "chunk_size":
        for value in divide_by[1:]:
            x_val = [
                experiment for experiment in experiments if getattr(experiment, divide_by(0)) == value
            ]
            x_value.append(x_val)
    elif divide_by(0) == "chunk_overlap":
        experiments.sort(key=lambda x: x.chunk_overlap)
    elif divide_by(0) == "top_n":
        experiments.sort(key=lambda x: x.top_n)
    elif divide_by(0) == "embedding_model":
        experiments.sort(key=lambda x: x.embedding_model)
    elif divide_by(0) == "language_model":
        experiments.sort(key=lambda x: x.language_model)
    else:
        print("Invalid divide_by value. No sorting applied.")

    return experiments


def plot_results():
    
    plot_data = defaultdict(list)

def main():
    extract_values(RESULTS)


if __name__ == "__main__":
    main()