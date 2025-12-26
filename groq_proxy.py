#!/usr/bin/env python3
"""
Groq API Proxy for lm-eval compatibility.

Transforms lm-eval requests to Groq-compatible format and handles
reasoning model parameters (reasoning_format, reasoning_effort).

Usage:
    python groq_proxy.py [--port 8000] [--reasoning-hidden]

Then run lm-eval with:
    ./eval_api.sh local <model> http://localhost:8000/v1
"""

import argparse
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
from pathlib import Path

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value and key not in os.environ:
                        os.environ[key] = value


class GroqProxyHandler(BaseHTTPRequestHandler):
    reasoning_hidden = False
    reasoning_effort = "low"

    def do_POST(self):
        if not self.path.endswith("/chat/completions"):
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        # Transform messages to Groq-compatible format
        if "messages" in data:
            cleaned_messages = []
            for msg in data["messages"]:
                cleaned_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                # Only include name if present and valid
                if "name" in msg and msg["name"]:
                    cleaned_msg["name"] = msg["name"]
                cleaned_messages.append(cleaned_msg)
            data["messages"] = cleaned_messages

        # Add reasoning parameters for reasoning models
        if GroqProxyHandler.reasoning_hidden:
            data["reasoning_format"] = "hidden"
            data["reasoning_effort"] = GroqProxyHandler.reasoning_effort

        # Remove unsupported parameters
        data.pop("tokenized_requests", None)
        data.pop("extra_body", None)

        # Forward to Groq
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            self.send_error(500, "GROQ_API_KEY not set")
            return

        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "lm-eval-harness/1.0",
            "Accept": "application/json",
        }

        req = urllib.request.Request(
            GROQ_API_URL,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                response_body = response.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"Groq API error: {e.code} - {error_body}")
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error_body.encode("utf-8"))
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        print(f"[Groq Proxy] {args[0]}")


def main():
    # Load .env file first
    load_env()

    parser = argparse.ArgumentParser(description="Groq API Proxy for lm-eval")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reasoning-hidden", action="store_true",
                        help="Hide reasoning output (for models like gpt-oss-20b)")
    parser.add_argument("--reasoning-effort", choices=["low", "medium", "high"],
                        default="low", help="Reasoning effort level")
    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in environment or .env file")
        print("Set it with: export GROQ_API_KEY=gsk_...")
        print("Or add it to .env file")
        return

    GroqProxyHandler.reasoning_hidden = args.reasoning_hidden
    GroqProxyHandler.reasoning_effort = args.reasoning_effort

    server = HTTPServer(("0.0.0.0", args.port), GroqProxyHandler)
    print(f"Groq Proxy listening on port {args.port}")
    print(f"GROQ_API_KEY: {os.environ['GROQ_API_KEY'][:10]}...")
    print(f"Reasoning hidden: {args.reasoning_hidden}")
    if args.reasoning_hidden:
        print(f"Reasoning effort: {args.reasoning_effort}")
    print(f"\nUsage with lm-eval:")
    print(f"  ./eval_api.sh local <model> http://localhost:{args.port}/v1")
    print(f"\nExample:")
    print(f"  ./eval_api.sh local openai/gpt-oss-20b http://localhost:{args.port}/v1")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
