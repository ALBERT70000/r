"""
Jerarquía de excepciones para R CLI.

Proporciona excepciones específicas para diferentes tipos de errores,
permitiendo manejo granular y mensajes informativos.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ErrorContext:
    """Contexto adicional para errores."""

    operation: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


class RCLIError(Exception):
    """
    Excepción base para R CLI.

    Todas las excepciones de R CLI heredan de esta clase.
    """

    category: str = "general"
    is_recoverable: bool = True
    exit_code: int = 1

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.cause = cause

    def to_dict(self) -> dict[str, Any]:
        """Convierte el error a formato estructurado."""
        return {
            "error": True,
            "category": self.category,
            "message": self.message,
            "recoverable": self.is_recoverable,
            "operation": self.context.operation,
            "details": self.context.details,
            "suggestions": self.context.suggestions,
        }

    def user_message(self) -> str:
        """Mensaje amigable para el usuario."""
        msg = self.message
        if self.context.suggestions:
            msg += "\n\nSugerencias:\n"
            msg += "\n".join(f"  - {s}" for s in self.context.suggestions)
        return msg


# === Errores de Validación ===


class ValidationError(RCLIError):
    """Error de validación de entrada."""

    category = "validation"
    is_recoverable = True
    exit_code = 2


class FileNotFoundError(ValidationError):
    """Archivo no encontrado."""

    def __init__(self, path: str, **kwargs: Any):
        context = ErrorContext(
            operation="file_access",
            details={"path": path},
            suggestions=[
                f"Verifica que el archivo existe: {path}",
                "Usa una ruta absoluta",
                "Comprueba los permisos de lectura",
            ],
        )
        super().__init__(f"Archivo no encontrado: {path}", context=context, **kwargs)


class InvalidInputError(ValidationError):
    """Entrada inválida del usuario."""

    def __init__(self, field: str, value: Any, expected: str, **kwargs: Any):
        context = ErrorContext(
            operation="input_validation",
            details={"field": field, "value": value, "expected": expected},
            suggestions=[f"El valor de '{field}' debe ser: {expected}"],
        )
        super().__init__(
            f"Entrada inválida para '{field}': {value}. Esperado: {expected}",
            context=context,
            **kwargs,
        )


# === Errores de Conexión ===


class ConnectionError(RCLIError):
    """Error de conexión con servicio externo."""

    category = "connection"
    is_recoverable = True
    exit_code = 3


class LLMConnectionError(ConnectionError):
    """Error conectando con el LLM."""

    def __init__(self, backend: str, url: str, cause: Optional[Exception] = None):
        context = ErrorContext(
            operation="llm_connection",
            details={"backend": backend, "url": url},
            suggestions=[
                f"Verifica que {backend} está corriendo",
                f"Comprueba la URL: {url}",
                "Ejecuta 'r status' para ver backends disponibles",
            ],
        )
        super().__init__(
            f"No se pudo conectar con {backend} en {url}",
            context=context,
            cause=cause,
        )


class TimeoutError(ConnectionError):
    """Timeout esperando respuesta."""

    def __init__(self, operation: str, timeout_seconds: float, **kwargs: Any):
        context = ErrorContext(
            operation=operation,
            details={"timeout_seconds": timeout_seconds},
            suggestions=[
                "Intenta con una consulta más simple",
                "Verifica que el servidor no esté sobrecargado",
                "Aumenta el timeout en la configuración",
            ],
        )
        super().__init__(
            f"Timeout después de {timeout_seconds}s en {operation}",
            context=context,
            **kwargs,
        )


# === Errores de Dependencias ===


class DependencyError(RCLIError):
    """Error de dependencia faltante."""

    category = "dependency"
    is_recoverable = False
    exit_code = 4


class MissingDependencyError(DependencyError):
    """Dependencia Python no instalada."""

    def __init__(self, package: str, feature: str, install_cmd: Optional[str] = None):
        install = install_cmd or f"pip install {package}"
        context = ErrorContext(
            operation="import_dependency",
            details={"package": package, "feature": feature},
            suggestions=[
                f"Instala la dependencia: {install}",
                "Para todas las features: pip install r-cli-ai[all]",
            ],
        )
        super().__init__(
            f"Dependencia '{package}' requerida para {feature} no está instalada",
            context=context,
        )


class ModelNotFoundError(DependencyError):
    """Modelo LLM no encontrado."""

    def __init__(self, model: str, backend: str):
        context = ErrorContext(
            operation="load_model",
            details={"model": model, "backend": backend},
            suggestions=[
                f"Descarga el modelo: ollama pull {model}" if backend == "ollama" else "",
                "Lista modelos disponibles: r models",
            ],
        )
        super().__init__(f"Modelo '{model}' no encontrado en {backend}", context=context)


# === Errores de Ejecución ===


class ExecutionError(RCLIError):
    """Error durante la ejecución de una operación."""

    category = "execution"
    is_recoverable = True
    exit_code = 5


class SkillExecutionError(ExecutionError):
    """Error ejecutando un skill."""

    def __init__(self, skill: str, tool: str, cause: Optional[Exception] = None):
        context = ErrorContext(
            operation="skill_execution",
            details={"skill": skill, "tool": tool},
            suggestions=[
                "Verifica los parámetros de entrada",
                "Consulta la documentación del skill",
            ],
        )
        super().__init__(
            f"Error ejecutando {skill}.{tool}",
            context=context,
            cause=cause,
        )


class ToolExecutionError(ExecutionError):
    """Error ejecutando una tool."""

    def __init__(self, tool_name: str, args: dict[str, Any], cause: Optional[Exception] = None):
        context = ErrorContext(
            operation="tool_execution",
            details={"tool": tool_name, "arguments": args},
        )
        super().__init__(
            f"Error ejecutando tool '{tool_name}'",
            context=context,
            cause=cause,
        )


# === Errores de Configuración ===


class ConfigurationError(RCLIError):
    """Error de configuración."""

    category = "configuration"
    is_recoverable = True
    exit_code = 6


class InvalidConfigError(ConfigurationError):
    """Configuración inválida."""

    def __init__(self, key: str, value: Any, reason: str):
        context = ErrorContext(
            operation="config_validation",
            details={"key": key, "value": value, "reason": reason},
            suggestions=[
                "Revisa ~/.r-cli/config.yaml",
                "Ejecuta 'r config' para ver configuración actual",
            ],
        )
        super().__init__(f"Configuración inválida '{key}': {reason}", context=context)


# === Errores de Sistema ===


class SystemError(RCLIError):
    """Error del sistema."""

    category = "system"
    is_recoverable = False
    exit_code = 7


class PermissionError(SystemError):
    """Error de permisos."""

    def __init__(self, path: str, operation: str):
        context = ErrorContext(
            operation=operation,
            details={"path": path},
            suggestions=[
                f"Verifica permisos del archivo/directorio: {path}",
                "Ejecuta con permisos adecuados",
            ],
        )
        super().__init__(f"Permiso denegado para {operation}: {path}", context=context)


# === Errores de Rate Limiting ===


class RateLimitError(RCLIError):
    """Rate limit alcanzado."""

    category = "rate_limit"
    is_recoverable = True
    exit_code = 8

    def __init__(self, service: str, retry_after: Optional[float] = None):
        context = ErrorContext(
            operation="api_request",
            details={"service": service, "retry_after": retry_after},
            suggestions=[
                "Espera unos segundos antes de reintentar",
                "Reduce la frecuencia de requests",
            ],
        )
        msg = f"Rate limit alcanzado para {service}"
        if retry_after:
            msg += f". Reintentar en {retry_after}s"
        super().__init__(msg, context=context)


# === Utilidades ===


def format_error_for_llm(error: RCLIError) -> str:
    """Formatea un error para que el LLM lo entienda."""
    return (
        f"[ERROR: {error.category}] {error.message}\n"
        f"Operación: {error.context.operation}\n"
        f"Recuperable: {'Sí' if error.is_recoverable else 'No'}"
    )


def is_retriable(error: Exception) -> bool:
    """Determina si un error puede reintentarse."""
    if isinstance(error, RCLIError):
        return error.is_recoverable and error.category in ("connection", "rate_limit")

    # Errores de conexión estándar
    retriable_types = (
        ConnectionResetError,
        ConnectionRefusedError,
        BrokenPipeError,
    )
    return isinstance(error, retriable_types)
