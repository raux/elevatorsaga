#!/usr/bin/env python3
"""Serve Elevator Saga and execute Python/Java strategies locally.

This server intentionally binds to loopback because submitted strategies are
arbitrary programs with the same OS permissions as the server process.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PYTHON_PORT = ROOT / "ports" / "python"
JAVA_PORT = ROOT / "ports" / "java"
MAX_REQUEST_BYTES = 250_000
MAX_OUTPUT_CHARS = 60_000
RUN_TIMEOUT_SECONDS = 30
COMPILE_TIMEOUT_SECONDS = 30
FINAL_RE = re.compile(
    r"Final:\s*([0-9.]+)s elapsed,\s*(\d+) transported,\s*(\d+) moves,\s*max wait ([0-9.]+)s"
)


def _working_java_tools() -> tuple[str | None, str | None]:
    """Return a matching java/javac pair, preferring Homebrew OpenJDK 11."""
    candidate_dirs = []
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate_dirs.append(Path(java_home) / "bin")
    candidate_dirs.extend(
        [
            Path("/opt/homebrew/opt/openjdk@11/bin"),
            Path("/usr/local/opt/openjdk@11/bin"),
        ]
    )

    for directory in candidate_dirs:
        java = directory / "java"
        javac = directory / "javac"
        if java.is_file() and javac.is_file():
            return str(java), str(javac)

    java = shutil.which("java")
    javac = shutil.which("javac")
    if java and javac:
        try:
            subprocess.run(
                [java, "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=True,
            )
            return java, javac
        except (OSError, subprocess.SubprocessError):
            pass
    return None, None


JAVA, JAVAC = _working_java_tools()


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def _trim_output(output: str) -> str:
    if len(output) <= MAX_OUTPUT_CHARS:
        return output
    return output[:MAX_OUTPUT_CHARS] + "\n… output truncated …"


def _simulation_response(language: str, completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    output = _trim_output(completed.stdout)
    match = FINAL_RE.search(output)
    if not match:
        return {
            "ok": False,
            "language": language,
            "passed": False,
            "error": "The strategy did not complete normally.",
            "output": output,
        }

    passed = completed.returncode == 0 and "CHALLENGE PASSED" in output
    return {
        "ok": True,
        "language": language,
        "passed": passed,
        "stats": {
            "elapsedTime": float(match.group(1)),
            "transported": int(match.group(2)),
            "moves": int(match.group(3)),
            "maxWaitTime": float(match.group(4)),
        },
        "output": output,
    }


def run_python_strategy(code: str, challenge: int) -> dict[str, Any]:
    if not 1 <= challenge <= 19:
        return {"ok": False, "error": "Python supports challenge numbers 1–19."}

    with tempfile.TemporaryDirectory(prefix="elevatorsaga-python-") as temp_dir:
        solution = Path(temp_dir) / "user_solution.py"
        solution.write_text(code, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(PYTHON_PORT)
        try:
            completed = _run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "elevatorsaga",
                    "--challenge",
                    str(challenge),
                    "--solution",
                    str(solution),
                ],
                cwd=PYTHON_PORT,
                timeout=RUN_TIMEOUT_SECONDS,
                env=env,
            )
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or "") + (error.stderr or "")
            return {
                "ok": False,
                "language": "python",
                "passed": False,
                "error": f"Python execution exceeded {RUN_TIMEOUT_SECONDS} seconds.",
                "output": _trim_output(output),
            }
        return _simulation_response("python", completed)


def _java_class_name(code: str) -> tuple[str | None, str | None]:
    if re.search(r"^\s*package\s+", code, re.MULTILINE):
        return None, "Package declarations are not supported in browser strategies."
    match = re.search(r"\bpublic\s+class\s+([A-Za-z_$][\w$]*)", code)
    if not match:
        return None, "Java code must contain a public strategy class."
    return match.group(1), None


def run_java_strategy(code: str, challenge: int) -> dict[str, Any]:
    if not JAVA or not JAVAC:
        return {
            "ok": False,
            "language": "java",
            "passed": False,
            "error": "A Java 11+ JDK was not found by the local server.",
            "output": "",
        }
    if not 1 <= challenge <= 18:
        return {"ok": False, "error": "Java supports challenge numbers 1–18."}

    class_name, class_error = _java_class_name(code)
    if class_error:
        return {"ok": False, "language": "java", "passed": False, "error": class_error, "output": ""}

    with tempfile.TemporaryDirectory(prefix="elevatorsaga-java-") as temp_dir:
        temp = Path(temp_dir)
        classes = temp / "classes"
        classes.mkdir()
        strategy_source = temp / f"{class_name}.java"
        strategy_source.write_text(code, encoding="utf-8")
        core_sources = sorted((JAVA_PORT / "src" / "main" / "java" / "elevatorsaga").glob("*.java"))
        compile_command = [JAVAC, "-encoding", "UTF-8", "-d", str(classes)]
        compile_command.extend(str(path) for path in core_sources)
        compile_command.append(str(strategy_source))

        try:
            compilation = _run_command(
                compile_command,
                cwd=JAVA_PORT,
                timeout=COMPILE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or "") + (error.stderr or "")
            return {
                "ok": False,
                "language": "java",
                "passed": False,
                "error": f"Java compilation exceeded {COMPILE_TIMEOUT_SECONDS} seconds.",
                "output": _trim_output(output),
            }

        if compilation.returncode != 0:
            return {
                "ok": False,
                "language": "java",
                "passed": False,
                "error": "Java compilation failed.",
                "output": _trim_output(compilation.stdout),
            }

        try:
            completed = _run_command(
                [
                    JAVA,
                    "-cp",
                    str(classes),
                    "elevatorsaga.Main",
                    "--strategy",
                    class_name,
                    "--challenge",
                    str(challenge),
                ],
                cwd=JAVA_PORT,
                timeout=RUN_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as error:
            output = (error.stdout or "") + (error.stderr or "")
            return {
                "ok": False,
                "language": "java",
                "passed": False,
                "error": f"Java execution exceeded {RUN_TIMEOUT_SECONDS} seconds.",
                "output": _trim_output(output),
            }
        return _simulation_response("java", completed)


def execute_strategy(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    language = payload.get("language")
    code = payload.get("code")
    challenge = payload.get("challenge")

    if language not in {"python", "java"}:
        return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Language must be python or java."}
    if not isinstance(code, str) or not code.strip():
        return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Strategy code is required."}
    if not isinstance(challenge, int):
        return HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Challenge must be an integer."}

    if language == "python":
        return HTTPStatus.OK, run_python_strategy(code, challenge)
    return HTTPStatus.OK, run_java_strategy(code, challenge)


class ElevatorSagaHandler(SimpleHTTPRequestHandler):
    server_version = "ElevatorSagaLocal/1.0"

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "python": True,
                    "java": bool(JAVA and JAVAC),
                    "javaRuntime": JAVA,
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/api/run":
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found."})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "Invalid content length."})
            return
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"ok": False, "error": "Request body is empty or too large."},
            )
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object.")
            status, result = execute_strategy(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(error)})
            return
        except Exception as error:  # Keep the local API responsive and report unexpected failures.
            self.log_error("strategy execution failed: %s", error)
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": f"Local execution failed: {error}"},
            )
            return
        self._send_json(status, result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the multi-language Elevator Saga UI locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback only)")
    parser.add_argument("--port", type=int, default=8001, help="HTTP port (default: 8001)")
    args = parser.parse_args()

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print(
            "Warning: submitted Python and Java code executes with your user permissions. "
            "Binding beyond loopback is unsafe.",
            file=sys.stderr,
        )

    handler = partial(ElevatorSagaHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Elevator Saga local server: http://{args.host}:{args.port}/index.html")
    print(f"Python runtime: {sys.executable}")
    print(f"Java runtime: {JAVA or 'not found'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
