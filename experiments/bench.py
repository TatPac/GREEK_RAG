from pathlib import Path
from datetime import datetime
import json
import math
import csv
import pickle
import ollama


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

# bench.py should live two levels below the project root,
# just like your current scripts.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "corpora" / "ready"

DATABASE_DIR = PROJECT_ROOT / "data" / "databases"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CORPUS_METADATA_PATH = DATA_DIR / "corpus.json"

with open(
    CORPUS_METADATA_PATH,
    "r",
    encoding="utf-8"
) as file:

    CORPUS = json.load(file)

CORPUS_NAME = CORPUS["corpus_name"]
CORPUS_ID = CORPUS["corpus_id"]
CORPUS_VERSION = CORPUS["version"]

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_DIR / "results"

CONFIG_PATH = EXPERIMENT_DIR / "config.json"
QUESTIONS_PATH = EXPERIMENT_DIR / "questions.json"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD CONFIGURATION
# ============================================================

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    CONFIG = json.load(file)


EMBEDDING_MODELS = CONFIG["embedding_models"]
CHUNK_SIZES = CONFIG["chunk_sizes"]
CHUNK_OVERLAPS = CONFIG["chunk_overlaps"]
TOP_N_VALUES = CONFIG["top_n"]
LANGUAGE_MODELS = CONFIG["language_models"]


# ============================================================
# LOAD QUESTIONS
# ============================================================

with open(QUESTIONS_PATH, "r", encoding="utf-8") as file:
    QUESTIONS = json.load(file)


# ============================================================
# TIMESTAMP
# ============================================================

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

RUN_NAME = f"{CORPUS_ID}_{TIMESTAMP}"

RUN_DIR = RESULTS_DIR / RUN_NAME
RUN_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# INFORMATION
# ============================================================

print()
print("=" * 70)
print("RAG BENCHMARK")
print("=" * 70)

print(f"Questions:        {len(QUESTIONS)}")
print(f"Embedding models: {len(EMBEDDING_MODELS)}")
print(f"Chunk sizes:      {CHUNK_SIZES}")
print(f"Chunk overlaps:   {CHUNK_OVERLAPS}")
print(f"Top-N values:     {TOP_N_VALUES}")
print(f"Language models:  {LANGUAGE_MODELS}")
print(f"Results:          {RUN_DIR}")

print("=" * 70)
print()


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )

    norm_a = math.sqrt(
        sum(x ** 2 for x in a)
    )

    norm_b = math.sqrt(
        sum(x ** 2 for x in b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(data_dir, chunk_size, chunk_overlap):

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    step = chunk_size - chunk_overlap

    dataset = []

    for file_path in sorted(data_dir.glob("*.txt")):

        print(f"Loading: {file_path.name}")

        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        for start in range(0, len(text), step):

            end = start + chunk_size

            chunk = text[start:end]

            if chunk.strip():

                dataset.append(
                    (
                        file_path.name,
                        chunk
                    )
                )

            if end >= len(text):
                break

    return dataset


# ============================================================
# CREATE VECTOR DATABASE
# ============================================================

def create_vector_database(dataset, embedding_model):

    vector_db = []

    total = len(dataset)

    print()
    print(
        f"Generating embeddings with "
        f"{embedding_model}"
    )

    for i, (filename, chunk) in enumerate(dataset):

        try:

            response = ollama.embed(
                model=embedding_model,
                input=chunk
            )

            embedding = response["embeddings"][0]

            vector_db.append(
                (
                    filename,
                    chunk,
                    embedding
                )
            )

            print(
                f"\rEmbedding "
                f"{i + 1}/{total}",
                end="",
                flush=True
            )

        except Exception as e:

            print()

            print(
                f"ERROR embedding chunk "
                f"{i + 1} from {filename}: {e}"
            )

    print()

    return vector_db

# ============================================================
# LOAD OR CREATE VECTOR DATABASE
# ============================================================

def get_vector_database(
    dataset,
    embedding_model,
    chunk_size,
    chunk_overlap
):

    safe_embedding_model = (
        embedding_model
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )

    database_name = (
        f"{CORPUS_ID}"
        f"__{safe_embedding_model}"
        f"__chunk{chunk_size}"
        f"__overlap{chunk_overlap}"
        f".pkl"
    )

    database_path = DATABASE_DIR / database_name

    # --------------------------------------------------------
    # LOAD EXISTING DATABASE
    # --------------------------------------------------------

    if database_path.exists():

        print()
        print(
            f"Loading existing database:"
        )

        print(
            f"  {database_path.name}"
        )

        with open(
            database_path,
            "rb"
        ) as file:

            vector_db = pickle.load(file)

        print(
            f"Loaded "
            f"{len(vector_db)} embeddings."
        )

        return vector_db

    # --------------------------------------------------------
    # CREATE NEW DATABASE
    # --------------------------------------------------------

    print()
    print(
        "Database not found."
    )

    print(
        "Generating embeddings..."
    )

    vector_db = create_vector_database(
        dataset,
        embedding_model
    )

    # --------------------------------------------------------
    # SAVE DATABASE
    # --------------------------------------------------------

    with open(
        database_path,
        "wb"
    ) as file:

        pickle.dump(
            vector_db,
            file
        )

    print()
    print(
        f"Saved database:"
    )

    print(
        f"  {database_path}"
    )

    return vector_db

# ============================================================
# RETRIEVE
# ============================================================

def retrieve(
    query,
    vector_db,
    embedding_model,
    top_n
):

    query_embedding = ollama.embed(
        model=embedding_model,
        input=query
    )["embeddings"][0]

    similarities = []

    for filename, chunk, embedding in vector_db:

        similarity = cosine_similarity(
            query_embedding,
            embedding
        )

        similarities.append(
            {
                "filename": filename,
                "chunk": chunk,
                "similarity": similarity
            }
        )

    similarities.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return similarities[:top_n]


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(
    question,
    retrieved_knowledge,
    language_model
):

    context = "\n".join(
        [
            (
                f"[{item['filename']}]\n"
                f"{item['chunk']}"
            )
            for item in retrieved_knowledge
        ]
    )

    instruction_prompt = f"""You are a helpful assistant specializing in
Koine Greek.

Use only the following retrieved context to answer the user's question.
Do not make up information that is not supported by the context.

Context:
{context}
"""

    response = ollama.chat(
        model=language_model,
        messages=[
            {
                "role": "system",
                "content": instruction_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response["message"]["content"]


# ============================================================
# SAVE HUMAN-READABLE RESULT
# ============================================================

def save_text_result(
    file,
    experiment_number,
    embedding_model,
    language_model,
    chunk_size,
    chunk_overlap,
    top_n,
    question,
    retrieved,
    answer
):

    file.write("\n")
    file.write("=" * 70 + "\n")
    file.write(
        f"EXPERIMENT {experiment_number}\n"
    )
    file.write("=" * 70 + "\n")

    file.write(
        f"Embedding model: {embedding_model}\n"
    )

    file.write(
        f"Language model:  {language_model}\n"
    )

    file.write(
        f"Chunk size:      {chunk_size}\n"
    )

    file.write(
        f"Chunk overlap:   {chunk_overlap}\n"
    )

    file.write(
        f"Top N:            {top_n}\n"
    )

    file.write("\n")
    file.write("QUESTION:\n")
    file.write(question + "\n")

    file.write("\n")
    file.write("-" * 70 + "\n")
    file.write("RETRIEVED KNOWLEDGE\n")
    file.write("-" * 70 + "\n")

    for rank, item in enumerate(retrieved, start=1):

        file.write("\n")
        file.write(
            f"RETRIEVED #{rank}\n"
        )

        file.write(
            f"Similarity: "
            f"{item['similarity']:.6f}\n"
        )

        file.write(
            f"Source: "
            f"{item['filename']}\n"
        )

        file.write("\n")
        file.write(item["chunk"])
        file.write("\n")

    file.write("\n")
    file.write("-" * 70 + "\n")
    file.write("GENERATED ANSWER\n")
    file.write("-" * 70 + "\n")

    file.write("\n")
    file.write(answer)
    file.write("\n\n")


# ============================================================
# MAIN BENCHMARK
# ============================================================

def main():

    all_results = []

    experiment_number = 0

    total_experiments = (
        len(EMBEDDING_MODELS)
        * len(CHUNK_SIZES)
        * len(CHUNK_OVERLAPS)
        * len(TOP_N_VALUES)
        * len(LANGUAGE_MODELS)
        * len(QUESTIONS)
    )

    print(
        f"Total experiments to run: "
        f"{total_experiments}"
    )

    print()

    text_results_path = (
        RUN_DIR / "answers.txt"
    )

    with open(
        text_results_path,
        "w",
        encoding="utf-8"
    ) as text_file:

        # ----------------------------------------------------
        # LOOP THROUGH ALL PARAMETERS
        # ----------------------------------------------------

        for embedding_model in EMBEDDING_MODELS:

            for chunk_size in CHUNK_SIZES:

                for chunk_overlap in CHUNK_OVERLAPS:

                    print()
                    print("=" * 70)

                    print(
                        f"Creating chunks:"
                    )

                    print(
                        f"  Size:    {chunk_size}"
                    )

                    print(
                        f"  Overlap: {chunk_overlap}"
                    )

                    print("=" * 70)

                    dataset = create_chunks(
                        DATA_DIR,
                        chunk_size,
                        chunk_overlap
                    )

                    print(
                        f"Created "
                        f"{len(dataset)} chunks."
                    )

                    # ----------------------------------------
                    # EMBEDDINGS
                    # ----------------------------------------

                    vector_db = get_vector_database(
                        dataset,
                        embedding_model,
                        chunk_size,
                        chunk_overlap
                    )

                    print(
                        f"Using "
                        f"{len(vector_db)} embeddings."
                    )

                    # ----------------------------------------
                    # QUESTIONS
                    # ----------------------------------------

                    for language_model in LANGUAGE_MODELS:

                        for top_n in TOP_N_VALUES:

                            for question in QUESTIONS:

                                experiment_number += 1

                                print()
                                print(
                                    "=" * 70
                                )

                                print(
                                    f"Experiment "
                                    f"{experiment_number}/"
                                    f"{total_experiments}"
                                )

                                print(
                                    f"Embedding: "
                                    f"{embedding_model}"
                                )

                                print(
                                    f"Chunk: "
                                    f"{chunk_size}"
                                )

                                print(
                                    f"Overlap: "
                                    f"{chunk_overlap}"
                                )

                                print(
                                    f"Top N: "
                                    f"{top_n}"
                                )

                                print(
                                    f"Question: "
                                    f"{question}"
                                )

                                print(
                                    "=" * 70
                                )

                                # ----------------------------
                                # RETRIEVAL
                                # ----------------------------

                                retrieved = retrieve(
                                    question,
                                    vector_db,
                                    embedding_model,
                                    top_n
                                )

                                # ----------------------------
                                # GENERATION
                                # ----------------------------

                                try:

                                    answer = generate_answer(
                                        question,
                                        retrieved,
                                        language_model
                                    )

                                except Exception as e:

                                    answer = (
                                        "ERROR generating answer: "
                                        f"{e}"
                                    )

                                # ----------------------------
                                # SAVE HUMAN RESULT
                                # ----------------------------

                                save_text_result(
                                    text_file,
                                    experiment_number,
                                    embedding_model,
                                    language_model,
                                    chunk_size,
                                    chunk_overlap,
                                    top_n,
                                    question,
                                    retrieved,
                                    answer
                                )

                                text_file.flush()

                                # ----------------------------
                                # SAVE MACHINE RESULT
                                # ----------------------------

                                result = {
                                    "experiment_number":
                                        experiment_number,

                                    "embedding_model":
                                        embedding_model,

                                    "language_model":
                                        language_model,

                                    "chunk_size":
                                        chunk_size,

                                    "chunk_overlap":
                                        chunk_overlap,

                                    "top_n":
                                        top_n,

                                    "question":
                                        question,

                                    "retrieved":
                                        retrieved,

                                    "answer":
                                        answer
                                }

                                all_results.append(result)

    # ========================================================
    # SAVE JSON
    # ========================================================

    json_path = RUN_DIR / "results.json"

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_results,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # SAVE CSV SUMMARY
    # ========================================================

    csv_path = RUN_DIR / "results.csv"

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            [
                "experiment",
                "embedding_model",
                "language_model",
                "chunk_size",
                "chunk_overlap",
                "top_n",
                "question",
                "top_similarity",
                "answer"
            ]
        )

        for result in all_results:

            retrieved = result["retrieved"]

            if retrieved:
                top_similarity = (
                    retrieved[0]["similarity"]
                )
            else:
                top_similarity = None

            writer.writerow(
                [
                    result["experiment_number"],
                    result["embedding_model"],
                    result["language_model"],
                    result["chunk_size"],
                    result["chunk_overlap"],
                    result["top_n"],
                    result["question"],
                    top_similarity,
                    result["answer"]
                ]
            )

    # ========================================================
    # SAVE CONFIG USED
    # ========================================================

    config_copy_path = RUN_DIR / "config.json"

    with open(
        config_copy_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            CONFIG,
            file,
            indent=4
        )

    # ========================================================
    # SAVE QUESTIONS USED
    # ========================================================

    questions_copy_path = RUN_DIR / "questions.json"

    with open(
        questions_copy_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            QUESTIONS,
            file,
            indent=4,
            ensure_ascii=False
        )

    # ========================================================
    # FINISHED
    # ========================================================

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)

    print(
        f"Experiments completed: "
        f"{len(all_results)}"
    )

    print(
        f"Results directory:\n"
        f"{RUN_DIR}"
    )

    print()
    print(
        f"Human-readable results:\n"
        f"{text_results_path}"
    )

    print(
        f"JSON results:\n"
        f"{json_path}"
    )

    print(
        f"CSV summary:\n"
        f"{csv_path}"
    )

    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()