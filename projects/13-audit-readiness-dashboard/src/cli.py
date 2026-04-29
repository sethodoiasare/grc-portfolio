"""CLI entry point for the Audit Readiness Dashboard."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Audit Readiness Dashboard — capstone GRC web dashboard"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8013,
        help="Port to listen on (default: 8013)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload",
    )

    args = parser.parse_args()

    import uvicorn

    print(f"\n  Audit Readiness Dashboard")
    print(f"  Open http://localhost:{args.port} in your browser\n")

    uvicorn.run(
        "src.api:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
