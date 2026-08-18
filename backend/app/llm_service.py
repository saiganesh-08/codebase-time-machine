"""
Turns raw commit history into a plain-English narrative of how a
function evolved. The LLM explains structured data -- it does not
invent the underlying facts (those come from git_analyzer + ast_analyzer).
"""
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def summarize_function_history(qualified_name: str, commit_messages: list[str], bugfix_count: int) -> str:
    if not commit_messages:
        return f"No recorded history found for `{qualified_name}` in the analyzed commit range."

    joined = "\n".join(f"- {m}" for m in commit_messages[:30])

    prompt = f"""You are summarizing the evolution of a function in a codebase for an engineer
who is about to modify it. Use only the commit messages given below as your source of truth.
Do not invent details that aren't implied by the messages.

Function: {qualified_name}
Number of bug-fix-flagged commits: {bugfix_count}

Commit messages (most recent first):
{joined}

Write a short (3-5 sentence) plain-English narrative describing how this function has evolved
and what an engineer should be careful about before changing it. Be concrete and grounded in
the commit messages, not generic advice."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    text_blocks = [b.text for b in response.content if b.type == "text"]
    return "\n".join(text_blocks).strip()
