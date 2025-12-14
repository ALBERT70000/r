"""
Skill de Plugins para R CLI.

Permite gestionar plugins: crear, instalar, habilitar, deshabilitar y eliminar.
"""

from pathlib import Path

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool
from r_cli.core.plugins import PluginManager


class PluginSkill(Skill):
    """Skill para gestión de plugins."""

    name = "plugin"
    description = "Gestiona plugins de la comunidad para R CLI"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plugins_dir = None
        if hasattr(self.config, "home_dir"):
            plugins_dir = Path(self.config.home_dir) / "plugins"
        self.manager = PluginManager(plugins_dir)

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="plugin_create",
                description="Crea un nuevo plugin desde template",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del plugin (solo letras, números, guiones bajos)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Descripción del plugin",
                        },
                        "author": {
                            "type": "string",
                            "description": "Nombre del autor",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.create_plugin,
            ),
            Tool(
                name="plugin_install",
                description="Instala un plugin desde directorio local o GitHub",
                parameters={
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Ruta local o URL de GitHub del plugin",
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Forzar reinstalación si ya existe",
                        },
                    },
                    "required": ["source"],
                },
                handler=self.install_plugin,
            ),
            Tool(
                name="plugin_uninstall",
                description="Desinstala un plugin",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del plugin a desinstalar",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.uninstall_plugin,
            ),
            Tool(
                name="plugin_enable",
                description="Habilita un plugin instalado",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del plugin",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.enable_plugin,
            ),
            Tool(
                name="plugin_disable",
                description="Deshabilita un plugin",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del plugin",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.disable_plugin,
            ),
            Tool(
                name="plugin_list",
                description="Lista todos los plugins instalados",
                parameters={"type": "object", "properties": {}},
                handler=self.list_plugins,
            ),
            Tool(
                name="plugin_info",
                description="Muestra información detallada de un plugin",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Nombre del plugin",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.plugin_info,
            ),
            Tool(
                name="plugin_validate",
                description="Valida la estructura de un plugin",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Ruta al directorio del plugin",
                        },
                    },
                    "required": ["path"],
                },
                handler=self.validate_plugin,
            ),
        ]

    def create_plugin(
        self,
        name: str,
        description: str = "Mi plugin personalizado",
        author: str = "",
    ) -> str:
        """Crea un nuevo plugin."""
        return self.manager.create_plugin(name, description, author)

    def install_plugin(
        self,
        source: str,
        force: bool = False,
    ) -> str:
        """Instala un plugin."""
        return self.manager.install_plugin(source, force)

    def uninstall_plugin(self, name: str) -> str:
        """Desinstala un plugin."""
        return self.manager.uninstall_plugin(name)

    def enable_plugin(self, name: str) -> str:
        """Habilita un plugin."""
        return self.manager.enable_plugin(name)

    def disable_plugin(self, name: str) -> str:
        """Deshabilita un plugin."""
        return self.manager.disable_plugin(name)

    def list_plugins(self) -> str:
        """Lista plugins instalados."""
        return self.manager.list_plugins()

    def plugin_info(self, name: str) -> str:
        """Información de un plugin."""
        return self.manager.get_plugin_info(name)

    def validate_plugin(self, path: str) -> str:
        """Valida un plugin."""
        plugin_path = Path(path).expanduser()
        if not plugin_path.is_dir():
            return f"Error: '{path}' no es un directorio válido"

        valid, message = self.manager.validate_plugin(plugin_path)
        return message

    def execute(self, **kwargs) -> str:
        """Ejecución directa del skill."""
        action = kwargs.get("action", "list")

        if action == "list":
            return self.list_plugins()
        elif action == "create":
            name = kwargs.get("name")
            if not name:
                return "Error: Se requiere --name para crear un plugin"
            return self.create_plugin(
                name=name,
                description=kwargs.get("description", "Mi plugin"),
                author=kwargs.get("author", ""),
            )
        elif action == "install":
            source = kwargs.get("source")
            if not source:
                return "Error: Se requiere --source para instalar"
            return self.install_plugin(source, kwargs.get("force", False))
        elif action == "uninstall" or action == "remove":
            name = kwargs.get("name")
            if not name:
                return "Error: Se requiere --name para desinstalar"
            return self.uninstall_plugin(name)
        elif action == "enable":
            name = kwargs.get("name")
            if not name:
                return "Error: Se requiere --name"
            return self.enable_plugin(name)
        elif action == "disable":
            name = kwargs.get("name")
            if not name:
                return "Error: Se requiere --name"
            return self.disable_plugin(name)
        elif action == "info":
            name = kwargs.get("name")
            if not name:
                return "Error: Se requiere --name"
            return self.plugin_info(name)
        elif action == "validate":
            path = kwargs.get("path")
            if not path:
                return "Error: Se requiere --path"
            return self.validate_plugin(path)
        else:
            return self.list_plugins()
