from pathlib import Path
import json
import numpy as np

from sentence_transformers import SentenceTransformer


class SemanticRetriever:
    """
    Semantic retriever over all knowledge units.

    Uses:
    - knowledge_units.json
    - all_embeddings.npz

    Because the embeddings are normalized, cosine similarity
    is simply the dot product.
    """

    def __init__(
        self,
        knowledge_units_path: str = "data/processed/knowledge_units/knowledge_units.json",
        embeddings_path: str = "data/processed/embeddings/all_embeddings.npz",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.knowledge_units_path = Path(knowledge_units_path)
        self.embeddings_path = Path(embeddings_path)

        print("Loading knowledge units...")
        self.units = self._load_knowledge_units()

        print("Loading embeddings...")
        self.embeddings, self.embedding_chunk_ids = self._load_embeddings()

        self._validate_alignment()

        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        print("Retriever ready.")
        print(f"Knowledge units: {len(self.units):,}")
        print(f"Embeddings:     {len(self.embeddings):,}")
        print(f"Dimensions:     {self.embeddings.shape[1]}")

    def _load_knowledge_units(self):
        if not self.knowledge_units_path.exists():
            raise FileNotFoundError(
                f"Knowledge units file not found:\n"
                f"{self.knowledge_units_path}"
            )

        with open(self.knowledge_units_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # knowledge_units.json is currently a dictionary containing
        # the actual knowledge-unit list.
        if isinstance(data, list):
            units = data

        elif isinstance(data, dict):
            possible_keys = [
                "knowledge_units",
                "chunks",
                "units",
                "data",
            ]

            units = None

            for key in possible_keys:
                if isinstance(data.get(key), list):
                    units = data[key]
                    break

            # Fallback: find the first list containing dictionaries.
            if units is None:
                for value in data.values():
                    if isinstance(value, list) and value:
                        if isinstance(value[0], dict):
                            units = value
                            break

            if units is None:
                raise ValueError(
                    "Could not find knowledge-unit list in JSON file."
                )

        else:
            raise ValueError(
                "Unexpected knowledge_units.json structure."
            )

        if not units:
            raise ValueError("Knowledge unit list is empty.")

        return units

    def _load_embeddings(self):
        if not self.embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found:\n"
                f"{self.embeddings_path}"
            )

        data = np.load(self.embeddings_path, allow_pickle=False)

        if "embeddings" not in data:
            raise ValueError(
                "Embeddings NPZ does not contain an 'embeddings' array."
            )

        embeddings = data["embeddings"].astype(np.float32)

        if "chunk_ids" in data:
            chunk_ids = data["chunk_ids"]
        else:
            chunk_ids = None

        return embeddings, chunk_ids

    def _validate_alignment(self):
        """
        Make sure each embedding corresponds to exactly one knowledge unit.
        """

        if len(self.units) != len(self.embeddings):
            raise ValueError(
                "Knowledge-unit count and embedding count do not match.\n"
                f"Knowledge units: {len(self.units)}\n"
                f"Embeddings:      {len(self.embeddings)}"
            )

        if self.embedding_chunk_ids is not None:

            if len(self.embedding_chunk_ids) != len(self.units):
                raise ValueError(
                    "Embedding chunk-ID count does not match knowledge units."
                )

            # Verify the first few and last few IDs.
            check_indices = list(range(min(5, len(self.units))))

            if len(self.units) > 5:
                check_indices.extend(
                    range(max(0, len(self.units) - 5), len(self.units))
                )

            for i in check_indices:
                expected = str(self.units[i].get("chunk_id", ""))
                actual = str(self.embedding_chunk_ids[i])

                if expected != actual:
                    raise ValueError(
                        "Embedding alignment check failed.\n"
                        f"Index:    {i}\n"
                        f"Expected: {expected}\n"
                        f"Actual:   {actual}"
                    )

        print("Alignment check: OK")

    def embed_query(self, query: str) -> np.ndarray:
        """
        Convert a query into the same normalized embedding space
        used by the knowledge units.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        vector = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return vector.astype(np.float32)

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_type: str | None = None,
        document: str | None = None,
    ):
        """
        Search the knowledge base.

        Parameters
        ----------
        query:
            User's question.

        top_k:
            Number of results to return.

        document_type:
            Optional filter:
            patient_guideline
            oncology_reference

        document:
            Optional exact document filename filter.
        """

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_vector = self.embed_query(query)

        # Since both query and stored vectors are normalized,
        # dot product = cosine similarity.
        scores = self.embeddings @ query_vector

        candidate_indices = np.arange(len(self.units))

        # Optional document-type filtering.
        if document_type is not None:
            candidate_indices = np.array(
                [
                    i
                    for i in candidate_indices
                    if self.units[i].get("document_type")
                    == document_type
                ],
                dtype=np.int64,
            )

        # Optional exact document filtering.
        if document is not None:
            candidate_indices = np.array(
                [
                    i
                    for i in candidate_indices
                    if self.units[i].get("document")
                    == document
                ],
                dtype=np.int64,
            )

        if len(candidate_indices) == 0:
            return []

        candidate_scores = scores[candidate_indices]

        actual_k = min(top_k, len(candidate_indices))

        # Faster than sorting all 31k results.
        if actual_k < len(candidate_indices):
            partial = np.argpartition(
                -candidate_scores,
                actual_k - 1
            )[:actual_k]

            selected_indices = candidate_indices[partial]

            selected_scores = scores[selected_indices]

            order = np.argsort(
                -selected_scores
            )

            selected_indices = selected_indices[order]

        else:
            order = np.argsort(-candidate_scores)
            selected_indices = candidate_indices[order]

        results = []

        for rank, index in enumerate(selected_indices, start=1):

            unit = self.units[int(index)]

            result = {
                "rank": rank,
                "score": float(scores[int(index)]),
                "chunk_id": unit.get("chunk_id"),
                "document": unit.get("document"),
                "document_type": unit.get("document_type"),
                "title": unit.get("title"),
                "chapter": unit.get("chapter"),
                "section": unit.get("section"),
                "page_start": unit.get("page_start"),
                "page_end": unit.get("page_end"),
                "content_type": unit.get("content_type"),
                "text": unit.get("text", ""),
            }

            results.append(result)

        return results


def print_results(results):
    """
    Human-readable retrieval output for debugging.
    """

    print()
    print("=" * 80)
    print("RETRIEVAL RESULTS")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for result in results:

        print()
        print(f"Rank:       {result['rank']}")
        print(f"Score:      {result['score']:.4f}")
        print(f"Document:   {result['document']}")
        print(f"Type:       {result['document_type']}")
        print(f"Pages:      {result['page_start']}-{result['page_end']}")
        print(f"Chapter:    {result['chapter']}")
        print(f"Section:    {result['section']}")
        print(f"Chunk ID:    {result['chunk_id']}")

        text = result["text"].replace("\n", " ").strip()

        if len(text) > 500:
            text = text[:500] + "..."

        print(f"Text:       {text}")


if __name__ == "__main__":

    retriever = SemanticRetriever()

    questions = [
        "What is ductal carcinoma in situ?",
        "What are the symptoms of lung cancer?",
        "What are treatment options for breast cancer?",
        "What is Waldenstrom macroglobulinemia?",
        "What is skin cancer?",
    ]

    for question in questions:

        print()
        print("#" * 80)
        print(f"QUESTION: {question}")
        print("#" * 80)

        results = retriever.search(
            question,
            top_k=5,
        )

        print_results(results)