"""
Schema Skill for R CLI.

JSON Schema utilities:
- Validate JSON against schema
- Generate schema from JSON
- Schema documentation
"""

import json
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class SchemaSkill(Skill):
    """Skill for JSON Schema operations."""

    name = "schema"
    description = "Schema: validate JSON, generate schemas"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="schema_validate",
                description="Validate JSON data against a schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "JSON data to validate",
                        },
                        "schema": {
                            "type": "string",
                            "description": "JSON Schema",
                        },
                    },
                    "required": ["data", "schema"],
                },
                handler=self.schema_validate,
            ),
            Tool(
                name="schema_generate",
                description="Generate JSON Schema from sample data",
                parameters={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Sample JSON data",
                        },
                        "title": {
                            "type": "string",
                            "description": "Schema title",
                        },
                    },
                    "required": ["data"],
                },
                handler=self.schema_generate,
            ),
            Tool(
                name="schema_document",
                description="Generate documentation from schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "JSON Schema",
                        },
                    },
                    "required": ["schema"],
                },
                handler=self.schema_document,
            ),
            Tool(
                name="schema_example",
                description="Generate example data from schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "schema": {
                            "type": "string",
                            "description": "JSON Schema",
                        },
                    },
                    "required": ["schema"],
                },
                handler=self.schema_example,
            ),
        ]

    def schema_validate(self, data: str, schema: str) -> str:
        """Validate JSON against schema."""
        try:
            data_obj = json.loads(data)
            schema_obj = json.loads(schema)
        except json.JSONDecodeError as e:
            return f"JSON parse error: {e}"

        # Try jsonschema library
        try:
            import jsonschema

            try:
                jsonschema.validate(data_obj, schema_obj)
                return json.dumps(
                    {
                        "valid": True,
                        "message": "Data is valid according to schema",
                    },
                    indent=2,
                )
            except jsonschema.ValidationError as e:
                return json.dumps(
                    {
                        "valid": False,
                        "error": e.message,
                        "path": list(e.path),
                        "schema_path": list(e.schema_path),
                    },
                    indent=2,
                )
            except jsonschema.SchemaError as e:
                return json.dumps(
                    {
                        "valid": False,
                        "error": f"Invalid schema: {e.message}",
                    },
                    indent=2,
                )

        except ImportError:
            # Fallback: basic validation
            return self._basic_validate(data_obj, schema_obj)

    def _basic_validate(self, data, schema, path="") -> str:
        """Basic schema validation without jsonschema library."""
        errors = []

        def validate(data, schema, path):
            schema_type = schema.get("type")

            if schema_type == "object":
                if not isinstance(data, dict):
                    errors.append(f"{path}: expected object, got {type(data).__name__}")
                    return

                # Check required
                for req in schema.get("required", []):
                    if req not in data:
                        errors.append(f"{path}: missing required property '{req}'")

                # Check properties
                props = schema.get("properties", {})
                for key, value in data.items():
                    if key in props:
                        validate(value, props[key], f"{path}.{key}")

            elif schema_type == "array":
                if not isinstance(data, list):
                    errors.append(f"{path}: expected array, got {type(data).__name__}")
                    return

                items = schema.get("items", {})
                for i, item in enumerate(data):
                    validate(item, items, f"{path}[{i}]")

            elif schema_type == "string":
                if not isinstance(data, str):
                    errors.append(f"{path}: expected string, got {type(data).__name__}")

            elif schema_type == "number":
                if not isinstance(data, (int, float)):
                    errors.append(f"{path}: expected number, got {type(data).__name__}")

            elif schema_type == "integer":
                if not isinstance(data, int):
                    errors.append(f"{path}: expected integer, got {type(data).__name__}")

            elif schema_type == "boolean":
                if not isinstance(data, bool):
                    errors.append(f"{path}: expected boolean, got {type(data).__name__}")

        validate(data, schema, "$")

        if errors:
            return json.dumps(
                {
                    "valid": False,
                    "errors": errors,
                    "note": "Install jsonschema for full validation: pip install jsonschema",
                },
                indent=2,
            )

        return json.dumps(
            {
                "valid": True,
                "note": "Basic validation passed. Install jsonschema for full validation.",
            },
            indent=2,
        )

    def schema_generate(self, data: str, title: Optional[str] = None) -> str:
        """Generate schema from sample data."""
        try:
            data_obj = json.loads(data)
        except json.JSONDecodeError as e:
            return f"JSON parse error: {e}"

        def infer_schema(obj):
            if obj is None:
                return {"type": "null"}
            elif isinstance(obj, bool):
                return {"type": "boolean"}
            elif isinstance(obj, int):
                return {"type": "integer"}
            elif isinstance(obj, float):
                return {"type": "number"}
            elif isinstance(obj, str):
                return {"type": "string"}
            elif isinstance(obj, list):
                if not obj:
                    return {"type": "array", "items": {}}
                # Infer from first item
                return {
                    "type": "array",
                    "items": infer_schema(obj[0]),
                }
            elif isinstance(obj, dict):
                properties = {}
                required = []
                for key, value in obj.items():
                    properties[key] = infer_schema(value)
                    required.append(key)
                return {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            else:
                return {}

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
        }

        if title:
            schema["title"] = title

        schema.update(infer_schema(data_obj))

        return json.dumps(schema, indent=2)

    def schema_document(self, schema: str) -> str:
        """Generate documentation from schema."""
        try:
            schema_obj = json.loads(schema)
        except json.JSONDecodeError as e:
            return f"JSON parse error: {e}"

        lines = []

        def document(obj, indent=0, name="root"):
            prefix = "  " * indent

            title = obj.get("title", name)
            desc = obj.get("description", "")
            obj_type = obj.get("type", "any")

            lines.append(f"{prefix}**{title}** ({obj_type})")
            if desc:
                lines.append(f"{prefix}  {desc}")

            if obj_type == "object":
                props = obj.get("properties", {})
                required = obj.get("required", [])

                for prop_name, prop_schema in props.items():
                    req_marker = "*" if prop_name in required else ""
                    lines.append(f"{prefix}  - {prop_name}{req_marker}:")
                    document(prop_schema, indent + 2, prop_name)

            elif obj_type == "array":
                items = obj.get("items", {})
                lines.append(f"{prefix}  Items:")
                document(items, indent + 2, "item")

            # Constraints
            constraints = []
            if "minimum" in obj:
                constraints.append(f"min: {obj['minimum']}")
            if "maximum" in obj:
                constraints.append(f"max: {obj['maximum']}")
            if "minLength" in obj:
                constraints.append(f"minLength: {obj['minLength']}")
            if "maxLength" in obj:
                constraints.append(f"maxLength: {obj['maxLength']}")
            if "pattern" in obj:
                constraints.append(f"pattern: {obj['pattern']}")
            if "enum" in obj:
                constraints.append(f"enum: {obj['enum']}")

            if constraints:
                lines.append(f"{prefix}  Constraints: {', '.join(constraints)}")

        document(schema_obj)

        return "\n".join(lines)

    def schema_example(self, schema: str) -> str:
        """Generate example from schema."""
        try:
            schema_obj = json.loads(schema)
        except json.JSONDecodeError as e:
            return f"JSON parse error: {e}"

        def generate(obj):
            obj_type = obj.get("type", "any")

            if "default" in obj:
                return obj["default"]
            if "example" in obj:
                return obj["example"]
            if "enum" in obj:
                return obj["enum"][0]

            if obj_type == "object":
                result = {}
                for prop_name, prop_schema in obj.get("properties", {}).items():
                    result[prop_name] = generate(prop_schema)
                return result
            elif obj_type == "array":
                items = obj.get("items", {})
                return [generate(items)]
            elif obj_type == "string":
                if "format" in obj:
                    formats = {
                        "email": "user@example.com",
                        "uri": "https://example.com",
                        "date": "2024-01-01",
                        "date-time": "2024-01-01T00:00:00Z",
                        "uuid": "550e8400-e29b-41d4-a716-446655440000",
                    }
                    return formats.get(obj["format"], "string")
                return "string"
            elif obj_type == "integer":
                return obj.get("minimum", 0)
            elif obj_type == "number":
                return obj.get("minimum", 0.0)
            elif obj_type == "boolean":
                return True
            elif obj_type == "null":
                return None
            else:
                return None

        example = generate(schema_obj)
        return json.dumps(example, indent=2)

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        action = kwargs.get("action", "validate")
        if action == "generate":
            return self.schema_generate(kwargs.get("data", "{}"))
        return f"Unknown action: {action}"
