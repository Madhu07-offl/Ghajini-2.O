import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss
except ImportError:
    faiss = None
    logger.warning("faiss not installed; memory retrieval will use fallback")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logger.warning("sentence_transformers not installed; memory retrieval will use fallback")


class MemoryRetrieval:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self.embedding_dim: int = 384
        self.model_name = model_name
        self.model = None
        self.index = None
        self._fallback_vectors: Dict[int, np.ndarray] = {}
        self._init_faiss_index()
        self._init_model()

    def _init_faiss_index(self) -> None:
        if faiss is not None:
            base_index = faiss.IndexFlatIP(self.embedding_dim)
            self.index = faiss.IndexIDMap2(base_index)
        else:
            self.index = None

    def _init_model(self) -> None:
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded memory sentence transformer: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer ({self.model_name}): {e}. Using deterministic fallback.")
                self.model = None

    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return (vector / norm).astype(np.float32)

    def _fallback_embed(self, text: str) -> np.ndarray:
        # Deterministic multilingual hash-based embedding for offline / test safety
        words = text.lower().split()
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        for i, word in enumerate(words):
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 / (i + 1))
        return self._normalize(vec)

    def embed_text(self, text: str) -> np.ndarray:
        if self.model is not None:
            try:
                emb = self.model.encode(text, normalize_embeddings=True)
                return np.array(emb, dtype=np.float32)
            except Exception as e:
                logger.warning(f"SentenceTransformer encode failed: {e}. Using fallback embed.")
        return self._fallback_embed(text)

    def add_memory(self, memory_id: int, text: str, existing_embedding_json: Optional[Any] = None) -> List[float]:
        if existing_embedding_json is not None:
            if isinstance(existing_embedding_json, str):
                try:
                    emb_list = json.loads(existing_embedding_json)
                    norm_emb = self._normalize(np.array(emb_list, dtype=np.float32))
                except Exception:
                    norm_emb = self.embed_text(text)
            elif isinstance(existing_embedding_json, np.ndarray):
                norm_emb = self._normalize(existing_embedding_json)
            else:
                norm_emb = self.embed_text(text)
        else:
            norm_emb = self.embed_text(text)

        if self.index is not None:
            vec_2d = np.array([norm_emb], dtype=np.float32)
            id_arr = np.array([memory_id], dtype=np.int64)
            self.index.add_with_ids(vec_2d, id_arr)
        else:
            self._fallback_vectors[memory_id] = norm_emb

        return norm_emb.tolist()

    def search(self, query_text: str, k: int = 5) -> List[Tuple[int, float]]:
        """
        Returns list of (memory_id, similarity_score) sorted by descending similarity.
        """
        total = self.index.ntotal if self.index is not None else len(self._fallback_vectors)
        if total == 0:
            return []

        query_emb = self.embed_text(query_text)
        actual_k = min(k, total)

        if self.index is not None:
            q_2d = np.array([query_emb], dtype=np.float32)
            distances, ids = self.index.search(q_2d, actual_k)
            results = []
            for dist, mid in zip(distances[0], ids[0]):
                if mid != -1:
                    results.append((int(mid), float(dist)))
            return results
        else:
            scored = []
            for mid, vec in self._fallback_vectors.items():
                sim = float(np.dot(query_emb, vec))
                scored.append((mid, sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:actual_k]

    def remove_memory(self, memory_id: int) -> None:
        if self.index is not None:
            try:
                id_arr = np.array([memory_id], dtype=np.int64)
                self.index.remove_ids(id_arr)
            except Exception as e:
                logger.warning(f"Error removing memory {memory_id} from FAISS: {e}")
        self._fallback_vectors.pop(memory_id, None)

    def load_from_db(self, db_memories: List[Tuple[int, str, Optional[str]]]) -> None:
        """
        Populate index from database tuples: (id, text, embedding_json)
        """
        for mem_id, text, emb_json in db_memories:
            self.add_memory(mem_id, text, emb_json)

    def clear(self) -> None:
        self._fallback_vectors.clear()
        self._init_faiss_index()


memory_retrieval = MemoryRetrieval()
