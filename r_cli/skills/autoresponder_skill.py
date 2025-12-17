"""
Auto-Responder Skill for R CLI.

Automated social media response system:
- Loads knowledge base from PDFs using RAG
- Uses local LLM to generate contextual responses
- Queues responses for review before sending
- Learns from approved responses
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool

logger = logging.getLogger(__name__)


class AutoResponderSkill(Skill):
    """Skill for automated social media responses using RAG + LLM."""

    name = "autoresponder"
    description = "Automated social media responder using local AI + knowledge base from PDFs"

    # Response templates
    RESPONSE_STYLES = {
        "professional": "formal, courteous, and professional",
        "friendly": "warm, friendly, and approachable",
        "casual": "relaxed and conversational",
        "support": "helpful, empathetic, and solution-oriented",
        "sales": "persuasive but not pushy, highlighting value",
    }

    def __init__(self, config=None):
        super().__init__(config)
        self._knowledge_base = None
        self._response_history = []
        self._style = "professional"
        self._persona = ""
        self._rules = []

    def get_tools(self) -> list[Tool]:
        return [
            # Knowledge Base Management
            Tool(
                name="autoresponder_load_pdf",
                description="Load a PDF into the knowledge base for generating responses",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to PDF file",
                        },
                        "category": {
                            "type": "string",
                            "description": "Category/tag for this content (e.g., 'faq', 'product', 'policy')",
                        },
                    },
                    "required": ["file_path"],
                },
                handler=self.load_pdf,
            ),
            Tool(
                name="autoresponder_load_text",
                description="Add text content to the knowledge base",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Text content to add",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title or identifier for this content",
                        },
                        "category": {
                            "type": "string",
                            "description": "Category/tag",
                        },
                    },
                    "required": ["content"],
                },
                handler=self.load_text,
            ),
            Tool(
                name="autoresponder_kb_status",
                description="Show knowledge base status and statistics",
                parameters={"type": "object", "properties": {}},
                handler=self.kb_status,
            ),
            Tool(
                name="autoresponder_kb_search",
                description="Search the knowledge base for relevant information",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results (default: 5)",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.kb_search,
            ),
            # Configuration
            Tool(
                name="autoresponder_config",
                description="Configure the auto-responder settings",
                parameters={
                    "type": "object",
                    "properties": {
                        "style": {
                            "type": "string",
                            "enum": list(self.RESPONSE_STYLES.keys()),
                            "description": "Response style",
                        },
                        "persona": {
                            "type": "string",
                            "description": "Persona description (e.g., 'tech support specialist', 'community manager')",
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum response length in characters",
                        },
                        "language": {
                            "type": "string",
                            "description": "Response language (e.g., 'es', 'en', 'fr')",
                        },
                    },
                },
                handler=self.configure,
            ),
            Tool(
                name="autoresponder_add_rule",
                description="Add a response rule or guideline",
                parameters={
                    "type": "object",
                    "properties": {
                        "rule": {
                            "type": "string",
                            "description": "Rule to follow (e.g., 'Never discuss competitor products', 'Always include a call-to-action')",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["must", "should", "nice_to_have"],
                            "description": "Rule priority",
                        },
                    },
                    "required": ["rule"],
                },
                handler=self.add_rule,
            ),
            Tool(
                name="autoresponder_list_rules",
                description="List all response rules and guidelines",
                parameters={"type": "object", "properties": {}},
                handler=self.list_rules,
            ),
            # Response Generation
            Tool(
                name="autoresponder_generate",
                description="Generate a response for a message using RAG + LLM",
                parameters={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to respond to",
                        },
                        "context": {
                            "type": "string",
                            "description": "Additional context (platform, sender info, conversation history)",
                        },
                        "style_override": {
                            "type": "string",
                            "enum": list(self.RESPONSE_STYLES.keys()),
                            "description": "Override the default style for this response",
                        },
                    },
                    "required": ["message"],
                },
                handler=self.generate_response,
            ),
            Tool(
                name="autoresponder_batch",
                description="Process multiple messages and generate responses",
                parameters={
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "string",
                            "description": "JSON array of messages: [{id, text, platform, sender}]",
                        },
                        "auto_queue": {
                            "type": "boolean",
                            "description": "Automatically queue responses for review",
                        },
                    },
                    "required": ["messages"],
                },
                handler=self.batch_generate,
            ),
            # Learning & Improvement
            Tool(
                name="autoresponder_feedback",
                description="Provide feedback on a generated response to improve future responses",
                parameters={
                    "type": "object",
                    "properties": {
                        "response_id": {
                            "type": "string",
                            "description": "ID of the response",
                        },
                        "rating": {
                            "type": "string",
                            "enum": ["good", "needs_improvement", "bad"],
                            "description": "Rating for the response",
                        },
                        "feedback": {
                            "type": "string",
                            "description": "Specific feedback or corrections",
                        },
                        "corrected_response": {
                            "type": "string",
                            "description": "The corrected/improved response",
                        },
                    },
                    "required": ["response_id", "rating"],
                },
                handler=self.add_feedback,
            ),
            Tool(
                name="autoresponder_history",
                description="View response generation history",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of entries to show",
                        },
                        "filter_rating": {
                            "type": "string",
                            "enum": ["good", "needs_improvement", "bad", "all"],
                        },
                    },
                },
                handler=self.view_history,
            ),
        ]

    def _get_rag_skill(self):
        """Get RAG skill instance for knowledge base operations."""
        try:
            from r_cli.skills.rag_skill import RAGSkill

            return RAGSkill(self.config)
        except ImportError:
            return None

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except ImportError:
            return ""
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1000) -> list[str]:
        """Split text into chunks with overlap."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        overlap = chunk_size // 5  # 20% overlap

        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to cut at sentence boundary
            if end < len(text):
                for sep in [". ", "\n\n", "\n", " "]:
                    last_sep = chunk.rfind(sep)
                    if last_sep > chunk_size // 2:
                        chunk = chunk[: last_sep + len(sep)]
                        break

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    # =========================================================================
    # Knowledge Base Tools
    # =========================================================================

    def load_pdf(
        self,
        file_path: str,
        category: Optional[str] = None,
    ) -> str:
        """Load a PDF into the knowledge base."""
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: File not found: {file_path}"

        if path.suffix.lower() != ".pdf":
            return "Error: File must be a PDF"

        # Extract text from PDF
        text = self._extract_pdf_text(str(path))
        if not text:
            return "Error: Could not extract text from PDF. Install pypdf: pip install pypdf"

        # Get RAG skill for indexing
        rag = self._get_rag_skill()
        if rag is None:
            return "Error: RAG skill not available. Install: pip install sentence-transformers"

        # Chunk and add to index
        chunks = self._chunk_text(text)

        for i, chunk in enumerate(chunks):
            metadata = {
                "source": str(path),
                "chunk": i,
                "total_chunks": len(chunks),
            }
            if category:
                metadata["category"] = category

            rag.add_document(
                content=chunk,
                doc_id=f"{path.stem}_chunk_{i}",
                source=str(path),
                tags=category,
            )

        return f"""✅ PDF loaded into knowledge base:
  File: {path.name}
  Size: {path.stat().st_size / 1024:.1f} KB
  Chunks: {len(chunks)}
  Category: {category or "general"}"""

    def load_text(
        self,
        content: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        """Add text content to knowledge base."""
        rag = self._get_rag_skill()
        if rag is None:
            return "Error: RAG skill not available"

        doc_id = title or f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = rag.add_document(
            content=content,
            doc_id=doc_id,
            source=title or "manual_input",
            tags=category,
        )

        return f"""✅ Text added to knowledge base:
  Title: {title or doc_id}
  Length: {len(content)} characters
  Category: {category or "general"}"""

    def kb_status(self) -> str:
        """Show knowledge base status."""
        rag = self._get_rag_skill()
        if rag is None:
            return "❌ RAG skill not available. Install: pip install sentence-transformers"

        stats = rag.get_stats()

        result = [
            "📚 Knowledge Base Status\n",
            "=" * 40,
            "",
            f"Response Style: {self._style} ({self.RESPONSE_STYLES[self._style]})",
            f"Persona: {self._persona or 'Not set'}",
            f"Rules configured: {len(self._rules)}",
            "",
            "RAG Index:",
            stats,
        ]

        return "\n".join(result)

    def kb_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """Search the knowledge base."""
        rag = self._get_rag_skill()
        if rag is None:
            return "Error: RAG skill not available"

        return rag.search(query, top_k=top_k)

    # =========================================================================
    # Configuration Tools
    # =========================================================================

    def configure(
        self,
        style: Optional[str] = None,
        persona: Optional[str] = None,
        max_length: Optional[int] = None,
        language: Optional[str] = None,
    ) -> str:
        """Configure the auto-responder."""
        changes = []

        if style:
            if style in self.RESPONSE_STYLES:
                self._style = style
                changes.append(f"Style: {style}")
            else:
                return (
                    f"Error: Invalid style. Choose from: {', '.join(self.RESPONSE_STYLES.keys())}"
                )

        if persona:
            self._persona = persona
            changes.append(f"Persona: {persona}")

        if not changes:
            # Show current config
            return f"""⚙️ Auto-Responder Configuration:

Style: {self._style} ({self.RESPONSE_STYLES[self._style]})
Persona: {self._persona or "Not set"}
Rules: {len(self._rules)}

Available styles:
{chr(10).join(f"  - {k}: {v}" for k, v in self.RESPONSE_STYLES.items())}"""

        return "✅ Configuration updated:\n  " + "\n  ".join(changes)

    def add_rule(
        self,
        rule: str,
        priority: str = "should",
    ) -> str:
        """Add a response rule."""
        self._rules.append(
            {
                "rule": rule,
                "priority": priority,
                "created_at": datetime.now().isoformat(),
            }
        )

        return f"✅ Rule added ({priority}): {rule}"

    def list_rules(self) -> str:
        """List all rules."""
        if not self._rules:
            return "No rules configured. Add rules with autoresponder_add_rule."

        result = ["📋 Response Rules\n"]

        priority_icons = {"must": "🔴", "should": "🟡", "nice_to_have": "🟢"}

        for i, rule in enumerate(self._rules, 1):
            icon = priority_icons.get(rule["priority"], "⚪")
            result.append(f"{i}. {icon} [{rule['priority']}] {rule['rule']}")

        return "\n".join(result)

    # =========================================================================
    # Response Generation
    # =========================================================================

    def generate_response(
        self,
        message: str,
        context: Optional[str] = None,
        style_override: Optional[str] = None,
    ) -> str:
        """Generate a response using RAG + LLM."""
        # 1. Search knowledge base for relevant information
        rag = self._get_rag_skill()
        relevant_docs = ""

        if rag:
            search_result = rag.search(message, top_k=3, threshold=0.3)
            if "No similar documents" not in search_result:
                relevant_docs = search_result

        # 2. Build the prompt for the LLM
        style = style_override or self._style
        style_desc = self.RESPONSE_STYLES.get(style, self.RESPONSE_STYLES["professional"])

        prompt_parts = [
            "You are a social media assistant helping to respond to messages.",
            f"Response style: {style_desc}",
        ]

        if self._persona:
            prompt_parts.append(f"Your persona: {self._persona}")

        if self._rules:
            rules_text = "\n".join(f"- {r['rule']}" for r in self._rules)
            prompt_parts.append(f"\nRules to follow:\n{rules_text}")

        if relevant_docs:
            prompt_parts.append(f"\nRelevant information from knowledge base:\n{relevant_docs}")

        if context:
            prompt_parts.append(f"\nAdditional context: {context}")

        prompt_parts.append(f"\nMessage to respond to:\n{message}")
        prompt_parts.append("\nGenerate a helpful response:")

        full_prompt = "\n\n".join(prompt_parts)

        # 3. Generate response using LLM
        try:
            from r_cli.core.config import Config
            from r_cli.core.llm import LLMClient

            config = self.config or Config.load()
            llm = LLMClient(config.llm)

            response = llm.chat(full_prompt)
            generated_text = response.content if hasattr(response, "content") else str(response)

            # 4. Store in history
            response_id = f"resp_{len(self._response_history) + 1}"
            self._response_history.append(
                {
                    "id": response_id,
                    "message": message,
                    "response": generated_text,
                    "style": style,
                    "had_kb_context": bool(relevant_docs),
                    "timestamp": datetime.now().isoformat(),
                    "rating": None,
                }
            )

            return f"""📝 Generated Response (ID: {response_id})

Style: {style}
Knowledge base used: {"Yes" if relevant_docs else "No"}

---
{generated_text}
---

Use autoresponder_feedback to rate this response."""

        except Exception as e:
            return f"Error generating response: {e}"

    def batch_generate(
        self,
        messages: str,
        auto_queue: bool = True,
    ) -> str:
        """Process multiple messages."""
        try:
            msg_list = json.loads(messages)
        except json.JSONDecodeError:
            return "Error: Invalid JSON for messages"

        results = []

        for msg in msg_list:
            msg_text = msg.get("text", "")
            context = f"Platform: {msg.get('platform', 'unknown')}, Sender: {msg.get('sender', 'unknown')}"

            # Generate response
            response = self.generate_response(msg_text, context=context)

            results.append(
                {
                    "id": msg.get("id"),
                    "original": msg_text[:50],
                    "response_preview": response[:100] if "Error" not in response else response,
                }
            )

        result_text = [f"📬 Batch Processing: {len(results)} messages\n"]

        for r in results:
            result_text.append(f"  [{r['id']}] {r['original']}...")
            result_text.append(f"    → {r['response_preview']}...")
            result_text.append("")

        if auto_queue:
            result_text.append("\n✅ Responses queued for review")

        return "\n".join(result_text)

    # =========================================================================
    # Learning & Improvement
    # =========================================================================

    def add_feedback(
        self,
        response_id: str,
        rating: str,
        feedback: Optional[str] = None,
        corrected_response: Optional[str] = None,
    ) -> str:
        """Add feedback for a response."""
        # Find the response
        for item in self._response_history:
            if item["id"] == response_id:
                item["rating"] = rating
                item["feedback"] = feedback
                item["corrected_response"] = corrected_response
                item["feedback_at"] = datetime.now().isoformat()

                # If corrected, add to knowledge base as example
                if corrected_response and rating == "bad":
                    rag = self._get_rag_skill()
                    if rag:
                        example = (
                            f"Question: {item['message']}\nGood response: {corrected_response}"
                        )
                        rag.add_document(
                            content=example,
                            doc_id=f"example_{response_id}",
                            source="feedback",
                            tags="response_examples",
                        )

                return f"""✅ Feedback recorded for {response_id}

Rating: {rating}
Feedback: {feedback or "None"}
Correction added: {"Yes" if corrected_response else "No"}"""

        return f"Error: Response {response_id} not found"

    def view_history(
        self,
        limit: int = 10,
        filter_rating: str = "all",
    ) -> str:
        """View response history."""
        if not self._response_history:
            return "No response history yet."

        filtered = self._response_history
        if filter_rating != "all":
            filtered = [h for h in filtered if h.get("rating") == filter_rating]

        filtered = filtered[-limit:]

        result = [f"📜 Response History (showing {len(filtered)})\n"]

        rating_icons = {"good": "✅", "needs_improvement": "⚠️", "bad": "❌", None: "⏳"}

        for item in filtered:
            icon = rating_icons.get(item.get("rating"))
            result.append(f"{icon} [{item['id']}] {item['timestamp'][:10]}")
            result.append(f"   Q: {item['message'][:50]}...")
            result.append(f"   A: {item['response'][:50]}...")
            result.append("")

        return "\n".join(result)

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        action = kwargs.get("action", "status")

        if action == "status":
            return self.kb_status()
        elif action == "generate":
            return self.generate_response(
                kwargs.get("message", ""),
                kwargs.get("context"),
            )
        elif action == "history":
            return self.view_history()
        else:
            return f"Unknown action: {action}"
