"""
Sistema de Embeddings Locales para R CLI.

Genera embeddings usando sentence-transformers 100% offline.
Soporta múltiples modelos optimizados para diferentes casos de uso.

Requisitos:
- sentence-transformers
- torch (CPU o GPU)
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np


@dataclass
class EmbeddingModel:
    """Configuración de un modelo de embeddings."""

    name: str
    model_id: str
    dimension: int
    description: str
    size_mb: int
    multilingual: bool = False
    max_seq_length: int = 512


# Modelos recomendados para diferentes casos de uso
EMBEDDING_MODELS = {
    # Modelos pequeños y rápidos
    "mini": EmbeddingModel(
        name="mini",
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        description="Rápido y ligero, ideal para CPU",
        size_mb=80,
        max_seq_length=256,
    ),
    "minilm": EmbeddingModel(
        name="minilm",
        model_id="sentence-transformers/all-MiniLM-L12-v2",
        dimension=384,
        description="Balance entre velocidad y calidad",
        size_mb=120,
        max_seq_length=256,
    ),
    # Modelos de alta calidad
    "mpnet": EmbeddingModel(
        name="mpnet",
        model_id="sentence-transformers/all-mpnet-base-v2",
        dimension=768,
        description="Alta calidad, mejor para búsqueda semántica",
        size_mb=420,
        max_seq_length=384,
    ),
    # Modelos multilingües
    "multilingual": EmbeddingModel(
        name="multilingual",
        model_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dimension=384,
        description="Soporta 50+ idiomas",
        size_mb=470,
        multilingual=True,
        max_seq_length=128,
    ),
    "multilingual-large": EmbeddingModel(
        name="multilingual-large",
        model_id="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        dimension=768,
        description="Alta calidad multilingüe",
        size_mb=1100,
        multilingual=True,
        max_seq_length=128,
    ),
    # Modelos especializados
    "code": EmbeddingModel(
        name="code",
        model_id="sentence-transformers/all-mpnet-base-v2",  # Funciona bien para código
        dimension=768,
        description="Optimizado para búsqueda de código",
        size_mb=420,
        max_seq_length=512,
    ),
    "qa": EmbeddingModel(
        name="qa",
        model_id="sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
        dimension=384,
        description="Optimizado para preguntas y respuestas",
        size_mb=80,
        max_seq_length=512,
    ),
    # Modelos para español
    "spanish": EmbeddingModel(
        name="spanish",
        model_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        dimension=384,
        description="Mejor opción para español",
        size_mb=470,
        multilingual=True,
        max_seq_length=128,
    ),
}


class LocalEmbeddings:
    """
    Generador de embeddings local usando sentence-transformers.

    Características:
    - 100% offline después de descargar el modelo
    - Caché de embeddings para evitar recálculos
    - Soporte para GPU (CUDA) y CPU
    - Múltiples modelos para diferentes casos de uso
    """

    def __init__(
        self,
        model_name: str = "mini",
        cache_dir: Optional[Path] = None,
        device: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Inicializa el generador de embeddings.

        Args:
            model_name: Nombre del modelo (ver EMBEDDING_MODELS)
            cache_dir: Directorio para caché de embeddings
            device: 'cuda', 'cpu', o None (auto-detect)
            use_cache: Si usar caché de embeddings
        """
        self.model_config = EMBEDDING_MODELS.get(model_name, EMBEDDING_MODELS["mini"])
        self.cache_dir = cache_dir or Path.home() / ".r-cli" / "embeddings_cache"
        self.use_cache = use_cache

        self._model = None
        self._device = device
        self._cache: dict[str, list[float]] = {}

        # Crear directorio de caché
        if use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_cache()

    def _detect_device(self) -> str:
        """Detecta el mejor dispositivo disponible."""
        if self._device:
            return self._device

        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    @property
    def model(self):
        """Lazy loading del modelo."""
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self):
        """Carga el modelo de sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer

            device = self._detect_device()
            model = SentenceTransformer(
                self.model_config.model_id,
                device=device,
            )

            # Configurar max_seq_length
            model.max_seq_length = self.model_config.max_seq_length

            return model

        except ImportError:
            raise ImportError(
                "sentence-transformers no está instalado. "
                "Ejecuta: pip install sentence-transformers"
            )

    def _get_cache_key(self, text: str) -> str:
        """Genera clave de caché para un texto."""
        content = f"{self.model_config.model_id}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_cache(self):
        """Carga caché de disco."""
        cache_file = self.cache_dir / f"cache_{self.model_config.name}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self):
        """Guarda caché a disco."""
        if not self.use_cache:
            return

        cache_file = self.cache_dir / f"cache_{self.model_config.name}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self._cache, f)
        except Exception:
            pass

    def embed(self, text: str) -> list[float]:
        """
        Genera embedding para un texto.

        Args:
            text: Texto a convertir en embedding

        Returns:
            Vector de embedding (lista de floats)
        """
        # Verificar caché
        if self.use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Generar embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()

        # Guardar en caché
        if self.use_cache:
            self._cache[cache_key] = embedding
            # Guardar periódicamente (cada 100 nuevos embeddings)
            if len(self._cache) % 100 == 0:
                self._save_cache()

        return embedding

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Genera embeddings para múltiples textos.

        Args:
            texts: Lista de textos
            batch_size: Tamaño del batch para procesamiento

        Returns:
            Lista de vectores de embedding
        """
        # Separar textos en caché y nuevos
        cached_results = {}
        texts_to_encode = []
        indices_to_encode = []

        for i, text in enumerate(texts):
            if self.use_cache:
                cache_key = self._get_cache_key(text)
                if cache_key in self._cache:
                    cached_results[i] = self._cache[cache_key]
                    continue

            texts_to_encode.append(text)
            indices_to_encode.append(i)

        # Generar embeddings para textos nuevos
        if texts_to_encode:
            new_embeddings = self.model.encode(
                texts_to_encode,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=len(texts_to_encode) > 100,
            )

            # Guardar en caché
            for idx, embedding in zip(indices_to_encode, new_embeddings):
                emb_list = embedding.tolist()
                cached_results[idx] = emb_list

                if self.use_cache:
                    cache_key = self._get_cache_key(texts[idx])
                    self._cache[cache_key] = emb_list

        # Reconstruir orden original
        results = [cached_results[i] for i in range(len(texts))]

        # Guardar caché
        if self.use_cache and texts_to_encode:
            self._save_cache()

        return results

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud coseno entre dos textos.

        Returns:
            Similitud entre 0 y 1 (1 = idénticos)
        """
        emb1 = np.array(self.embed(text1))
        emb2 = np.array(self.embed(text2))

        # Cosine similarity (los embeddings ya están normalizados)
        return float(np.dot(emb1, emb2))

    def find_similar(
        self,
        query: str,
        candidates: list[str],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Encuentra los textos más similares a una query.

        Args:
            query: Texto de búsqueda
            candidates: Lista de textos candidatos
            top_k: Número de resultados

        Returns:
            Lista de {text, similarity, index}
        """
        query_emb = np.array(self.embed(query))
        candidate_embs = np.array(self.embed_batch(candidates))

        # Calcular similitudes
        similarities = np.dot(candidate_embs, query_emb)

        # Ordenar por similitud
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(
                {
                    "text": candidates[idx],
                    "similarity": float(similarities[idx]),
                    "index": int(idx),
                }
            )

        return results

    def get_model_info(self) -> dict[str, Any]:
        """Retorna información del modelo actual."""
        return {
            "name": self.model_config.name,
            "model_id": self.model_config.model_id,
            "dimension": self.model_config.dimension,
            "description": self.model_config.description,
            "size_mb": self.model_config.size_mb,
            "multilingual": self.model_config.multilingual,
            "max_seq_length": self.model_config.max_seq_length,
            "device": self._detect_device(),
            "cache_size": len(self._cache),
        }

    def clear_cache(self):
        """Limpia la caché de embeddings."""
        self._cache = {}
        cache_file = self.cache_dir / f"cache_{self.model_config.name}.json"
        if cache_file.exists():
            cache_file.unlink()


class SemanticIndex:
    """
    Índice semántico para búsqueda eficiente.

    Almacena documentos con sus embeddings y permite búsqueda
    semántica sin necesidad de ChromaDB.
    """

    def __init__(
        self,
        embeddings: LocalEmbeddings,
        index_path: Optional[Path] = None,
    ):
        """
        Inicializa el índice semántico.

        Args:
            embeddings: Instancia de LocalEmbeddings
            index_path: Ruta para persistir el índice
        """
        self.embeddings = embeddings
        self.index_path = index_path or Path.home() / ".r-cli" / "semantic_index.json"

        self.documents: list[dict[str, Any]] = []
        self.vectors: Optional[np.ndarray] = None

        self._load_index()

    def _load_index(self):
        """Carga el índice de disco."""
        if self.index_path.exists():
            try:
                with open(self.index_path) as f:
                    data = json.load(f)

                self.documents = data.get("documents", [])

                # Reconstruir matriz de vectores
                if self.documents:
                    vectors = [doc["embedding"] for doc in self.documents]
                    self.vectors = np.array(vectors)

            except Exception:
                self.documents = []
                self.vectors = None

    def _save_index(self):
        """Guarda el índice a disco."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"documents": self.documents}

        with open(self.index_path, "w") as f:
            json.dump(data, f)

    def add(
        self,
        content: str,
        doc_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Añade un documento al índice.

        Args:
            content: Contenido del documento
            doc_id: ID opcional del documento
            metadata: Metadatos adicionales

        Returns:
            ID del documento
        """
        if doc_id is None:
            doc_id = hashlib.md5(content.encode()).hexdigest()[:12]

        # Generar embedding
        embedding = self.embeddings.embed(content)

        # Crear documento
        doc = {
            "id": doc_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }

        # Añadir al índice
        self.documents.append(doc)

        # Actualizar matriz de vectores
        if self.vectors is None:
            self.vectors = np.array([embedding])
        else:
            self.vectors = np.vstack([self.vectors, embedding])

        # Guardar
        self._save_index()

        return doc_id

    def add_batch(
        self,
        documents: list[dict[str, Any]],
    ) -> list[str]:
        """
        Añade múltiples documentos al índice.

        Args:
            documents: Lista de {content, metadata?, id?}

        Returns:
            Lista de IDs
        """
        contents = [doc["content"] for doc in documents]
        embeddings = self.embeddings.embed_batch(contents)

        ids = []
        new_docs = []
        new_vectors = []

        for doc, embedding in zip(documents, embeddings):
            doc_id = doc.get("id") or hashlib.md5(doc["content"].encode()).hexdigest()[:12]
            ids.append(doc_id)

            new_doc = {
                "id": doc_id,
                "content": doc["content"],
                "embedding": embedding,
                "metadata": doc.get("metadata", {}),
                "created_at": datetime.now().isoformat(),
            }
            new_docs.append(new_doc)
            new_vectors.append(embedding)

        # Actualizar índice
        self.documents.extend(new_docs)

        if self.vectors is None:
            self.vectors = np.array(new_vectors)
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])

        # Guardar
        self._save_index()

        return ids

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Busca documentos similares a la query.

        Args:
            query: Texto de búsqueda
            top_k: Número máximo de resultados
            threshold: Similitud mínima (0-1)

        Returns:
            Lista de documentos con similitud
        """
        if not self.documents or self.vectors is None:
            return []

        # Generar embedding de la query
        query_emb = np.array(self.embeddings.embed(query))

        # Calcular similitudes
        similarities = np.dot(self.vectors, query_emb)

        # Filtrar por threshold y ordenar
        indices = np.where(similarities >= threshold)[0]
        sorted_indices = indices[np.argsort(similarities[indices])[::-1]][:top_k]

        results = []
        for idx in sorted_indices:
            doc = self.documents[idx].copy()
            doc["similarity"] = float(similarities[idx])
            del doc["embedding"]  # No incluir embedding en resultado
            results.append(doc)

        return results

    def delete(self, doc_id: str) -> bool:
        """Elimina un documento del índice."""
        for i, doc in enumerate(self.documents):
            if doc["id"] == doc_id:
                self.documents.pop(i)
                self.vectors = np.delete(self.vectors, i, axis=0)
                self._save_index()
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        """Retorna estadísticas del índice."""
        return {
            "total_documents": len(self.documents),
            "embedding_dimension": self.embeddings.model_config.dimension,
            "model": self.embeddings.model_config.name,
            "index_size_mb": self.index_path.stat().st_size / 1024 / 1024
            if self.index_path.exists()
            else 0,
        }

    def clear(self):
        """Limpia todo el índice."""
        self.documents = []
        self.vectors = None
        if self.index_path.exists():
            self.index_path.unlink()


def list_available_models() -> str:
    """Lista los modelos de embeddings disponibles."""
    result = ["Modelos de embeddings disponibles:\n"]

    for name, model in EMBEDDING_MODELS.items():
        lang = "Multilingüe" if model.multilingual else "Inglés"
        result.append(f"  - {name}: {model.description}")
        result.append(f"      Dimensión: {model.dimension}, Tamaño: {model.size_mb}MB, {lang}")
        result.append("")

    result.append("Uso: LocalEmbeddings(model_name='mpnet')")
    result.append("Instalación: pip install sentence-transformers")

    return "\n".join(result)
