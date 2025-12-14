"""
Herramientas compartidas para R CLI.

Estas son utilidades de bajo nivel usadas por múltiples skills.
"""

from r_cli.tools.file_utils import ensure_dir, get_file_type, safe_path
from r_cli.tools.text_processing import chunk_text, extract_sentences, word_count

__all__ = [
    "chunk_text",
    "ensure_dir",
    "extract_sentences",
    "get_file_type",
    "safe_path",
    "word_count",
]
