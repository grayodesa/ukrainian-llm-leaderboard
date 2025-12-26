#!/usr/bin/env python3
"""
Proxy server that converts reasoning model responses to standard format.
Extracts content from reasoning_content field for lm-eval compatibility.

Usage:
    python reasoning_proxy.py --port 8080 --target https://api.tokenfactory.nebius.com/v1

Then use: OPENAI_BASE_URL=http://localhost:8080/v1 ./eval_api.sh openai model-name
"""

import argparse
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import ssl


class ReasoningProxyHandler(BaseHTTPRequestHandler):
    target_base_url = None
    api_key = None

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Forward request to target API
        target_url = f"{self.target_base_url}{self.path}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': self.headers.get('Authorization', f'Bearer {self.api_key}')
        }

        try:
            req = urllib.request.Request(
                target_url,
                data=body,
                headers=headers,
                method='POST'
            )

            # Disable SSL verification for simplicity (not recommended for production)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, context=ctx) as response:
                response_body = response.read()
                response_data = json.loads(response_body)

                # Convert reasoning_content to content
                if 'choices' in response_data:
                    for choice in response_data['choices']:
                        message = choice.get('message', {})

                        # If content is null/empty but reasoning_content exists
                        if not message.get('content') and message.get('reasoning_content'):
                            # Extract final answer from reasoning or use full reasoning
                            reasoning = message['reasoning_content']

                            # Try to find final answer after </think> or similar markers
                            for marker in ['</think>', '</reasoning>', '**Answer:**', 'Answer:']:
                                if marker in reasoning:
                                    parts = reasoning.split(marker, 1)
                                    if len(parts) > 1 and parts[1].strip():
                                        message['content'] = parts[1].strip()
                                        break

                            # If no marker found, use the last part of reasoning
                            if not message.get('content'):
                                # Take last paragraph or sentence as answer
                                lines = [l.strip() for l in reasoning.strip().split('\n') if l.strip()]
                                if lines:
                                    message['content'] = lines[-1]
                                else:
                                    message['content'] = reasoning

                modified_body = json.dumps(response_data).encode()

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', len(modified_body))
                self.end_headers()
                self.wfile.write(modified_body)

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, format, *args):
        print(f"[Proxy] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description='Reasoning model proxy for lm-eval')
    parser.add_argument('--port', type=int, default=8080, help='Proxy port')
    parser.add_argument('--target', required=True, help='Target API base URL')
    parser.add_argument('--api-key', help='API key (or use OPENAI_API_KEY env var)')
    args = parser.parse_args()

    ReasoningProxyHandler.target_base_url = args.target.rstrip('/')
    ReasoningProxyHandler.api_key = args.api_key or os.environ.get('OPENAI_API_KEY', '')

    server = HTTPServer(('localhost', args.port), ReasoningProxyHandler)
    print(f"Reasoning proxy running on http://localhost:{args.port}")
    print(f"Target API: {ReasoningProxyHandler.target_base_url}")
    print(f"Use: OPENAI_BASE_URL=http://localhost:{args.port}/v1 ./eval_api.sh openai your-model")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down proxy...")
        server.shutdown()


if __name__ == '__main__':
    main()
