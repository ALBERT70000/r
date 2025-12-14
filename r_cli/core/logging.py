"""
Sistema de logging para R CLI.

Proporciona:
- Rotating file logs
- Console output para warnings+
- Decorador para timing de operaciones
- Tracking de tokens LLM
"""

import functools
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Optional

# Logger principal
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "r_cli") -> logging.Logger:
    """Obtiene el logger de R CLI."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return logging.getLogger(name)


def setup_logging(
    log_dir: Optional[str] = None,
    level: int = logging.DEBUG,
    max_bytes: int = 10_000_000,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configura el sistema de logging.

    Args:
        log_dir: Directorio para logs (default: ~/.r-cli/logs)
        level: Nivel de logging
        max_bytes: Tamaño máximo por archivo
        backup_count: Número de archivos de respaldo

    Returns:
        Logger configurado
    """
    logger = logging.getLogger("r_cli")
    logger.setLevel(level)

    # Evitar duplicar handlers
    if logger.handlers:
        return logger

    # Directorio de logs
    if log_dir is None:
        log_dir = os.path.expanduser("~/.r-cli/logs")
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Formato de logs
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "[%(levelname)s] %(message)s",
    )

    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_path / "r_cli.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Handler para consola (solo warnings+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def timed(func: Callable) -> Callable:
    """
    Decorador que registra el tiempo de ejecución.

    Uso:
        @timed
        def my_function():
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger()
        start = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"{func.__qualname__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__qualname__} failed after {elapsed:.3f}s: {e}")
            raise

    return wrapper


def timed_async(func: Callable) -> Callable:
    """
    Decorador que registra el tiempo de ejecución para funciones async.

    Uso:
        @timed_async
        async def my_async_function():
            ...
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = get_logger()
        start = time.perf_counter()

        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"{func.__qualname__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            logger.error(f"{func.__qualname__} failed after {elapsed:.3f}s: {e}")
            raise

    return wrapper


class TokenTracker:
    """
    Rastrea uso de tokens LLM.

    Uso:
        tracker = TokenTracker()
        tracker.record(prompt_tokens=100, completion_tokens=50)
        print(tracker.summary())
    """

    def __init__(self) -> None:
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_requests = 0
        self._logger = get_logger("r_cli.tokens")

    @property
    def total_tokens(self) -> int:
        """Total de tokens usados."""
        return self.total_prompt_tokens + self.total_completion_tokens

    def record(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "unknown",
    ) -> None:
        """Registra uso de tokens."""
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_requests += 1

        self._logger.debug(
            f"Token usage: prompt={prompt_tokens}, completion={completion_tokens}, "
            f"model={model}, total_session={self.total_tokens}"
        )

    def summary(self) -> dict[str, Any]:
        """Retorna resumen de uso."""
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset(self) -> None:
        """Reinicia contadores."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_requests = 0


# Instancia global del tracker
token_tracker = TokenTracker()


def log_skill_execution(skill_name: str, tool_name: str, success: bool, duration: float) -> None:
    """Log de ejecución de skill."""
    logger = get_logger("r_cli.skills")
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Skill execution: {skill_name}.{tool_name} | {status} | {duration:.3f}s")


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """Log de error con contexto."""
    logger = get_logger("r_cli.errors")
    msg = f"{type(error).__name__}: {error}"
    if context:
        msg = f"[{context}] {msg}"
    logger.exception(msg)
