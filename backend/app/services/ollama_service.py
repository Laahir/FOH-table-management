import httpx

from app.config import settings


def ask_ollama(prompt: str) -> str:
    """Call Ollama; return plain English fallback if unavailable."""
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            if text:
                return text
    except Exception:
        pass
    return ""


def seating_suggestion(party_size: int, tables: list[dict]) -> str:
    if not tables:
        return f"Sorry, we don't have any tables free right now for a party of {party_size}. I'd suggest asking the host to combine tables or wait a few minutes."

    table_lines = "\n".join(
        f"- Table {t['number']}: seats {t['capacity']}, status {t['status']}, section {t.get('section', 'main')}"
        for t in tables[:8]
    )
    prompt = (
        f"You are a friendly restaurant host. A party of {party_size} guests needs a table.\n"
        f"Available tables:\n{table_lines}\n\n"
        "Recommend the top 3 best options in plain conversational English. "
        "Explain briefly why each works. No JSON, no bullet codes, no technical jargon."
    )
    result = ask_ollama(prompt)
    if result:
        return result

    picks = sorted(tables, key=lambda t: abs(t["capacity"] - party_size))[:3]
    lines = [f"For a party of {party_size}, here are my top picks:"]
    for t in picks:
        lines.append(
            f"Table {t['number']} seats {t['capacity']} — "
            f"{'a snug fit' if t['capacity'] == party_size else 'comfortable with a little room'}."
        )
    return " ".join(lines)


def shift_report(summary_stats: dict) -> str:
    prompt = (
        "You are a restaurant manager writing an end-of-shift summary for staff.\n"
        f"Stats: {summary_stats}\n"
        "Write one short paragraph in plain English covering covers, busy periods, and anything worth noting. "
        "No JSON, no lists of raw numbers."
    )
    result = ask_ollama(prompt)
    if result:
        return result
    return (
        f"Tonight we served {summary_stats.get('total_sessions', 0)} parties across "
        f"{summary_stats.get('tables_used', 0)} tables. "
        f"{summary_stats.get('active_now', 0)} tables are still in service. "
        "Overall service ran smoothly — review the floor plan for any tables still in cleaning."
    )
