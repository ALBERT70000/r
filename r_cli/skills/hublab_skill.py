"""
HubLab Skill for R CLI.

Integration with HubLab.dev - Universal Capsule Compiler.
Access 8,150+ pre-built UI capsules for multi-platform development.

Features:
- Search capsules by name, category, or tags
- Get capsule details and code
- List categories and explore the catalog
- Suggest components for app descriptions
"""

import json
import os
from pathlib import Path
from typing import Optional
import urllib.request

from r_cli.core.agent import Skill
from r_cli.core.llm import Tool


class HubLabSkill(Skill):
    """Skill for HubLab capsule operations."""

    name = "hublab"
    description = "HubLab: search 8,150+ UI capsules, generate component code"

    # Default paths
    HUBLAB_PATH = os.environ.get("HUBLAB_PATH", "/Users/c/hublab")
    METADATA_FILE = "lib/capsules-metadata.json"
    CAPSULES_FILE = "lib/all-capsules.ts"
    API_BASE = "https://hublab.dev/api"

    def __init__(self):
        """Initialize HubLab skill."""
        super().__init__()
        self._capsules_cache: Optional[list] = None
        self._categories_cache: Optional[dict] = None

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="hublab_search",
                description="Search HubLab capsules by name, category, or tags",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (name, tag, or description)",
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by category (e.g., UI, Layout, Form)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results (default: 20)",
                        },
                    },
                    "required": ["query"],
                },
                handler=self.hublab_search,
            ),
            Tool(
                name="hublab_capsule",
                description="Get details for a specific capsule",
                parameters={
                    "type": "object",
                    "properties": {
                        "capsule_id": {
                            "type": "string",
                            "description": "Capsule ID (e.g., button, card, form)",
                        },
                    },
                    "required": ["capsule_id"],
                },
                handler=self.hublab_capsule,
            ),
            Tool(
                name="hublab_categories",
                description="List all capsule categories with counts",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.hublab_categories,
            ),
            Tool(
                name="hublab_browse",
                description="Browse capsules by category",
                parameters={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Category to browse",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results (default: 30)",
                        },
                    },
                    "required": ["category"],
                },
                handler=self.hublab_browse,
            ),
            Tool(
                name="hublab_suggest",
                description="Suggest capsules for an app description",
                parameters={
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "App or feature description",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max suggestions (default: 15)",
                        },
                    },
                    "required": ["description"],
                },
                handler=self.hublab_suggest,
            ),
            Tool(
                name="hublab_code",
                description="Get React/TypeScript code for a capsule",
                parameters={
                    "type": "object",
                    "properties": {
                        "capsule_id": {
                            "type": "string",
                            "description": "Capsule ID",
                        },
                        "platform": {
                            "type": "string",
                            "description": "Platform: react (default), swift, kotlin",
                        },
                    },
                    "required": ["capsule_id"],
                },
                handler=self.hublab_code,
            ),
            Tool(
                name="hublab_stats",
                description="Get HubLab catalog statistics",
                parameters={
                    "type": "object",
                    "properties": {},
                },
                handler=self.hublab_stats,
            ),
        ]

    def _load_capsules(self) -> list:
        """Load capsules from local metadata file."""
        if self._capsules_cache is not None:
            return self._capsules_cache

        metadata_path = Path(self.HUBLAB_PATH) / self.METADATA_FILE

        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    self._capsules_cache = json.load(f)
                return self._capsules_cache
            except Exception:
                pass

        # Fallback to API
        try:
            req = urllib.request.Request(
                f"{self.API_BASE}/ai/capsules",
                headers={"User-Agent": "R-CLI/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                self._capsules_cache = data.get("capsules", [])
                return self._capsules_cache
        except Exception:
            return []

    def _get_categories(self) -> dict:
        """Get category counts."""
        if self._categories_cache is not None:
            return self._categories_cache

        capsules = self._load_capsules()
        categories = {}

        for cap in capsules:
            cat = cap.get("category", "Other")
            categories[cat] = categories.get(cat, 0) + 1

        self._categories_cache = categories
        return categories

    def _match_score(self, capsule: dict, query: str) -> int:
        """Calculate match score for ranking."""
        query = query.lower()
        score = 0

        # Exact ID match
        if capsule.get("id", "").lower() == query:
            score += 100

        # Name match
        name = capsule.get("name", "").lower()
        if query in name:
            score += 50
        if name.startswith(query):
            score += 30

        # Tag match
        tags = [t.lower() for t in capsule.get("tags", [])]
        if query in tags:
            score += 40
        for tag in tags:
            if query in tag:
                score += 10

        # Description match
        desc = capsule.get("description", "").lower()
        if query in desc:
            score += 20

        # Category match
        if query in capsule.get("category", "").lower():
            score += 15

        return score

    def hublab_search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """Search capsules."""
        capsules = self._load_capsules()

        if not capsules:
            return json.dumps({
                "error": "Could not load capsules. Check HUBLAB_PATH or API.",
                "hint": f"Set HUBLAB_PATH env var (current: {self.HUBLAB_PATH})",
            }, indent=2)

        # Filter by category if specified
        if category:
            capsules = [
                c for c in capsules
                if c.get("category", "").lower() == category.lower()
            ]

        # Score and rank
        scored = []
        for cap in capsules:
            score = self._match_score(cap, query)
            if score > 0:
                scored.append((score, cap))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, cap in scored[:limit]:
            results.append({
                "id": cap.get("id"),
                "name": cap.get("name"),
                "category": cap.get("category"),
                "description": cap.get("description", "")[:150],
                "tags": cap.get("tags", [])[:5],
                "score": score,
            })

        return json.dumps({
            "query": query,
            "category_filter": category,
            "count": len(results),
            "total_searched": len(capsules),
            "results": results,
        }, indent=2)

    def hublab_capsule(self, capsule_id: str) -> str:
        """Get capsule details."""
        capsules = self._load_capsules()

        for cap in capsules:
            if cap.get("id", "").lower() == capsule_id.lower():
                return json.dumps({
                    "found": True,
                    "capsule": {
                        "id": cap.get("id"),
                        "name": cap.get("name"),
                        "category": cap.get("category"),
                        "description": cap.get("description"),
                        "tags": cap.get("tags", []),
                        "platform": cap.get("platform", "react"),
                    },
                    "usage": f"Import and use <{cap.get('name', capsule_id)} /> in your React app",
                    "docs_url": f"https://hublab.dev/capsules/{capsule_id}",
                }, indent=2)

        # Try partial match
        matches = []
        for cap in capsules:
            if capsule_id.lower() in cap.get("id", "").lower():
                matches.append(cap.get("id"))

        return json.dumps({
            "found": False,
            "capsule_id": capsule_id,
            "similar": matches[:10] if matches else [],
            "hint": "Use hublab_search to find capsules",
        }, indent=2)

    def hublab_categories(self) -> str:
        """List all categories."""
        categories = self._get_categories()

        # Sort by count descending
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

        return json.dumps({
            "total_categories": len(categories),
            "total_capsules": sum(categories.values()),
            "categories": [
                {"name": name, "count": count}
                for name, count in sorted_cats
            ],
        }, indent=2)

    def hublab_browse(
        self,
        category: str,
        limit: int = 30,
    ) -> str:
        """Browse capsules by category."""
        capsules = self._load_capsules()

        results = []
        for cap in capsules:
            if cap.get("category", "").lower() == category.lower():
                results.append({
                    "id": cap.get("id"),
                    "name": cap.get("name"),
                    "description": cap.get("description", "")[:100],
                    "tags": cap.get("tags", [])[:3],
                })

                if len(results) >= limit:
                    break

        if not results:
            # Try partial match
            categories = self._get_categories()
            matches = [c for c in categories if category.lower() in c.lower()]

            return json.dumps({
                "category": category,
                "count": 0,
                "hint": f"Category not found. Similar: {matches[:5]}",
                "all_categories_url": "Use hublab_categories to see all",
            }, indent=2)

        return json.dumps({
            "category": category,
            "count": len(results),
            "capsules": results,
        }, indent=2)

    def hublab_suggest(
        self,
        description: str,
        limit: int = 15,
    ) -> str:
        """Suggest capsules for an app description."""
        capsules = self._load_capsules()

        # Extract keywords from description
        words = description.lower().replace(",", " ").replace(".", " ").split()
        keywords = [w for w in words if len(w) > 2]

        # Common UI term mappings
        term_map = {
            "login": ["auth", "login", "form", "input"],
            "signup": ["auth", "register", "form"],
            "dashboard": ["dashboard", "chart", "card", "stats"],
            "cart": ["cart", "ecommerce", "shopping"],
            "chat": ["chat", "message", "realtime"],
            "profile": ["profile", "avatar", "user"],
            "settings": ["settings", "form", "toggle"],
            "table": ["table", "data", "grid"],
            "list": ["list", "item", "collection"],
            "search": ["search", "filter", "input"],
            "payment": ["payment", "stripe", "checkout"],
            "upload": ["upload", "file", "media"],
            "notification": ["notification", "alert", "toast"],
            "modal": ["modal", "dialog", "popup"],
            "navigation": ["nav", "menu", "sidebar"],
            "form": ["form", "input", "validation"],
            "button": ["button", "cta", "action"],
        }

        # Expand keywords with mappings
        expanded = set(keywords)
        for word in keywords:
            if word in term_map:
                expanded.update(term_map[word])

        # Score capsules
        scored = []
        for cap in capsules:
            score = 0
            cap_text = f"{cap.get('id', '')} {cap.get('name', '')} {cap.get('description', '')} {' '.join(cap.get('tags', []))}".lower()

            for kw in expanded:
                if kw in cap_text:
                    score += 10
                    if kw in cap.get("tags", []):
                        score += 5

            if score > 0:
                scored.append((score, cap))

        scored.sort(key=lambda x: x[0], reverse=True)

        suggestions = []
        seen_categories = {}

        for score, cap in scored:
            cat = cap.get("category", "Other")
            # Limit per category for diversity
            if seen_categories.get(cat, 0) >= 3:
                continue

            seen_categories[cat] = seen_categories.get(cat, 0) + 1
            suggestions.append({
                "id": cap.get("id"),
                "name": cap.get("name"),
                "category": cat,
                "reason": f"Matches: {', '.join([k for k in expanded if k in cap.get('id', '').lower() or k in ' '.join(cap.get('tags', [])).lower()][:3])}",
            })

            if len(suggestions) >= limit:
                break

        return json.dumps({
            "description": description[:100],
            "keywords_detected": list(expanded)[:15],
            "suggestion_count": len(suggestions),
            "suggestions": suggestions,
            "next_step": "Use hublab_code to get implementation code",
        }, indent=2)

    def hublab_code(
        self,
        capsule_id: str,
        platform: str = "react",
    ) -> str:
        """Get code for a capsule."""
        capsules = self._load_capsules()

        # Find capsule
        capsule = None
        for cap in capsules:
            if cap.get("id", "").lower() == capsule_id.lower():
                capsule = cap
                break

        if not capsule:
            return json.dumps({
                "error": f"Capsule not found: {capsule_id}",
                "hint": "Use hublab_search to find valid capsule IDs",
            }, indent=2)

        # Try to load code from all-capsules.ts
        capsules_ts_path = Path(self.HUBLAB_PATH) / self.CAPSULES_FILE

        code = None
        if capsules_ts_path.exists():
            try:
                content = capsules_ts_path.read_text()
                # Simple extraction (capsule definitions are in the file)
                # This is a basic implementation - for production use proper parsing
                import re

                # Look for capsule definition
                pattern = rf'["\']?{capsule_id}["\']?\s*:\s*\{{[^}}]+\}}'
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)

                if match:
                    code = f"// Found in all-capsules.ts\n{match.group(0)}"
            except Exception:
                pass

        # Generate example code based on capsule info
        name = capsule.get("name", capsule_id.title())
        component_name = "".join(word.title() for word in name.split())

        if platform == "react":
            example_code = f'''// {name} Component
// From HubLab: https://hublab.dev/capsules/{capsule_id}

import React from 'react';

interface {component_name}Props {{
  // Add props based on capsule requirements
  className?: string;
  children?: React.ReactNode;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
  className = '',
  children,
}}) => {{
  return (
    <div className={{`{capsule_id} ${{className}}`}}>
      {{children}}
    </div>
  );
}};

// Usage:
// <{component_name}>Content</{component_name}>
'''
        elif platform == "swift":
            example_code = f'''// {name} Component (SwiftUI)
// From HubLab: https://hublab.dev/capsules/{capsule_id}

import SwiftUI

struct {component_name}: View {{
    var body: some View {{
        VStack {{
            Text("{name}")
        }}
    }}
}}

// Usage:
// {component_name}()
'''
        elif platform == "kotlin":
            example_code = f'''// {name} Component (Jetpack Compose)
// From HubLab: https://hublab.dev/capsules/{capsule_id}

@Composable
fun {component_name}(
    modifier: Modifier = Modifier
) {{
    Column(modifier = modifier) {{
        Text("{name}")
    }}
}}

// Usage:
// {component_name}()
'''
        else:
            example_code = f"// Platform '{platform}' not supported. Use: react, swift, kotlin"

        return json.dumps({
            "capsule_id": capsule_id,
            "name": name,
            "platform": platform,
            "code": example_code,
            "full_code_available": code is not None,
            "docs_url": f"https://hublab.dev/capsules/{capsule_id}",
        }, indent=2)

    def hublab_stats(self) -> str:
        """Get catalog statistics."""
        capsules = self._load_capsules()
        categories = self._get_categories()

        # Count by platform
        platforms = {}
        for cap in capsules:
            plat = cap.get("platform", "react")
            platforms[plat] = platforms.get(plat, 0) + 1

        # Most common tags
        all_tags = {}
        for cap in capsules:
            for tag in cap.get("tags", []):
                all_tags[tag] = all_tags.get(tag, 0) + 1

        top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:20]

        return json.dumps({
            "total_capsules": len(capsules),
            "total_categories": len(categories),
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10],
            "platforms": platforms,
            "top_tags": top_tags,
            "source": "hublab.dev",
            "api_url": self.API_BASE,
            "local_path": self.HUBLAB_PATH,
        }, indent=2)

    def execute(self, **kwargs) -> str:
        """Direct skill execution."""
        if "query" in kwargs:
            return self.hublab_search(kwargs["query"])
        return self.hublab_stats()
