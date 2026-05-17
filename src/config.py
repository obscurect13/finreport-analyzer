import os
import sys

REQUIRED_ENV_VARS = {
    "ANTHROPIC_API_KEY":
    "Required to call the Claude API for report analysis.",
}

OPTIONAL_ENV_VARS = {
    "API_KEY":
    "If set, the FastAPI /api/* endpoints require X-API-Key header.",
    "RATE_LIMIT_PER_MINUTE":
    "Max API requests per IP per minute (default: 10).",
}


def validate_env() -> None:
    """
    Check that all required environment variables are set.
    Exits with a clear error message if any are missing.
    """
    missing = [
        (var, desc)
        for var, desc in REQUIRED_ENV_VARS.items()
        if not os.getenv(var)
    ]

    if missing:
        lines = ["", "❌ Missing required environment variables:", ""]
        for var, desc in missing:
            lines.append(f"  • {var}: {desc}")
        lines += [
            "",
            "  Create a .env file at the project root:",
            "",
        ]
        for var, _ in missing:
            lines.append(f"  {var}=your_value_here")
        lines.append("")
        print("\n".join(lines), file=sys.stderr)
        sys.exit(1)
