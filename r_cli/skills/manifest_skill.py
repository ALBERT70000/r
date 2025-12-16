"""
Manifest Skill for R CLI.

Web App Manifest utilities:
- Generate manifest.json
- Validate manifests
- Icon generation metadata
"""

import json
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class ManifestSkill(Skill):
    """Skill for Web App Manifest operations."""

    name = "manifest"
    description = "Manifest: generate and validate web app manifests"

    ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

    DISPLAY_MODES = ["fullscreen", "standalone", "minimal-ui", "browser"]
    ORIENTATIONS = [
        "any",
        "natural",
        "landscape",
        "portrait",
        "portrait-primary",
        "portrait-secondary",
        "landscape-primary",
        "landscape-secondary",
    ]

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="manifest_generate",
                description="Generate a web app manifest",
                parameters={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "App name",
                        },
                        "short_name": {
                            "type": "string",
                            "description": "Short name for home screen",
                        },
                        "description": {
                            "type": "string",
                            "description": "App description",
                        },
                        "start_url": {
                            "type": "string",
                            "description": "Start URL (default: /)",
                        },
                        "display": {
                            "type": "string",
                            "description": "Display mode: standalone, fullscreen, minimal-ui, browser",
                        },
                        "theme_color": {
                            "type": "string",
                            "description": "Theme color (hex)",
                        },
                        "background_color": {
                            "type": "string",
                            "description": "Background color (hex)",
                        },
                        "icons_path": {
                            "type": "string",
                            "description": "Path prefix for icons",
                        },
                    },
                    "required": ["name"],
                },
                handler=self.manifest_generate,
            ),
            Tool(
                name="manifest_validate",
                description="Validate a web app manifest",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Manifest JSON content",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.manifest_validate,
            ),
            Tool(
                name="manifest_icons",
                description="Generate icon entries for manifest",
                parameters={
                    "type": "object",
                    "properties": {
                        "base_path": {
                            "type": "string",
                            "description": "Base path for icons",
                        },
                        "sizes": {
                            "type": "array",
                            "description": "Icon sizes to generate",
                        },
                        "format": {
                            "type": "string",
                            "description": "Image format (png, webp)",
                        },
                    },
                    "required": ["base_path"],
                },
                handler=self.manifest_icons,
            ),
            Tool(
                name="manifest_shortcuts",
                description="Generate shortcuts for manifest",
                parameters={
                    "type": "object",
                    "properties": {
                        "shortcuts": {
                            "type": "array",
                            "description": "List of shortcuts (name, url, description)",
                        },
                    },
                    "required": ["shortcuts"],
                },
                handler=self.manifest_shortcuts,
            ),
            Tool(
                name="manifest_html_tags",
                description="Generate HTML meta tags for PWA",
                parameters={
                    "type": "object",
                    "properties": {
                        "manifest_path": {
                            "type": "string",
                            "description": "Path to manifest.json",
                        },
                        "theme_color": {
                            "type": "string",
                            "description": "Theme color",
                        },
                        "apple_icon": {
                            "type": "string",
                            "description": "Apple touch icon path",
                        },
                    },
                    "required": ["manifest_path"],
                },
                handler=self.manifest_html_tags,
            ),
        ]

    def manifest_generate(
        self,
        name: str,
        short_name: Optional[str] = None,
        description: Optional[str] = None,
        start_url: str = "/",
        display: str = "standalone",
        theme_color: str = "#ffffff",
        background_color: str = "#ffffff",
        icons_path: str = "/icons",
    ) -> str:
        """Generate manifest.json."""
        manifest = {
            "name": name,
            "short_name": short_name or name[:12],
            "start_url": start_url,
            "display": display,
            "theme_color": theme_color,
            "background_color": background_color,
            "icons": [],
        }

        if description:
            manifest["description"] = description

        # Generate icon entries
        for size in self.ICON_SIZES:
            manifest["icons"].append(
                {
                    "src": f"{icons_path}/icon-{size}x{size}.png",
                    "sizes": f"{size}x{size}",
                    "type": "image/png",
                }
            )

        # Add maskable icon
        manifest["icons"].append(
            {
                "src": f"{icons_path}/icon-512x512-maskable.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            }
        )

        return json.dumps(manifest, indent=2)

    def manifest_validate(self, content: str) -> str:
        """Validate manifest."""
        try:
            manifest = json.loads(content)
        except json.JSONDecodeError as e:
            return json.dumps(
                {
                    "valid": False,
                    "errors": [f"JSON parse error: {e}"],
                },
                indent=2,
            )

        errors = []
        warnings = []

        # Required fields
        if "name" not in manifest:
            errors.append("Missing required field: name")

        # Recommended fields
        recommended = [
            "short_name",
            "start_url",
            "display",
            "icons",
            "theme_color",
            "background_color",
        ]
        for field in recommended:
            if field not in manifest:
                warnings.append(f"Missing recommended field: {field}")

        # Validate display
        if "display" in manifest and manifest["display"] not in self.DISPLAY_MODES:
            errors.append(f"Invalid display mode: {manifest['display']}")

        # Validate orientation
        if "orientation" in manifest and manifest["orientation"] not in self.ORIENTATIONS:
            errors.append(f"Invalid orientation: {manifest['orientation']}")

        # Validate icons
        if "icons" in manifest:
            has_192 = False
            has_512 = False
            has_maskable = False

            for icon in manifest["icons"]:
                if "src" not in icon:
                    errors.append("Icon missing src")
                if "sizes" not in icon:
                    warnings.append(f"Icon missing sizes: {icon.get('src', 'unknown')}")
                else:
                    if "192x192" in icon["sizes"]:
                        has_192 = True
                    if "512x512" in icon["sizes"]:
                        has_512 = True

                if icon.get("purpose") == "maskable":
                    has_maskable = True

            if not has_192:
                warnings.append("Missing 192x192 icon (required for Add to Home Screen)")
            if not has_512:
                warnings.append("Missing 512x512 icon (required for Splash Screen)")
            if not has_maskable:
                warnings.append("No maskable icon (recommended for adaptive icons)")

        # Validate colors
        for color_field in ["theme_color", "background_color"]:
            if color_field in manifest:
                color = manifest[color_field]
                if not color.startswith("#") and not color.startswith("rgb"):
                    warnings.append(f"{color_field} should be a valid color")

        # Validate short_name length
        if "short_name" in manifest and len(manifest["short_name"]) > 12:
            warnings.append("short_name should be 12 characters or less")

        return json.dumps(
            {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "has_icons": "icons" in manifest,
                "icon_count": len(manifest.get("icons", [])),
            },
            indent=2,
        )

    def manifest_icons(
        self,
        base_path: str,
        sizes: Optional[list] = None,
        format: str = "png",
    ) -> str:
        """Generate icon entries."""
        sizes = sizes or self.ICON_SIZES

        icons = []
        for size in sizes:
            icons.append(
                {
                    "src": f"{base_path}/icon-{size}x{size}.{format}",
                    "sizes": f"{size}x{size}",
                    "type": f"image/{format}",
                }
            )

        # Add maskable
        icons.append(
            {
                "src": f"{base_path}/icon-512x512-maskable.{format}",
                "sizes": "512x512",
                "type": f"image/{format}",
                "purpose": "maskable",
            }
        )

        return json.dumps(
            {
                "icons": icons,
                "sizes_needed": sizes + ["512x512 (maskable)"],
            },
            indent=2,
        )

    def manifest_shortcuts(self, shortcuts: list) -> str:
        """Generate shortcuts array."""
        result = []

        for shortcut in shortcuts:
            if isinstance(shortcut, str):
                shortcut = {"name": shortcut, "url": f"/{shortcut.lower()}"}

            entry = {
                "name": shortcut.get("name", "Shortcut"),
                "url": shortcut.get("url", "/"),
            }

            if "description" in shortcut:
                entry["description"] = shortcut["description"]
            if "icon" in shortcut:
                entry["icons"] = [{"src": shortcut["icon"], "sizes": "96x96"}]

            result.append(entry)

        return json.dumps({"shortcuts": result}, indent=2)

    def manifest_html_tags(
        self,
        manifest_path: str,
        theme_color: str = "#ffffff",
        apple_icon: Optional[str] = None,
    ) -> str:
        """Generate HTML meta tags."""
        tags = [
            f'<link rel="manifest" href="{manifest_path}">',
            f'<meta name="theme-color" content="{theme_color}">',
            '<meta name="mobile-web-app-capable" content="yes">',
            '<meta name="apple-mobile-web-app-capable" content="yes">',
            '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
        ]

        if apple_icon:
            tags.append(f'<link rel="apple-touch-icon" href="{apple_icon}">')

        return "\n".join(tags)

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        if "name" in kwargs:
            return self.manifest_generate(kwargs["name"])
        return "Provide app name to generate manifest"
