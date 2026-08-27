from pathlib import Path
from datetime import datetime
import json
import pickle
import ollama


# --------------------------------------------------
# Locate project directories
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "corpora" / "ready"
DATABASE_DIR = PROJECT_ROOT / "data" / "databases"

# Create database directory if it doesn't exist
DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Models
# --------------------------------------------------

EMBEDDING_MODEL = "qwen3-embedding:0.6b"
LANGUAGE_MODEL = "qwen3:4b"


# --------------------------------------------------
# Load all TXT files
# --------------------------------------------------

dataset = []

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400
STEP = CHUNK_SIZE - CHUNK_OVERLAP

for file_path in sorted(DATA_DIR.glob("*.txt")):

    print(f"Loading: {file_path.name}")

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    for start in range(0, len(text), STEP):

        end = start + CHUNK_SIZE

        chunk = text[start:end]

        if chunk.strip():
            dataset.append((file_path.name, chunk))

        if end >= len(text):
            break

print(f"Created {len(dataset)} chunks from {DATA_DIR}")

# --------------------------------------------------
# Create vector database
# --------------------------------------------------

# Each element:
# (filename, chunk, embedding)

VECTOR_DB = []


def add_chunk_to_database(filename, chunk):

    embedding = ollama.embed(
        model=EMBEDDING_MODEL,
        input=chunk
    )["embeddings"][0]

    VECTOR_DB.append((filename, chunk, embedding))


# --------------------------------------------------
# Generate embeddings
# --------------------------------------------------

for i, (filename, chunk) in enumerate(dataset):

    try:

        add_chunk_to_database(filename, chunk)

        print(
            f"Added chunk {i + 1}/{len(dataset)} "
            f"to the database"
        )

    except Exception as e:

        print(
            f"ERROR embedding chunk {i + 1} "
            f"from {filename}: {e}"
        )


# --------------------------------------------------
# Save database
# --------------------------------------------------

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

database_name = (
    f"sblgnt_{EMBEDDING_MODEL.replace(':', '-')}_{timestamp}"
)

database_path = DATABASE_DIR / f"{database_name}.pkl"
metadata_path = DATABASE_DIR / f"{database_name}.json"


with open(database_path, "wb") as file:
    pickle.dump(VECTOR_DB, file)


# --------------------------------------------------
# Save metadata
# --------------------------------------------------

source_files = sorted(
    set(filename for filename, chunk in dataset)
)

metadata = {
    "database_name": database_name,
    "created": datetime.now().isoformat(timespec="seconds"),
    "embedding_model": EMBEDDING_MODEL,
    "language_model": LANGUAGE_MODEL,
    "corpus": "SBLGNT",
    "source_directory": str(DATA_DIR),
    "source_files": source_files,
    "total_entries": len(dataset),
    "embedded_entries": len(VECTOR_DB),
}


with open(metadata_path, "w", encoding="utf-8") as file:
    json.dump(metadata, file, indent=4)


# --------------------------------------------------
# Finished
# --------------------------------------------------

print()
print("========================================")
print("Embedding complete!")
print("========================================")
print(f"Database: {database_path}")
print(f"Metadata: {metadata_path}")
print(f"Embedded entries: {len(VECTOR_DB)}")