#!/usr/bin/env python3
"""
NotebookLM Headless Query CLI

Wrapper around notebooklm-py library for headless API access.
Used by the notebooklm-verifier agent via Bash.

Usage:
  notebooklm-query.py check                              Verify auth is valid
  notebooklm-query.py list [--json]                       List all notebooks
  notebooklm-query.py query -n NAME -q QUESTION [--json]  Query a notebook
  notebooklm-query.py sources -n NAME [--json]            List sources
  notebooklm-query.py harvest --cookies JSON               Store Chrome cookies

Exit codes: 0=success, 1=error, 2=auth failure (re-harvest needed)
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Auth failure exit code — agent uses this to detect expired tokens
EXIT_AUTH = 2


def _find_notebook(notebooks, name):
    """Find notebook by exact or partial name match (case-insensitive)."""
    name_lower = name.lower()
    # Exact match first
    for nb in notebooks:
        if nb.title.lower() == name_lower:
            return nb
    # Partial match
    matches = [nb for nb in notebooks if name_lower in nb.title.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        titles = [nb.title for nb in matches]
        print(
            json.dumps({"error": "ambiguous_name", "matches": titles}),
            file=sys.stderr,
        )
        return None
    return None


def _nb_to_dict(nb):
    """Convert Notebook to serializable dict."""
    return {
        "id": nb.id,
        "title": nb.title,
        "sources_count": nb.sources_count,
        "created_at": nb.created_at.isoformat() if nb.created_at else None,
    }


def _source_to_dict(src):
    """Convert Source to serializable dict."""
    return {
        "id": src.id,
        "title": src.title,
        "url": src.url,
        "status": src.status,
        "created_at": src.created_at.isoformat() if src.created_at else None,
    }


def _ask_result_to_dict(result, notebook_title=None):
    """Convert AskResult to serializable dict."""
    return {
        "answer": result.answer,
        "conversation_id": result.conversation_id,
        "turn_number": result.turn_number,
        "is_follow_up": result.is_follow_up,
        "notebook": notebook_title,
        "references": [
            {
                "source_id": ref.source_id,
                "citation_number": ref.citation_number,
                "cited_text": ref.cited_text,
            }
            for ref in (result.references or [])
        ],
    }


async def cmd_check():
    """Verify auth is valid by listing notebooks."""
    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        print(
            json.dumps(
                {
                    "status": "ok",
                    "notebooks_count": len(notebooks),
                    "message": f"Auth valid. {len(notebooks)} notebooks accessible.",
                }
            )
        )


async def cmd_list(as_json):
    """List all notebooks."""
    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()

    if as_json:
        print(json.dumps([_nb_to_dict(nb) for nb in notebooks], indent=2))
    else:
        for nb in notebooks:
            print(f"  {nb.title}  ({nb.sources_count} sources)  [{nb.id}]")


async def cmd_query(name, question, conv_id, as_json):
    """Query a notebook."""
    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        nb = _find_notebook(notebooks, name)
        if not nb:
            print(
                json.dumps(
                    {
                        "error": "notebook_not_found",
                        "name": name,
                        "available": [n.title for n in notebooks],
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(1)

        result = await client.chat.ask(
            notebook_id=nb.id,
            question=question,
            conversation_id=conv_id,
        )

    if as_json:
        print(json.dumps(_ask_result_to_dict(result, nb.title), indent=2))
    else:
        print(f"Notebook: {nb.title}")
        print(f"Turn: {result.turn_number}")
        print(f"Conversation ID: {result.conversation_id}")
        print(f"\n{result.answer}\n")
        if result.references:
            print("Citations:")
            for ref in result.references:
                text = (ref.cited_text or "")[:100]
                print(f"  [{ref.citation_number}] {text}...")


async def cmd_sources(name, as_json):
    """List sources in a notebook."""
    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        nb = _find_notebook(notebooks, name)
        if not nb:
            print(
                json.dumps(
                    {
                        "error": "notebook_not_found",
                        "name": name,
                        "available": [n.title for n in notebooks],
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(1)

        sources = await client.sources.list(nb.id)

    if as_json:
        print(json.dumps([_source_to_dict(s) for s in sources], indent=2))
    else:
        for src in sources:
            print(f"  {src.title or '(untitled)'}  [{src.id}]")


def cmd_harvest(cookies_json):
    """Convert Chrome cookies to Playwright storage_state.json format."""
    storage_dir = Path.home() / ".notebooklm"
    storage_dir.mkdir(exist_ok=True)
    storage_file = storage_dir / "storage_state.json"

    try:
        cookies = json.loads(cookies_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": "invalid_json", "detail": str(e)}), file=sys.stderr)
        sys.exit(1)

    # Handle different input formats
    if isinstance(cookies, dict):
        # Format: {"SID": "value", "HSID": "value", ...}
        cookie_list = []
        for name, value in cookies.items():
            cookie_list.append(
                {
                    "name": name,
                    "value": value,
                    "domain": ".google.com",
                    "path": "/",
                    "expires": -1,
                    "httpOnly": True,
                    "secure": name.startswith("__Secure"),
                    "sameSite": "None" if name.startswith("__Secure") else "Lax",
                }
            )
    elif isinstance(cookies, list):
        # Already in Playwright cookie format or Chrome export format
        cookie_list = cookies
    else:
        print(
            json.dumps({"error": "unexpected_format", "type": type(cookies).__name__}),
            file=sys.stderr,
        )
        sys.exit(1)

    # Write Playwright storage state format
    storage_state = {"cookies": cookie_list, "origins": []}
    storage_file.write_text(json.dumps(storage_state, indent=2))

    print(
        json.dumps(
            {
                "status": "ok",
                "path": str(storage_file),
                "cookies_count": len(cookie_list),
                "message": f"Saved {len(cookie_list)} cookies. Run 'check' to verify.",
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM Headless Query CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # check
    sub.add_parser("check", help="Verify auth is valid")

    # list
    p_list = sub.add_parser("list", help="List all notebooks")
    p_list.add_argument("--json", action="store_true", help="JSON output")

    # query
    p_query = sub.add_parser("query", help="Query a notebook")
    p_query.add_argument("-n", "--notebook-name", required=True, help="Notebook name")
    p_query.add_argument("-q", "--question", required=True, help="Question to ask")
    p_query.add_argument("--conv-id", help="Conversation ID for follow-ups")
    p_query.add_argument("--json", action="store_true", help="JSON output")

    # sources
    p_src = sub.add_parser("sources", help="List sources in a notebook")
    p_src.add_argument("-n", "--notebook-name", required=True, help="Notebook name")
    p_src.add_argument("--json", action="store_true", help="JSON output")

    # harvest
    p_harvest = sub.add_parser("harvest", help="Store Chrome cookies")
    p_harvest.add_argument(
        "--cookies", required=True, help="Cookie JSON (dict or list)"
    )

    args = parser.parse_args()

    try:
        if args.command == "check":
            asyncio.run(cmd_check())
        elif args.command == "list":
            asyncio.run(cmd_list(args.json))
        elif args.command == "query":
            asyncio.run(
                cmd_query(args.notebook_name, args.question, args.conv_id, args.json)
            )
        elif args.command == "sources":
            asyncio.run(cmd_sources(args.notebook_name, args.json))
        elif args.command == "harvest":
            cmd_harvest(args.cookies)
    except FileNotFoundError:
        print(
            json.dumps(
                {
                    "error": "no_auth",
                    "message": "No storage_state.json found. Run: notebooklm login",
                    "path": str(Path.home() / ".notebooklm" / "storage_state.json"),
                }
            ),
            file=sys.stderr,
        )
        sys.exit(EXIT_AUTH)
    except (ValueError, ImportError) as e:
        err_str = str(e).lower()
        if "cookie" in err_str or "auth" in err_str or "token" in err_str:
            print(
                json.dumps(
                    {
                        "error": "auth_failed",
                        "message": str(e),
                        "hint": "Run: notebooklm login (or harvest via Chrome)",
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(EXIT_AUTH)
        print(json.dumps({"error": "value_error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Check if it's an auth error from the library
        err_name = type(e).__name__
        if "Auth" in err_name or "401" in str(e) or "403" in str(e):
            print(
                json.dumps(
                    {
                        "error": "auth_expired",
                        "type": err_name,
                        "message": str(e),
                        "hint": "Run: notebooklm login",
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(EXIT_AUTH)
        print(
            json.dumps({"error": err_name, "message": str(e)}),
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
