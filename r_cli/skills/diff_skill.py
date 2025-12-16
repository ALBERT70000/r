"""
Diff Skill for R CLI.

Text and file diff utilities:
- Compare texts/files
- Generate patches
- Apply patches
- Unified/context diff
"""

import difflib
import json
from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class DiffSkill(Skill):
    """Skill for diff operations."""

    name = "diff"
    description = "Diff: compare texts/files, patches"

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="diff_texts",
                description="Compare two texts",
                parameters={
                    "type": "object",
                    "properties": {
                        "text1": {
                            "type": "string",
                            "description": "First text",
                        },
                        "text2": {
                            "type": "string",
                            "description": "Second text",
                        },
                        "format": {
                            "type": "string",
                            "description": "Format: unified, context, ndiff, html",
                        },
                    },
                    "required": ["text1", "text2"],
                },
                handler=self.diff_texts,
            ),
            Tool(
                name="diff_files",
                description="Compare two files",
                parameters={
                    "type": "object",
                    "properties": {
                        "file1": {
                            "type": "string",
                            "description": "First file path",
                        },
                        "file2": {
                            "type": "string",
                            "description": "Second file path",
                        },
                        "format": {
                            "type": "string",
                            "description": "Format: unified, context, ndiff",
                        },
                    },
                    "required": ["file1", "file2"],
                },
                handler=self.diff_files,
            ),
            Tool(
                name="diff_summary",
                description="Get summary of differences",
                parameters={
                    "type": "object",
                    "properties": {
                        "text1": {
                            "type": "string",
                            "description": "First text",
                        },
                        "text2": {
                            "type": "string",
                            "description": "Second text",
                        },
                    },
                    "required": ["text1", "text2"],
                },
                handler=self.diff_summary,
            ),
            Tool(
                name="diff_words",
                description="Word-level diff between texts",
                parameters={
                    "type": "object",
                    "properties": {
                        "text1": {
                            "type": "string",
                            "description": "First text",
                        },
                        "text2": {
                            "type": "string",
                            "description": "Second text",
                        },
                    },
                    "required": ["text1", "text2"],
                },
                handler=self.diff_words,
            ),
            Tool(
                name="patch_create",
                description="Create a patch from two texts",
                parameters={
                    "type": "object",
                    "properties": {
                        "original": {
                            "type": "string",
                            "description": "Original text",
                        },
                        "modified": {
                            "type": "string",
                            "description": "Modified text",
                        },
                        "filename": {
                            "type": "string",
                            "description": "Filename for patch header",
                        },
                    },
                    "required": ["original", "modified"],
                },
                handler=self.patch_create,
            ),
            Tool(
                name="similarity_ratio",
                description="Calculate similarity ratio between texts",
                parameters={
                    "type": "object",
                    "properties": {
                        "text1": {
                            "type": "string",
                            "description": "First text",
                        },
                        "text2": {
                            "type": "string",
                            "description": "Second text",
                        },
                    },
                    "required": ["text1", "text2"],
                },
                handler=self.similarity_ratio,
            ),
        ]

    def diff_texts(
        self,
        text1: str,
        text2: str,
        format: str = "unified",
    ) -> str:
        """Compare two texts."""
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)

        if format == "unified":
            diff = difflib.unified_diff(lines1, lines2, fromfile="text1", tofile="text2")
        elif format == "context":
            diff = difflib.context_diff(lines1, lines2, fromfile="text1", tofile="text2")
        elif format == "ndiff":
            diff = difflib.ndiff(lines1, lines2)
        elif format == "html":
            differ = difflib.HtmlDiff()
            return differ.make_table(lines1, lines2, fromdesc="Text 1", todesc="Text 2")
        else:
            diff = difflib.unified_diff(lines1, lines2)

        result = "".join(diff)
        return result if result else "No differences found"

    def diff_files(
        self,
        file1: str,
        file2: str,
        format: str = "unified",
    ) -> str:
        """Compare two files."""
        path1 = Path(file1).expanduser()
        path2 = Path(file2).expanduser()

        if not path1.exists():
            return f"File not found: {file1}"
        if not path2.exists():
            return f"File not found: {file2}"

        try:
            text1 = path1.read_text()
            text2 = path2.read_text()

            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)

            if format == "unified":
                diff = difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2)
            elif format == "context":
                diff = difflib.context_diff(lines1, lines2, fromfile=file1, tofile=file2)
            elif format == "ndiff":
                diff = difflib.ndiff(lines1, lines2)
            else:
                diff = difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2)

            result = "".join(diff)
            return result if result else "No differences found"

        except Exception as e:
            return f"Error: {e}"

    def diff_summary(self, text1: str, text2: str) -> str:
        """Get diff summary."""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        opcodes = matcher.get_opcodes()

        stats = {
            "equal": 0,
            "replace": 0,
            "insert": 0,
            "delete": 0,
        }

        changes = []
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                stats["equal"] += i2 - i1
            elif tag == "replace":
                stats["replace"] += max(i2 - i1, j2 - j1)
                changes.append(f"Replace lines {i1 + 1}-{i2} with {j2 - j1} new lines")
            elif tag == "insert":
                stats["insert"] += j2 - j1
                changes.append(f"Insert {j2 - j1} lines after line {i1}")
            elif tag == "delete":
                stats["delete"] += i2 - i1
                changes.append(f"Delete lines {i1 + 1}-{i2}")

        return json.dumps(
            {
                "lines_text1": len(lines1),
                "lines_text2": len(lines2),
                "stats": stats,
                "similarity": f"{matcher.ratio() * 100:.1f}%",
                "changes": changes[:20],  # Limit changes shown
            },
            indent=2,
        )

    def diff_words(self, text1: str, text2: str) -> str:
        """Word-level diff."""
        words1 = text1.split()
        words2 = text2.split()

        matcher = difflib.SequenceMatcher(None, words1, words2)

        result = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                result.append(" ".join(words1[i1:i2]))
            elif tag == "replace":
                result.append(f"[-{' '.join(words1[i1:i2])}-]")
                result.append(f"[+{' '.join(words2[j1:j2])}+]")
            elif tag == "insert":
                result.append(f"[+{' '.join(words2[j1:j2])}+]")
            elif tag == "delete":
                result.append(f"[-{' '.join(words1[i1:i2])}-]")

        return " ".join(result)

    def patch_create(
        self,
        original: str,
        modified: str,
        filename: str = "file",
    ) -> str:
        """Create unified patch."""
        lines1 = original.splitlines(keepends=True)
        lines2 = modified.splitlines(keepends=True)

        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )

        return "".join(diff)

    def similarity_ratio(self, text1: str, text2: str) -> str:
        """Calculate similarity ratio."""
        # Line-based
        matcher_lines = difflib.SequenceMatcher(None, text1.splitlines(), text2.splitlines())

        # Character-based
        matcher_chars = difflib.SequenceMatcher(None, text1, text2)

        # Word-based
        matcher_words = difflib.SequenceMatcher(None, text1.split(), text2.split())

        return json.dumps(
            {
                "line_similarity": f"{matcher_lines.ratio() * 100:.2f}%",
                "word_similarity": f"{matcher_words.ratio() * 100:.2f}%",
                "char_similarity": f"{matcher_chars.ratio() * 100:.2f}%",
                "quick_ratio": f"{matcher_chars.quick_ratio() * 100:.2f}%",
            },
            indent=2,
        )

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        return self.diff_texts(
            kwargs.get("text1", ""),
            kwargs.get("text2", ""),
        )
