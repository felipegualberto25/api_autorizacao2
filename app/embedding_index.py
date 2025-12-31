import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
INDEX_DIR = "/app/data/vector_index"
THRESHOLD = float(os.environ.get("EMBEDDING_THRESHOLD", "0.75"))

class ProcedureEmbeddingIndex:

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(f"{INDEX_DIR}/procedures.index")

        with open(f"{INDEX_DIR}/procedures_meta.pkl", "rb") as f:
            self.meta = pickle.load(f)

    def query(self, text: str, top_k: int = 5):
        emb = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        distances, indices = self.index.search(emb, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            score = 1 - float(dist)  # HNSWFlat retorna distância L2
            if score >= THRESHOLD:
                proc = self.meta[idx]
                results.append({
                    "code": proc["code"],
                    "description": proc["desc"],
                    "score": score
                })

        return results
