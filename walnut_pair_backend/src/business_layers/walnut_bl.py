from src.domain_layers.services.embedding_service import ImageEmbeddingService
import numpy as np

class WalnutBL:
    def __init__(self):
        self.embedding_service = ImageEmbeddingService()

    def generate_pair_embedding(self, front_path: str, back_path: str):
        front_emb = self.embedding_service.generate(front_path)
        back_emb = self.embedding_service.generate(back_path)
        # Keep separate embeddings for comparison
        return front_emb, back_emb

    def similarity(self, emb1, emb2):
        """Cosine similarity"""
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        return float(np.dot(emb1, emb2))
