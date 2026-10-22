"""Launch graphical desktop assistant or use its headless development mode."""

from __future__ import annotations

import argparse

from .agent import Agent


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Desktop early prototype")
    parser.add_argument("--ask", help="Run one request without opening the GUI")
    parser.add_argument(
        "--provider", choices=("builtin", "local", "openai", "anthropic"),
        default="builtin", help="Inference backend for --ask (default: builtin)",
    )
    args = parser.parse_args()
    if args.ask is not None:
        result = Agent().ask(args.ask, args.provider)
        print(result.message)
        if result.pending:
            print("Action needs graphical approval; no change was applied.")
        return

    try:
        from .ui import AssistantApp
    except (ImportError, ValueError) as exc:
        parser.error(
            "GNOME graphical libraries are required to launch the UI. "
            f"Try --ask for headless diagnostics. Details: {exc}"
        )
    app = AssistantApp()
    raise SystemExit(app.run(None))


if __name__ == "__main__":
    main()
