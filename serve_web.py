"""Serve the live ArenAI Grid viewer and provide an API to run matches."""
from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from agents import HeuristicAgent, RandomAgent
from game_engine import GameEngine
from replay import ReplayRecorder


AGENT_REGISTRY = {
    "random": RandomAgent,
    "heuristic": HeuristicAgent,
}

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"


def build_agent(agent_name: str, seed: Optional[int]) -> object:
    cls = AGENT_REGISTRY[agent_name]
    return cls(seed=seed)


def run_match(blue: str, red: str, seed: Optional[int]) -> dict:
    agent_blue = build_agent(blue, seed)
    agent_red = build_agent(red, None if seed is None else seed + 1)
    recorder = ReplayRecorder()
    engine = GameEngine(agent_blue, agent_red, seed=seed, fast_mode=True)
    winner_state = engine.play(recorder=recorder)
    return recorder.to_dict(winner_state.name)


class ArenAIRequestHandler(SimpleHTTPRequestHandler):
    """Serves static files from web/ and handles /api/run to generate a fresh match."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            return self._handle_run(parsed)
        return super().do_GET()

    def _handle_run(self, parsed):
        params = parse_qs(parsed.query)
        blue = params.get("blue", ["heuristic"])[0]
        red = params.get("red", ["random"])[0]
        seed_param = params.get("seed", [None])[0]
        try:
            seed = int(seed_param) if seed_param is not None else None
        except ValueError:
            return self._send_json({"error": "Invalid seed"}, status=400)

        if blue not in AGENT_REGISTRY or red not in AGENT_REGISTRY:
            return self._send_json({"error": f"Agents must be in {list(AGENT_REGISTRY.keys())}"}, status=400)

        replay = run_match(blue, red, seed)
        return self._send_json(replay)

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the live ArenAI Grid web viewer with /api/run.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the local web server")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Serving from {WEB_DIR} at http://localhost:{args.port}")
    print("Use /api/run?blue=heuristic&red=random&seed=123 to trigger a match, or click 'Run Match' in the UI.")

    with ThreadingHTTPServer(("", args.port), ArenAIRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Shutting down server.")
        finally:
            httpd.server_close()


if __name__ == "__main__":
    main()
