"""
Main terminal interface for R CLI.

Handles:
- Rendering formatted responses
- Information panels
- Skills/commands tables
- Conversation history
"""

from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from r_cli.ui.themes import get_theme


class Terminal:
    """
    Rich terminal interface for R CLI.

    Usage:
    ```python
    term = Terminal(theme="ps2")
    term.print_welcome()
    term.print_response("Hello, I'm R!")
    term.print_skill_list(skills)
    ```
    """

    def __init__(self, theme: str = "ps2"):
        self.console = Console()
        self.theme = get_theme(theme)

    def print(self, message: str = "", style: Optional[str] = None):
        """Print a simple message."""
        if message:
            self.console.print(message, style=style or self.theme.secondary)
        else:
            self.console.print()

    def print_welcome(self):
        """Display welcome banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██████╗        ██████╗██╗     ██╗                        ║
║     ██╔══██╗      ██╔════╝██║     ██║                        ║
║     ██████╔╝█████╗██║     ██║     ██║                        ║
║     ██╔══██╗╚════╝██║     ██║     ██║                        ║
║     ██║  ██║      ╚██████╗███████╗██║                        ║
║     ╚═╝  ╚═╝       ╚═════╝╚══════╝╚═╝                        ║
║                                                               ║
║     Local AI Operating System                                 ║
║     100% Private · 100% Offline · 100% Yours                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
        """

        self.console.print(banner, style=self.theme.primary)
        self.console.print()

    def print_status(self, llm_connected: bool, skills_count: int):
        """Display system status."""
        status = Table(show_header=False, box=None, padding=(0, 2))
        status.add_column()
        status.add_column()

        # LLM status
        if llm_connected:
            status.add_row(
                f"[{self.theme.success}]{self.theme.success_symbol}[/] LLM",
                "[green]Connected[/green]",
            )
        else:
            status.add_row(
                f"[{self.theme.error}]{self.theme.error_symbol}[/] LLM", "[red]Disconnected[/red]"
            )

        status.add_row(
            f"[{self.theme.secondary}]◈[/] Skills",
            f"[{self.theme.secondary}]{skills_count} available[/]",
        )

        self.console.print(Panel(status, title="Status", border_style=self.theme.dim))

    def print_response(self, response: str, title: str = "R"):
        """Display agent response with formatting."""
        # Detect if it's markdown
        if any(marker in response for marker in ["```", "##", "- ", "**"]):
            content = Markdown(response)
        else:
            content = response

        self.console.print(
            Panel(
                content,
                title=f"[{self.theme.primary}]{title}[/]",
                border_style=self.theme.accent,
                padding=(1, 2),
            )
        )

    def print_stream_start(self, title: str = "R"):
        """Start a streaming response."""
        self.console.print(f"\n[{self.theme.primary}]{title}:[/] ", end="")
        self._stream_buffer = ""

    def print_stream_chunk(self, chunk: str):
        """Print a streaming chunk."""
        self.console.print(chunk, end="", markup=False)
        self._stream_buffer = getattr(self, "_stream_buffer", "") + chunk

    def print_stream_end(self):
        """End a streaming response."""
        self.console.print()  # New line at the end
        return getattr(self, "_stream_buffer", "")

    def print_user_input(self, message: str):
        """Display user input."""
        self.console.print(f"[{self.theme.dim}]You:[/] [{self.theme.secondary}]{message}[/]")

    def print_thinking(self, message: str = "Thinking"):
        """Display 'thinking' indicator."""
        return Progress(
            SpinnerColumn(spinner_name="dots", style=self.theme.accent),
            TextColumn(f"[{self.theme.dim}]{message}...[/]"),
            console=self.console,
            transient=True,
        )

    def print_skill_list(self, skills: dict):
        """Display available skills table."""
        table = Table(
            title="Available Skills",
            show_header=True,
            header_style=self.theme.primary,
            border_style=self.theme.dim,
        )

        table.add_column("Skill", style=self.theme.accent)
        table.add_column("Description", style=self.theme.secondary)
        table.add_column("Command", style=self.theme.dim)

        for name, skill in skills.items():
            table.add_row(
                name,
                skill.description,
                f"r {name} <args>",
            )

        self.console.print(table)

    def print_tool_call(self, tool_name: str, args: dict):
        """Display a tool call."""
        args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        self.console.print(
            f"[{self.theme.dim}]  {self.theme.thinking_symbol} {tool_name}({args_str})[/]"
        )

    def print_tool_result(self, result: str):
        """Display tool result."""
        # Truncate if too long
        if len(result) > 500:
            result = result[:500] + "..."

        self.console.print(
            Panel(
                result,
                title="Result",
                border_style=self.theme.dim,
                padding=(0, 1),
            )
        )

    def print_error(self, message: str):
        """Display an error."""
        self.console.print(f"[{self.theme.error}]{self.theme.error_symbol} Error: {message}[/]")

    def print_success(self, message: str):
        """Display a success message."""
        self.console.print(f"[{self.theme.success}]{self.theme.success_symbol} {message}[/]")

    def print_warning(self, message: str):
        """Display a warning."""
        self.console.print(f"[{self.theme.warning}]⚠ {message}[/]")

    def print_code(self, code: str, language: str = "python"):
        """Display code with syntax highlighting."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_file_tree(self, path: str, files: list[str]):
        """Display file tree."""
        tree = Tree(f"📁 {path}", style=self.theme.accent)

        for f in files[:20]:  # Limit
            if f.endswith("/"):
                tree.add(f"📁 {f}", style=self.theme.secondary)
            else:
                tree.add(f"📄 {f}", style=self.theme.dim)

        if len(files) > 20:
            tree.add(f"... and {len(files) - 20} more", style=self.theme.dim)

        self.console.print(tree)

    def get_input(self, prompt: str = "") -> str:
        """Get user input."""
        symbol = self.theme.prompt_symbol
        return self.console.input(f"[{self.theme.primary}]{symbol}[/] {prompt}")

    def clear(self):
        """Clear the screen."""
        self.console.clear()

    def print_help(self):
        """Display general help."""
        help_text = """
# R CLI - Commands

## Chat
Simply type your message to chat with R.

## Skills (direct commands)
- `r pdf "content"` - Generate a PDF
- `r code script.py` - Create code
- `r sql "query"` - Execute SQL
- `r resume document.pdf` - Summarize document
- `r fs list` - List files

## Control
- `/help` - Show this help
- `/skills` - List available skills
- `/clear` - Clear screen
- `/config` - Show configuration
- `/exit` - Exit

## Examples
```
> Generate a PDF report about Python
> Summarize this document: report.pdf
> SELECT * FROM sales WHERE year = 2024
> Create a function that sorts a list
```
        """

        self.console.print(Markdown(help_text))
