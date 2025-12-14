"""
Main agent for R CLI.

Orchestrates:
- LLM Client for reasoning
- Skills for task execution
- Memory for context
- UI for user feedback
"""

import os
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from r_cli.core.config import Config
from r_cli.core.llm import LLMClient, Tool
from r_cli.core.memory import Memory

console = Console()


# Base system prompt for the agent
SYSTEM_PROMPT = """You are R, a local AI assistant that runs 100% offline in the user's terminal.

Your personality:
- Direct and efficient (no unnecessary flourishes)
- Technically competent
- Action-oriented (prefer to act rather than ask too many questions)

Capabilities:
- Generate documents (PDF, LaTeX, Markdown)
- Summarize long texts
- Write and analyze code
- SQL queries in natural language
- Manage local files
- Remember context from previous conversations

Restrictions:
- You can only access the user's local files
- You have no internet access
- Respond in the same language as the user

When using tools:
1. Briefly explain what you're going to do
2. Execute the tool
3. Report the result concisely

If you can't do something, explain why and suggest alternatives.
"""


class Agent:
    """
    Main agent that processes user requests.

    Usage:
    ```python
    agent = Agent()
    response = agent.run("Generate a PDF with the project summary")
    ```
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.ensure_directories()

        # Core components
        self.llm = LLMClient(self.config)
        self.memory = Memory(self.config)

        # Registered skills (loaded dynamically)
        self.skills: dict[str, Skill] = {}
        self.tools: list[Tool] = []

        # State
        self.is_running = False

        # Configure LLM
        self._setup_llm()

    def _setup_llm(self) -> None:
        """Configure the LLM with system prompt and context."""
        # Load previous session if exists
        if self.memory.load_session():
            session_summary = self.memory.get_session_summary()
            full_prompt = f"{SYSTEM_PROMPT}\n\n{session_summary}"
        else:
            full_prompt = SYSTEM_PROMPT

        self.llm.set_system_prompt(full_prompt)

    def register_skill(self, skill: "Skill") -> None:
        """Register a skill and its tools."""
        self.skills[skill.name] = skill

        # Add skill's tools
        for tool in skill.get_tools():
            self.tools.append(tool)

        console.print(f"[dim]Skill registered: {skill.name}[/dim]")

    def load_skills(self) -> None:
        """Load all available skills, respecting configuration."""
        from r_cli.skills import get_all_skills

        for skill_class in get_all_skills():
            try:
                skill = skill_class(self.config)

                # Check if skill is enabled in config
                if not self.config.skills.is_skill_enabled(skill.name):
                    console.print(f"[dim]Skill disabled in config: {skill.name}[/dim]")
                    continue

                self.register_skill(skill)
            except ImportError as e:
                console.print(
                    f"[yellow]Missing dependency for {skill_class.__name__}: {e}[/yellow]"
                )
            except TypeError as e:
                console.print(
                    f"[yellow]Configuration error in {skill_class.__name__}: {e}[/yellow]"
                )
            except OSError as e:
                console.print(f"[yellow]File/IO error in {skill_class.__name__}: {e}[/yellow]")
            except Exception as e:
                console.print(
                    f"[yellow]Unexpected error loading {skill_class.__name__}: {e}[/yellow]"
                )

    def run(self, user_input: str, show_thinking: bool = True) -> str:
        """
        Process user input and return response.

        Args:
            user_input: User's message
            show_thinking: Whether to show reasoning process

        Returns:
            Agent's response
        """
        # Add to memory
        self.memory.add_short_term(user_input, entry_type="user_input")

        # Get relevant context
        context = self.memory.get_relevant_context(user_input)

        # Prepare message with context
        if context:
            augmented_input = f"{user_input}\n\n[Available context]\n{context}"
        else:
            augmented_input = user_input

        # Execute with tools if skills are registered
        if self.tools:
            response = self.llm.chat_with_tools(augmented_input, self.tools)
        else:
            response_msg = self.llm.chat(augmented_input)
            response = response_msg.content or ""

        # Add response to memory
        self.memory.add_short_term(response, entry_type="agent_response")

        # Save session
        self.memory.save_session()

        return response

    def run_stream(self, user_input: str):
        """
        Process user input with streaming.

        Yields response chunks as they arrive.

        Args:
            user_input: User's message

        Yields:
            Text chunks of the response
        """
        # Add to memory
        self.memory.add_short_term(user_input, entry_type="user_input")

        # Get relevant context
        context = self.memory.get_relevant_context(user_input)

        # Prepare message with context
        if context:
            augmented_input = f"{user_input}\n\n[Available context]\n{context}"
        else:
            augmented_input = user_input

        # Use streaming (without tools for simple streaming)
        full_response = ""
        for chunk in self.llm.chat_stream_sync(augmented_input):
            full_response += chunk
            yield chunk

        # Add complete response to memory
        self.memory.add_short_term(full_response, entry_type="agent_response")

        # Save session
        self.memory.save_session()

    def run_skill_directly(self, skill_name: str, **kwargs) -> str:
        """
        Execute a skill directly without going through the LLM.

        Useful for direct commands like: r pdf "content"
        """
        if skill_name not in self.skills:
            return f"Skill not found: {skill_name}"

        skill = self.skills[skill_name]
        return skill.execute(**kwargs)

    def check_connection(self) -> bool:
        """Check connection to the LLM server."""
        return self.llm._check_connection()

    def get_available_skills(self) -> list[str]:
        """Return list of available skills."""
        return list(self.skills.keys())

    def show_help(self) -> None:
        """Show help about available skills."""
        help_text = "# Available Skills\n\n"

        for name, skill in self.skills.items():
            help_text += f"## {name}\n"
            help_text += f"{skill.description}\n\n"
            help_text += f"**Usage:** `r {name} <args>`\n\n"

        console.print(Panel(Markdown(help_text), title="R CLI Help", border_style="blue"))


class Skill:
    """
    Base class for skills.

    Skills are specialized mini-programs that the agent can use.

    Implementation example:
    ```python
    class PDFSkill(Skill):
        name = "pdf"
        description = "Generate PDF documents"

        def get_tools(self) -> list[Tool]:
            return [
                Tool(
                    name="generate_pdf",
                    description="Generate a PDF",
                    parameters={...},
                    handler=self.generate_pdf,
                )
            ]

        def generate_pdf(self, content: str, output: str) -> str:
            # Implementation
            return f"PDF generated: {output}"
    ```
    """

    name: str = "base_skill"
    description: str = "Base skill"

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.output_dir = os.path.expanduser(self.config.output_dir)

    def get_tools(self) -> list[Tool]:
        """Return the tools this skill provides."""
        return []

    def execute(self, **kwargs) -> str:
        """Direct execution of the skill (without LLM)."""
        return "Not implemented"
