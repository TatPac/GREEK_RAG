import json
from pathlib import Path
from collections import defaultdict
import statistics
from matplotlib.pylab import exp
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(PROJECT_ROOT / "experiments" / "results" / "sblgnt_v001_2026-08-29_13-44-50" / "results.csv")
plt.figure()
df.groupby("chunk_size")["top_similarity"].mean().plot(kind="bar", title="Average Top Similarity by Chunk Size")
plt.figure()
df.groupby("embedding_model")["top_similarity"].mean().plot(kind="bar", title="Average Top Similarity by Embedding Model")

df.groupby(["embedding_model", "chunk_size", "chunk_overlap"])["top_similarity"].mean().unstack("embedding_model").plot(kind="line", title="Average Top Similarity by Embedding Model, Chunk Size, and Chunk Overlap")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
df.groupby(["embedding_model", "chunk_size", "chunk_overlap"])["top_similarity"].mean().unstack("chunk_size").plot(kind="line", title="Average Top Similarity by Embedding Model, Chunk Size, and Chunk Overlap")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
df.groupby(["embedding_model", "chunk_size", "chunk_overlap"])["top_similarity"].mean().unstack("chunk_overlap").plot(kind="line", title="Average Top Similarity by Embedding Model, Chunk Size, and Chunk Overlap")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

plt.show()

