
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.rag.retriever import SemanticRetriever

question = "What are the risk factors for melanoma?"

print("\nLoading original SentenceTransformer model...")
original_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("\nGenerating original embedding...")
original_vector = original_model.encode(
    question,
    normalize_embeddings=True,
    convert_to_numpy=True,
)

print("\nLoading our current retriever...")
retriever = SemanticRetriever()

print("\nGenerating current embedding...")
current_vector = retriever.embed_query(question)

difference = np.max(
    np.abs(original_vector - current_vector)
)

similarity = np.dot(
    original_vector,
    current_vector
)

print("\n===== COMPATIBILITY TEST =====")
print("Original shape:", original_vector.shape)
print("Current shape:", current_vector.shape)
print("Maximum absolute difference:", difference)
print("Cosine similarity:", similarity)

if difference < 0.0001:
    print("RESULT: PASS - Embeddings are compatible!")
else:
    print("RESULT: REVIEW - Embeddings differ.")
