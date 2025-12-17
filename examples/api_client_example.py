#!/usr/bin/env python3
"""
R CLI - REST API Client Example

Shows how to use R CLI as a server and connect from any client.
First, start the server: r serve --port 8765
"""

import requests

BASE_URL = "http://localhost:8765"


def chat_completion():
    """OpenAI-compatible chat completion."""
    response = requests.post(
        f"{BASE_URL}/v1/chat",
        json={
            "messages": [{"role": "user", "content": "What is Python?"}],
            "stream": False,
        },
    )
    print("Chat response:")
    print(response.json())


def chat_streaming():
    """Streaming chat completion."""
    response = requests.post(
        f"{BASE_URL}/v1/chat",
        json={
            "messages": [{"role": "user", "content": "Count from 1 to 5"}],
            "stream": True,
        },
        stream=True,
    )
    print("Streaming response:")
    for line in response.iter_lines():
        if line:
            print(line.decode())


def call_skill_directly():
    """Call a skill without going through the LLM."""
    response = requests.post(
        f"{BASE_URL}/v1/skills/call",
        json={
            "skill": "datetime",
            "tool": "now",
            "arguments": {"format": "%Y-%m-%d %H:%M:%S"},
        },
    )
    print("Direct skill call:")
    print(response.json())


def list_skills():
    """List all available skills."""
    response = requests.get(f"{BASE_URL}/v1/skills")
    skills = response.json()
    print(f"Available skills ({len(skills)}):")
    for skill in skills[:10]:  # First 10
        print(f"  - {skill['name']}: {skill['description'][:50]}...")


def generate_pdf():
    """Generate a PDF via API."""
    response = requests.post(
        f"{BASE_URL}/v1/skills/call",
        json={
            "skill": "pdf",
            "tool": "generate_pdf",
            "arguments": {
                "content": "# Hello World\n\nThis PDF was generated via the R CLI API.",
                "title": "API Generated PDF",
            },
        },
    )
    print("PDF generation:")
    print(response.json())


if __name__ == "__main__":
    print("R CLI API Examples")
    print("=" * 40)
    print("Make sure server is running: r serve --port 8765\n")

    try:
        list_skills()
        print()
        call_skill_directly()
        print()
        # Uncomment to test chat (requires LLM running):
        # chat_completion()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to R CLI server.")
        print("Start it with: r serve --port 8765")
