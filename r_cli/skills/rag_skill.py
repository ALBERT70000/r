"""
Skill de RAG Mejorado para R CLI.

Búsqueda semántica usando embeddings locales con sentence-transformers.
100% offline después de descargar el modelo.
"""

from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class RAGSkill(Skill):
    """Skill para RAG con embeddings locales."""

    name = "rag"
    description = "Base de conocimiento con búsqueda semántica usando embeddings locales"

    # Modelos disponibles
    MODELS = {
        "mini": "Rápido y ligero (80MB, ideal para CPU)",
        "minilm": "Balance velocidad/calidad (120MB)",
        "mpnet": "Alta calidad (420MB)",
        "multilingual": "Soporta 50+ idiomas (470MB)",
        "spanish": "Optimizado para español (470MB)",
        "qa": "Optimizado para Q&A (80MB)",
        "code": "Para búsqueda de código (420MB)",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._embeddings = None
        self._index = None
        self._model_name = "mini"  # Default

    def _get_embeddings(self):
        """Lazy loading de embeddings."""
        if self._embeddings is None:
            try:
                from r_cli.core.embeddings import LocalEmbeddings

                cache_dir = None
                if hasattr(self.config, "home_dir"):
                    cache_dir = Path(self.config.home_dir) / "embeddings_cache"

                self._embeddings = LocalEmbeddings(
                    model_name=self._model_name,
                    cache_dir=cache_dir,
                    use_cache=True,
                )
            except ImportError:
                return None
        return self._embeddings

    def _get_index(self):
        """Lazy loading del índice semántico."""
        if self._index is None:
            embeddings = self._get_embeddings()
            if embeddings is None:
                return None

            try:
                from r_cli.core.embeddings import SemanticIndex

                index_path = None
                if hasattr(self.config, "home_dir"):
                    index_path = Path(self.config.home_dir) / "semantic_index.json"

                self._index = SemanticIndex(
                    embeddings=embeddings,
                    index_path=index_path,
                )
            except Exception:
                return None

        return self._index

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="rag_add",
                description="Añade un documento a la base de conocimiento",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Contenido del documento",
                        },
                        "doc_id": {
                            "type": "string",
                            "description": "ID opcional del documento",
                        },
                        "source": {
                            "type": "string",
                            "description": "Fuente/origen del documento",
                        },
                        "tags": {
                            "type": "string",
                            "description": "Tags separados por comas",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.add_document,
            ),
            Tool(
                name="rag_add_file",
                description="Añade un archivo a la base de conocimiento",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Ruta al archivo",
                        },
                        "chunk_size": {
                            "type": "integer",
                            "description": "Tamaño de chunks (default: 1000)",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.add_file,
            ),
            Tool(
                name="rag_search",
                description="Busca documentos similares usando búsqueda semántica",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto de búsqueda",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Número de resultados (default: 5)",
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Similitud mínima 0-1 (default: 0.3)",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.search,
            ),
            Tool(
                name="rag_similarity",
                description="Calcula similitud semántica entre dos textos",
                parameters={
                    "type": "object",
                    "properties": {
                        "text1": {"type": "string", "description": "Primer texto"},
                        "text2": {"type": "string", "description": "Segundo texto"},
                    },
                    "required": ["text1", "text2"],
                },
                handler=self.similarity,
            ),
            Tool(
                name="rag_list_models",
                description="Lista los modelos de embeddings disponibles",
                parameters={"type": "object", "properties": {}},
                handler=self.list_models,
            ),
            Tool(
                name="rag_set_model",
                description="Cambia el modelo de embeddings",
                parameters={
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "enum": list(self.MODELS.keys()),
                            "description": "Nombre del modelo",
                        },
                    },
                    "required": ["model"],
                },
                handler=self.set_model,
            ),
            Tool(
                name="rag_stats",
                description="Muestra estadísticas del índice",
                parameters={"type": "object", "properties": {}},
                handler=self.get_stats,
            ),
            Tool(
                name="rag_delete",
                description="Elimina un documento del índice",
                parameters={
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "string",
                            "description": "ID del documento a eliminar",
                        },
                    },
                    "required": ["doc_id"],
                },
                handler=self.delete_document,
            ),
            Tool(
                name="rag_clear",
                description="Limpia todo el índice (cuidado!)",
                parameters={"type": "object", "properties": {}},
                handler=self.clear_index,
            ),
        ]

    def add_document(
        self,
        content: str,
        doc_id: Optional[str] = None,
        source: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> str:
        """Añade un documento al índice."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado. Ejecuta: pip install sentence-transformers"

        try:
            metadata = {}
            if source:
                metadata["source"] = source
            if tags:
                metadata["tags"] = [t.strip() for t in tags.split(",")]

            doc_id = index.add(
                content=content,
                doc_id=doc_id,
                metadata=metadata,
            )

            return f"Documento añadido con ID: {doc_id}\nContenido: {content[:100]}..."

        except Exception as e:
            return f"Error añadiendo documento: {e}"

    def add_file(
        self,
        file_path: str,
        chunk_size: int = 1000,
    ) -> str:
        """Añade un archivo al índice, dividiéndolo en chunks."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado. Ejecuta: pip install sentence-transformers"

        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: Archivo no encontrado: {file_path}"

        try:
            # Leer archivo
            content = path.read_text(encoding="utf-8", errors="ignore")

            # Dividir en chunks
            chunks = self._chunk_text(content, chunk_size)

            # Añadir chunks
            documents = []
            for i, chunk in enumerate(chunks):
                documents.append(
                    {
                        "content": chunk,
                        "id": f"{path.stem}_{i}",
                        "metadata": {
                            "source": str(path),
                            "chunk": i,
                            "total_chunks": len(chunks),
                        },
                    }
                )

            ids = index.add_batch(documents)

            return f"Archivo añadido: {path.name}\n{len(chunks)} chunks indexados."

        except Exception as e:
            return f"Error procesando archivo: {e}"

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """Divide texto en chunks."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        overlap = chunk_size // 5  # 20% overlap

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Cortar en punto o espacio
            if end < len(text):
                for sep in [". ", "\n\n", "\n", " "]:
                    last_sep = chunk.rfind(sep)
                    if last_sep > chunk_size // 2:
                        chunk = chunk[: last_sep + len(sep)]
                        end = start + last_sep + len(sep)
                        break

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3,
    ) -> str:
        """Busca documentos similares."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado. Ejecuta: pip install sentence-transformers"

        try:
            results = index.search(
                query=query,
                top_k=top_k,
                threshold=threshold,
            )

            if not results:
                return f"No se encontraron documentos similares a: '{query}'"

            output = [f"Resultados para: '{query}'\n"]

            for i, doc in enumerate(results, 1):
                similarity = doc["similarity"]
                content = doc["content"]
                if len(content) > 300:
                    content = content[:300] + "..."

                output.append(f"{i}. [Similitud: {similarity:.2%}]")
                output.append(f"   ID: {doc['id']}")

                if doc.get("metadata", {}).get("source"):
                    output.append(f"   Fuente: {doc['metadata']['source']}")

                output.append(f"   {content}")
                output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"Error en búsqueda: {e}"

    def similarity(self, text1: str, text2: str) -> str:
        """Calcula similitud entre dos textos."""
        embeddings = self._get_embeddings()
        if embeddings is None:
            return "Error: sentence-transformers no instalado."

        try:
            sim = embeddings.similarity(text1, text2)

            interpretation = ""
            if sim >= 0.8:
                interpretation = "Muy similares"
            elif sim >= 0.6:
                interpretation = "Similares"
            elif sim >= 0.4:
                interpretation = "Moderadamente similares"
            elif sim >= 0.2:
                interpretation = "Poco similares"
            else:
                interpretation = "No relacionados"

            return f"""Similitud semántica: {sim:.2%} ({interpretation})

Texto 1: {text1[:100]}{"..." if len(text1) > 100 else ""}
Texto 2: {text2[:100]}{"..." if len(text2) > 100 else ""}"""

        except Exception as e:
            return f"Error calculando similitud: {e}"

    def list_models(self) -> str:
        """Lista modelos disponibles."""
        try:
            from r_cli.core.embeddings import list_available_models

            return list_available_models()
        except ImportError:
            result = ["Modelos de embeddings disponibles:\n"]
            for name, desc in self.MODELS.items():
                result.append(f"  - {name}: {desc}")
            result.append("\nInstalación: pip install sentence-transformers")
            return "\n".join(result)

    def set_model(self, model: str) -> str:
        """Cambia el modelo de embeddings."""
        if model not in self.MODELS:
            return f"Error: Modelo '{model}' no válido. Usa: {', '.join(self.MODELS.keys())}"

        self._model_name = model
        self._embeddings = None  # Forzar recarga
        self._index = None

        return f"Modelo cambiado a: {model}\n{self.MODELS[model]}"

    def get_stats(self) -> str:
        """Estadísticas del índice."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado."

        try:
            stats = index.get_stats()
            embeddings = self._get_embeddings()
            model_info = embeddings.get_model_info() if embeddings else {}

            result = [
                "Estadísticas del RAG:\n",
                f"  Documentos indexados: {stats['total_documents']}",
                f"  Dimensión embeddings: {stats['embedding_dimension']}",
                f"  Modelo: {stats['model']}",
                f"  Tamaño del índice: {stats['index_size_mb']:.2f} MB",
            ]

            if model_info:
                result.append(f"  Dispositivo: {model_info.get('device', 'N/A')}")
                result.append(f"  Cache de embeddings: {model_info.get('cache_size', 0)} entradas")

            return "\n".join(result)

        except Exception as e:
            return f"Error obteniendo estadísticas: {e}"

    def delete_document(self, doc_id: str) -> str:
        """Elimina un documento."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado."

        if index.delete(doc_id):
            return f"Documento '{doc_id}' eliminado."
        else:
            return f"Documento '{doc_id}' no encontrado."

    def clear_index(self) -> str:
        """Limpia todo el índice."""
        index = self._get_index()
        if index is None:
            return "Error: sentence-transformers no instalado."

        index.clear()
        return "Índice limpiado completamente."

    def execute(self, **kwargs) -> str:
        """Ejecución directa del skill."""
        action = kwargs.get("action", "stats")
        query = kwargs.get("query")
        content = kwargs.get("content")
        file_path = kwargs.get("file")

        if query:
            return self.search(query, kwargs.get("top_k", 5))
        elif content:
            return self.add_document(content, kwargs.get("id"), kwargs.get("source"))
        elif file_path:
            return self.add_file(file_path, kwargs.get("chunk_size", 1000))
        elif action == "models":
            return self.list_models()
        elif action == "clear":
            return self.clear_index()
        else:
            return self.get_stats()
