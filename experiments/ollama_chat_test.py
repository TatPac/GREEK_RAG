from pathlib import Path
import pickle
import ollama


# --------------------------------------------------
# Locate project directories
# --------------------------------------------------


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_ROOT / "data" / "databases"
DATABASE_PATH = DATABASE_DIR / "sblgnt_v001__yxchia_multilingual-e5-base_latest__chunk1000__overlap100.pkl"


# --------------------------------------------------
# Models
# --------------------------------------------------

EMBEDDING_MODEL = "yxchia/multilingual-e5-base:latest"
LANGUAGE_MODEL = "qwen3:4b"


# --------------------------------------------------
# Load vector database
# --------------------------------------------------

with open(DATABASE_PATH, "rb") as file:
    VECTOR_DB = pickle.load(file)

print(f"Loaded {len(VECTOR_DB)} embeddings.")


# --------------------------------------------------
# Cosine similarity
# --------------------------------------------------

def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))

    norm_a = sum(x ** 2 for x in a) ** 0.5
    norm_b = sum(x ** 2 for x in b) ** 0.5

    return dot_product / (norm_a * norm_b)


# --------------------------------------------------
# Retrieve relevant chunks
# --------------------------------------------------

def retrieve(query, top_n=3):

    query_embedding = ollama.embed(
        model=EMBEDDING_MODEL,
        input=query
    )["embeddings"][0]

    similarities = []

    for filename, chunk, embedding in VECTOR_DB:

        similarity = cosine_similarity(
            query_embedding,
            embedding
        )

        similarities.append(
            (filename, chunk, similarity)
        )

    similarities.sort(
        key=lambda x: x[2],
        reverse=True
    )

    return similarities[:top_n]


# --------------------------------------------------
# Ask a question
# --------------------------------------------------

input_query = input("Ask me a question: ")

retrieved_knowledge = retrieve(input_query)


# --------------------------------------------------
# Display retrieved knowledge
# --------------------------------------------------

print("\nRetrieved knowledge:")

for filename, chunk, similarity in retrieved_knowledge:

    print(
        f"\n[{filename}] "
        f"(similarity: {similarity:.3f})"
    )

    print(chunk)


# --------------------------------------------------
# Build context for the LLM
# --------------------------------------------------

context = "\n".join(
    [
        f"[{filename}]\n{chunk}"
        for filename, chunk, similarity in retrieved_knowledge
    ]
)


# --------------------------------------------------
# Generate answer
# --------------------------------------------------

instruction_prompt = f"""You are a helpful assistant specializing in
Koine Greek.

Use only the following retrieved context to answer the user's question.
Do not make up information that is not supported by the context.

Context:
{context}
"""


stream = ollama.chat(
    model=LANGUAGE_MODEL,
    messages=[
        {
            "role": "system",
            "content": instruction_prompt
        },
        {
            "role": "user",
            "content": input_query
        },
    ],
    stream=True,
)


# --------------------------------------------------
# Display response
# --------------------------------------------------

print("\nChatbot response:")

for chunk in stream:
    print(
        chunk["message"]["content"],
        end="",
        flush=True
    )

print()