#!/usr/bin/env python3
"""
R CLI - RAG (Retrieval Augmented Generation) Example

Shows how to build and query a knowledge base from your documents.
Requires: pip install r-cli-ai[rag]
"""

from r_cli.core.agent import Agent


def main():
    agent = Agent()
    agent.load_skills()

    # 1. Index documents
    print("Indexing documents...")
    result = agent.run_skill_directly(
        "rag",
        action="add",
        path="./docs",  # Your documents folder
        collection="my_knowledge",
    )
    print(f"Indexed: {result}")

    # 2. Query the knowledge base
    print("\nQuerying knowledge base...")
    result = agent.run_skill_directly(
        "rag",
        action="query",
        query="How does authentication work?",
        collection="my_knowledge",
        top_k=3,
    )
    print(f"Results:\n{result}")

    # 3. List collections
    print("\nAvailable collections:")
    result = agent.run_skill_directly(
        "rag",
        action="list",
    )
    print(result)


if __name__ == "__main__":
    main()
