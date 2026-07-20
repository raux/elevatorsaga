#!/usr/bin/env python3
"""Python-first NiceGUI visualization for Python and Java Elevator Saga strategies."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from nicegui import ui

ROOT = Path(__file__).resolve().parent
PYTHON_PORT = ROOT / "ports" / "python"
JAVA_PORT = ROOT / "ports" / "java"
INDEX_HTML = ROOT / "index.html"
PROCESS_TIMEOUT = 45
SAMPLE_EVERY = 0.1
TIMER_INTERVAL = 0.05


def editor_template(template_id: str) -> str:
    html = INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(
        rf'<script type="text/plain" id="{re.escape(template_id)}">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Missing editor template: {template_id}")
    return match.group(1)


DEFAULT_CODE = {
    "python": editor_template("default-python-implementation"),
    "java": editor_template("default-java-implementation"),
}


def java_tools() -> tuple[str | None, str | None]:
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(Path(os.environ["JAVA_HOME"]) / "bin")
    candidates.extend(
        [Path("/opt/homebrew/opt/openjdk@11/bin"), Path("/usr/local/opt/openjdk@11/bin")]
    )
    for directory in candidates:
        if (directory / "java").is_file() and (directory / "javac").is_file():
            return str(directory / "java"), str(directory / "javac")
    return shutil.which("java"), shutil.which("javac")


JAVA, JAVAC = java_tools()


def run_process(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=PROCESS_TIMEOUT,
        check=False,
    )


def java_class_name(code: str) -> str:
    if re.search(r"^\s*package\s+", code, re.MULTILINE):
        raise ValueError("Package declarations are not supported in editor strategies.")
    match = re.search(r"\bpublic\s+class\s+([A-Za-z_$][\w$]*)", code)
    if not match:
        raise ValueError("Java code must contain a public strategy class.")
    return match.group(1)


def generate_python_trace(code: str, challenge: int) -> tuple[dict[str, Any], str]:
    with tempfile.TemporaryDirectory(prefix="elevatorsaga-nicegui-python-") as temp_dir:
        temp = Path(temp_dir)
        solution = temp / "user_solution.py"
        output = temp / "trace.json"
        solution.write_text(code, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(PYTHON_PORT)
        completed = run_process(
            [
                sys.executable,
                "-B",
                "-m",
                "elevatorsaga.trace",
                "--solution",
                str(solution),
                "--challenge",
                str(challenge),
                "--sample-every",
                str(SAMPLE_EVERY),
                "--output",
                str(output),
            ],
            PYTHON_PORT,
            env,
        )
        if not output.exists():
            raise RuntimeError(completed.stdout or "Python trace runner did not produce output.")
        return json.loads(output.read_text(encoding="utf-8")), completed.stdout


def generate_java_trace(code: str, challenge: int) -> tuple[dict[str, Any], str]:
    if not JAVA or not JAVAC:
        raise RuntimeError("A Java 11+ JDK is required for Java visualization.")
    class_name = java_class_name(code)
    with tempfile.TemporaryDirectory(prefix="elevatorsaga-nicegui-java-") as temp_dir:
        temp = Path(temp_dir)
        classes = temp / "classes"
        classes.mkdir()
        source = temp / f"{class_name}.java"
        output = temp / "trace.json"
        source.write_text(code, encoding="utf-8")

        core_sources = sorted((JAVA_PORT / "src" / "main" / "java" / "elevatorsaga").glob("*.java"))
        compilation = run_process(
            [JAVAC, "-encoding", "UTF-8", "-d", str(classes)]
            + [str(path) for path in core_sources]
            + [str(source)],
            JAVA_PORT,
        )
        if compilation.returncode != 0:
            raise RuntimeError("Java compilation failed:\n" + compilation.stdout)

        execution = run_process(
            [
                JAVA,
                "-cp",
                str(classes),
                "elevatorsaga.TraceMain",
                "--strategy",
                class_name,
                "--challenge",
                str(challenge),
                "--sample-every",
                str(SAMPLE_EVERY),
                "--output",
                str(output),
            ],
            JAVA_PORT,
        )
        process_output = compilation.stdout + execution.stdout
        if not output.exists():
            raise RuntimeError(process_output or "Java trace runner did not produce output.")
        return json.loads(output.read_text(encoding="utf-8")), process_output


def generate_trace(language: str, code: str, challenge: int) -> tuple[dict[str, Any], str]:
    if language == "python":
        return generate_python_trace(code, challenge)
    if language == "java":
        return generate_java_trace(code, challenge)
    raise ValueError(f"Unsupported language: {language}")


class ReplayController:
    """Owns one browser client's Python-driven replay state and elements."""

    def __init__(self) -> None:
        self.trace: dict[str, Any] | None = None
        self.frame_index = 0
        self.playing = False
        self.speed = 1.0
        self.accumulator = 0.0
        self.world_width = 420.0
        self.world_height = 200.0
        self.floor_count = 4
        self.scene_height = 420
        self.elevator_elements: list[dict[str, Any]] = []
        self.user_elements: dict[int, dict[str, Any]] = {}
        self.user_states: dict[int, str] = {}
        self.visible_users: set[int] = set()

        self.scene = None
        self.play_button = None
        self.progress = None
        self.time_label = None
        self.transported_label = None
        self.moves_label = None
        self.wait_label = None

    def load(self, trace: dict[str, Any]) -> None:
        if not trace.get("frames") or not trace.get("scene"):
            raise RuntimeError(trace.get("result", {}).get("error") or "The trace contains no frames.")
        self.trace = trace
        self.frame_index = 0
        self.playing = False
        self.accumulator = 0.0
        scene = trace["scene"]
        floor_count = int(scene["floorCount"])
        floor_height = float(scene["floorHeight"])
        capacities = scene["elevatorCapacities"]
        self.floor_count = floor_count
        self.world_height = max(floor_count * floor_height, 1.0)
        elevator_span = sum(20.0 + float(capacity) * 10.0 for capacity in capacities)
        self.world_width = max(350.0, 240.0 + elevator_span)
        self.scene_height = max(330, min(720, floor_count * 72))
        floor_pixels = self.scene_height / floor_count
        car_height = max(34.0, floor_pixels - 8.0)
        self.elevator_elements = []
        self.user_elements = {}
        self.user_states = {}
        self.visible_users = set()

        self.scene.clear()
        self.scene.style(replace=self.scene_style())
        first_frame = trace["frames"][0]
        with self.scene:
            for floor in range(floor_count):
                y = (floor_count - 1 - floor) * floor_height
                top = self.y_percent(y)
                with ui.element("div").classes("floor-band").style(
                    replace=f"top:{top:.3f}%;height:{100.0 / floor_count:.3f}%;"
                ):
                    ui.label(str(floor)).classes("floor-label")
                    ui.element("div").classes("floor-call-panel").tooltip(f"Floor {floor}")

            for index, (capacity, initial) in enumerate(zip(capacities, first_frame["elevators"])):
                car_width = max(54.0, min(94.0, 28.0 + float(capacity) * 10.0))
                left = self.x_percent(float(initial["x"]))
                ui.element("div").classes("elevator-shaft").style(
                    replace=f"left:{left:.3f}%;width:{car_width:.1f}px;"
                )
                with ui.element("div").classes("elevator-car is-idle").style(
                    replace=(
                        f"left:{left:.3f}%;top:{self.y_percent(float(initial['y'])):.3f}%;"
                        f"width:{car_width:.1f}px;height:{car_height:.1f}px;"
                    )
                ) as elevator:
                    with ui.element("div").classes("elevator-display"):
                        up_indicator = ui.label("▲").classes("direction-light")
                        floor_indicator = ui.label(str(initial.get("floor", 0))).classes("car-floor")
                        down_indicator = ui.label("▼").classes("direction-light")
                    ui.element("div").classes("elevator-cab")
                    ui.element("div").classes("elevator-door door-left")
                    ui.element("div").classes("elevator-door door-right")
                    with ui.element("div").classes("elevator-load-track"):
                        load_indicator = ui.element("div").classes("elevator-load")
                elevator.tooltip(f"Elevator {index + 1}, capacity {capacity}")
                self.elevator_elements.append(
                    {
                        "root": elevator,
                        "floor": floor_indicator,
                        "up": up_indicator,
                        "down": down_indicator,
                        "load": load_indicator,
                    }
                )

        self.progress.props(f"max={max(0, len(trace['frames']) - 1)}")
        self.progress.set_value(0)
        self.play_button.set_text("Play")
        self.render_frame(0)

    def x_percent(self, x: float) -> float:
        return max(5.0, min(96.0, 4.0 + x / self.world_width * 92.0))

    def y_percent(self, y: float) -> float:
        return max(0.0, min(100.0, y / self.world_height * 100.0))

    def scene_style(self) -> str:
        sample_every = SAMPLE_EVERY
        if self.trace:
            sample_every = float(self.trace["scene"].get("sampleEvery", SAMPLE_EVERY))
        duration_ms = max(45.0, min(180.0, sample_every / max(self.speed, 0.1) * 1000.0))
        return f"height:{self.scene_height}px;--motion-duration:{duration_ms:.0f}ms;"

    def set_speed(self, speed: float) -> None:
        self.speed = speed
        if self.scene:
            self.scene.style(replace=self.scene_style())

    def elevator_style(self, elevator: dict[str, Any]) -> str:
        return (
            f"left:{self.x_percent(float(elevator['x'])):.3f}%;"
            f"top:{self.y_percent(float(elevator['y'])):.3f}%;"
        )

    def user_style(self, user: dict[str, Any]) -> str:
        color = {"female": "#ff70a6", "child": "#ffb347"}.get(user.get("type"), "#5bb8ff")
        return (
            f"left:{self.x_percent(float(user['x'])):.3f}%;"
            f"top:{self.y_percent(float(user['y'])):.3f}%;"
            f"--person-color:{color};"
        )

    def render_frame(self, index: int) -> None:
        if not self.trace:
            return
        frames = self.trace["frames"]
        self.frame_index = max(0, min(index, len(frames) - 1))
        frame = frames[self.frame_index]

        for elevator_data, parts in zip(frame["elevators"], self.elevator_elements):
            elevator = parts["root"]
            elevator.style(replace=self.elevator_style(elevator_data))
            moving = bool(elevator_data.get("moving", False))
            elevator.classes(
                add="is-moving" if moving else "is-idle",
                remove="is-idle" if moving else "is-moving",
            )
            parts["floor"].set_text(str(elevator_data.get("floor", 0)))
            parts["up"].style(
                replace="color:#52f59b;opacity:1;" if elevator_data.get("up") else "opacity:.16;"
            )
            parts["down"].style(
                replace="color:#52f59b;opacity:1;" if elevator_data.get("down") else "opacity:.16;"
            )
            load = max(0.0, min(1.0, float(elevator_data.get("load", 0.0))))
            load_color = "#ff5d73" if load > 0.85 else "#52f59b"
            parts["load"].style(replace=f"width:{load * 100:.1f}%;background:{load_color};")

        current_users = set()
        for user in frame["users"]:
            user_id = int(user["id"])
            current_users.add(user_id)
            state = "leaving" if user.get("done") else "riding" if user.get("riding") else "waiting"
            if user_id not in self.user_elements:
                direction = "↑" if int(user["to"]) > int(user["from"]) else "↓"
                with self.scene:
                    with ui.element("div").classes(f"passenger is-{state}") as element:
                        ui.element("div").classes("passenger-head")
                        ui.element("div").classes("passenger-body")
                        ui.label(f"{direction}{user['to']}").classes("passenger-destination")
                    element.tooltip(f"Passenger: floor {user['from']} → {user['to']}")
                self.user_elements[user_id] = {"root": element}
                self.user_states[user_id] = state
            parts = self.user_elements[user_id]
            element = parts["root"]
            if self.user_states[user_id] != state:
                element.classes(
                    add=f"is-{state}",
                    remove="is-waiting is-riding is-leaving",
                )
                self.user_states[user_id] = state
            element.style(replace=self.user_style(user))
            if user_id not in self.visible_users:
                element.set_visibility(True)

        for user_id in self.visible_users - current_users:
            self.user_elements[user_id]["root"].set_visibility(False)
        self.visible_users = current_users

        stats = frame["stats"]
        self.time_label.set_text(f"{float(frame['time']):.1f}s")
        self.transported_label.set_text(str(stats["transported"]))
        self.moves_label.set_text(str(stats["moves"]))
        self.wait_label.set_text(f"{float(stats['maxWaitTime']):.1f}s")
        self.progress.set_value(self.frame_index)

        if self.frame_index >= len(frames) - 1:
            self.playing = False
            self.play_button.set_text("Replay")

    def toggle(self) -> None:
        if not self.trace:
            ui.notify("Run a Python or Java strategy first.", type="warning")
            return
        if self.frame_index >= len(self.trace["frames"]) - 1:
            self.render_frame(0)
        self.playing = not self.playing
        self.play_button.set_text("Pause" if self.playing else "Play")

    def seek(self, value: float | None) -> None:
        if self.trace and value is not None:
            self.render_frame(int(value))

    def tick(self) -> None:
        if not self.playing or not self.trace:
            return
        sample_every = float(self.trace["scene"].get("sampleEvery", SAMPLE_EVERY))
        self.accumulator += TIMER_INTERVAL * self.speed
        advance = 0
        while self.accumulator + 1e-9 >= sample_every:
            self.accumulator -= sample_every
            advance += 1
        if advance:
            self.render_frame(self.frame_index + advance)


ui.add_css(
    """
    body { background: #edf2f7; color: #203040; }
    .app-shell { width: min(1500px, 96vw); margin: 0 auto; }
    .control-card, .editor-card, .visual-card { background: white; border-radius: 12px; box-shadow: 0 5px 20px rgba(25,45,70,.10); }
    .code-editor textarea { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important; font-size: 13px; line-height: 1.35; min-height: 520px !important; }
    .elevator-scene {
        position: relative; isolation: isolate; width: 100%; min-height: 330px; overflow: hidden;
        border: 4px solid #101a2a; border-radius: 12px;
        background: radial-gradient(circle at 22% 12%, rgba(67,116,164,.22), transparent 30%),
                    linear-gradient(135deg, #14263c 0%, #1c344d 54%, #102236 100%);
        box-shadow: inset 0 0 45px rgba(0,0,0,.34);
    }
    .floor-band {
        position: absolute; left: 0; right: 0; z-index: 0;
        border-bottom: 2px solid rgba(211,228,244,.45);
        background: linear-gradient(180deg, rgba(255,255,255,.018), rgba(255,255,255,.065));
    }
    .floor-band::after {
        content: ''; position: absolute; left: 74px; right: 0; bottom: 0; height: 7px;
        background: linear-gradient(180deg, #40576c, #26394b); box-shadow: 0 -1px rgba(255,255,255,.16);
    }
    .floor-label {
        position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
        width: 42px; color: rgba(225,239,252,.70); font-size: 24px; font-weight: 800;
        text-align: center; font-variant-numeric: tabular-nums;
    }
    .floor-call-panel {
        position: absolute; left: 58px; top: 50%; width: 9px; height: 24px;
        transform: translateY(-50%); border: 1px solid #8095a8; border-radius: 5px;
        background: radial-gradient(circle at 50% 30%, #6af0a4 0 2px, #23394b 3px);
        box-shadow: 0 2px 5px rgba(0,0,0,.35);
    }
    .elevator-shaft {
        position: absolute; top: 0; bottom: 0; z-index: 1;
        border-left: 2px solid rgba(11,20,30,.74); border-right: 2px solid rgba(11,20,30,.74);
        background: repeating-linear-gradient(90deg, rgba(0,0,0,.20) 0 2px, rgba(255,255,255,.018) 2px 12px);
        transform: translateX(-2px);
    }
    .elevator-car {
        position: absolute; z-index: 5; overflow: visible; box-sizing: border-box;
        border: 3px solid #efc866; border-radius: 7px 7px 3px 3px;
        background: linear-gradient(145deg, #466781, #243d55); color: white;
        box-shadow: 0 5px 12px rgba(0,0,0,.48), inset 0 0 0 1px rgba(255,255,255,.12);
        transition: left var(--motion-duration) linear, top var(--motion-duration) linear, box-shadow .18s ease;
        will-change: left, top;
    }
    .elevator-car.is-moving { box-shadow: 0 9px 18px rgba(0,0,0,.55), 0 0 13px rgba(239,200,102,.22); }
    .elevator-display {
        position: absolute; top: 3px; left: 50%; z-index: 9; transform: translateX(-50%);
        display: flex; align-items: center; justify-content: center; gap: 4px;
        min-width: 42px; height: 15px; padding: 0 5px; border-radius: 3px;
        background: #111c25; box-shadow: inset 0 0 4px #000;
    }
    .elevator-display .q-label { line-height: 1; }
    .direction-light { color: #52f59b; font-size: 7px; transition: opacity .15s ease; }
    .car-floor { min-width: 12px; color: #f6d97e; font: 700 10px/1 ui-monospace, monospace; text-align: center; }
    .elevator-cab { position: absolute; z-index: 1; left: 5px; right: 5px; top: 21px; bottom: 6px; background: linear-gradient(#abc1d0, #6f899d); border: 1px solid #d7e4ec; }
    .elevator-door {
        position: absolute; z-index: 4; top: 20px; bottom: 5px; width: calc(50% - 5px);
        background: linear-gradient(90deg, #839aaa, #c1d0d9 48%, #738b9c);
        border: 1px solid rgba(34,53,67,.72); transition: transform .22s cubic-bezier(.2,.8,.2,1);
    }
    .door-left { left: 5px; transform-origin: left center; }
    .door-right { right: 5px; transform-origin: right center; }
    .elevator-car.is-idle .door-left { transform: scaleX(.18); }
    .elevator-car.is-idle .door-right { transform: scaleX(.18); }
    .elevator-load-track { position: absolute; left: 5px; right: 5px; bottom: -7px; height: 3px; overflow: hidden; border-radius: 3px; background: rgba(5,12,18,.68); }
    .elevator-load { height: 100%; width: 0; border-radius: 3px; background: #52f59b; transition: width .18s ease, background .18s ease; }
    .passenger {
        position: absolute; z-index: 8; width: 18px; height: 29px; pointer-events: auto;
        transform: translateX(-50%); transform-origin: center bottom;
        transition: left var(--motion-duration) linear, top var(--motion-duration) linear, opacity .28s ease, filter .28s ease;
        will-change: left, top; filter: drop-shadow(0 2px 2px rgba(0,0,0,.46));
    }
    .passenger-head {
        position: absolute; left: 5px; top: 0; width: 9px; height: 9px; border-radius: 50%;
        background: #ffd3b6; border: 1px solid rgba(32,37,45,.62); z-index: 2;
    }
    .passenger-body {
        position: absolute; left: 3px; top: 8px; width: 13px; height: 14px; border-radius: 6px 6px 3px 3px;
        background: var(--person-color); border: 1px solid rgba(255,255,255,.72);
        box-shadow: inset 0 -3px rgba(0,0,0,.12);
    }
    .passenger-body::before, .passenger-body::after {
        content: ''; position: absolute; top: 12px; width: 4px; height: 9px;
        border-radius: 0 0 3px 3px; background: var(--person-color); border-bottom: 1px solid rgba(255,255,255,.65);
    }
    .passenger-body::before { left: 1px; }
    .passenger-body::after { right: 1px; }
    .passenger-destination {
        position: absolute; left: 15px; top: -7px; min-width: 24px; padding: 1px 4px;
        border-radius: 8px; background: rgba(8,19,29,.88); border: 1px solid rgba(255,255,255,.38);
        color: #f5f9fc; font: 700 9px/13px ui-monospace, monospace; text-align: center;
        opacity: .92; transition: opacity .18s ease;
    }
    .passenger.is-riding { z-index: 7; }
    .passenger.is-riding .passenger-destination { opacity: 0; }
    .passenger.is-riding .passenger-body { filter: saturate(.82); }
    .passenger.is-waiting .passenger-body { animation: passenger-wait 1.5s ease-in-out infinite; }
    .passenger.is-leaving { opacity: .34; filter: grayscale(.45) drop-shadow(0 2px 2px rgba(0,0,0,.3)); }
    .passenger.is-leaving .passenger-destination { opacity: 0; }
    @keyframes passenger-wait { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-2px); } }
    @media (prefers-reduced-motion: reduce) {
        .elevator-car, .passenger, .elevator-door, .elevator-load { transition-duration: 1ms !important; }
        .passenger.is-waiting .passenger-body { animation: none; }
    }
    .metric { min-width: 105px; padding: 10px 14px; border-radius: 8px; background: #f4f7fa; text-align: center; }
    .metric-title { color: #60758a; font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { font-size: 20px; font-weight: 700; color: #17324d; }
    """,
    shared=True,
)


@ui.page("/")
def index_page() -> None:
    replay = ReplayController()
    saved_code = dict(DEFAULT_CODE)
    current_language = {"value": "python"}

    ui.page_title("Elevator Saga — Python NiceGUI")
    with ui.column().classes("app-shell gap-4 py-4"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("Elevator Saga").classes("text-3xl font-bold")
                ui.label("Python-driven visualization for Python and Java strategies").classes("text-sm text-slate-500")
            ui.badge("NiceGUI · Python UI", color="primary")

        with ui.card().classes("control-card w-full p-4"):
            with ui.row().classes("w-full items-end gap-4"):
                language_select = ui.select(
                    {"python": "Python", "java": "Java"},
                    value="python",
                    label="Strategy language",
                ).classes("w-48")
                challenge_select = ui.select(
                    {number: f"Challenge {number}" for number in range(1, 19)},
                    value=1,
                    label="Challenge",
                ).classes("w-48")
                run_button = ui.button("Run and visualize", icon="play_arrow")
                status_label = ui.label("Ready — Python is selected by default.").classes("text-sm text-slate-600")
            ui.label(
                "Strategies execute locally with your user permissions. Only run code you trust. "
                "The simulation is recorded first and then replayed in this Python-controlled UI."
            ).classes("text-xs text-amber-800 mt-2")

        with ui.row().classes("w-full items-stretch gap-4 flex-wrap lg:flex-nowrap"):
            with ui.card().classes("editor-card p-3 w-full lg:w-5/12"):
                ui.label("Strategy code").classes("font-semibold")
                editor = ui.textarea(value=saved_code["python"]).classes("code-editor w-full").props("outlined")
            with ui.card().classes("visual-card p-3 w-full lg:w-7/12"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Recorded simulation").classes("font-semibold")
                    with ui.row().classes("items-center gap-2"):
                        replay.play_button = ui.button("Play", icon="smart_display", on_click=replay.toggle).props("outline")
                        speed_select = ui.select(
                            {0.5: "0.5×", 1.0: "1×", 2.0: "2×", 4.0: "4×", 8.0: "8×"},
                            value=1.0,
                            label="Replay speed",
                            on_change=lambda event: replay.set_speed(float(event.value)),
                        ).classes("w-28")
                replay.scene = ui.element("div").classes("elevator-scene mt-2")
                with ui.row().classes("w-full gap-2 mt-3"):
                    def metric(title: str):
                        with ui.column().classes("metric gap-0"):
                            ui.label(title).classes("metric-title")
                            return ui.label("0").classes("metric-value")
                    replay.time_label = metric("Time")
                    replay.transported_label = metric("Transported")
                    replay.moves_label = metric("Moves")
                    replay.wait_label = metric("Max wait")
                replay.progress = ui.slider(min=0, max=1, value=0, on_change=lambda event: replay.seek(event.value)).classes("w-full")

        with ui.expansion("Runtime output", icon="terminal").classes("w-full bg-white rounded-lg"):
            output_log = ui.label("No strategy has been run yet.").classes("font-mono whitespace-pre-wrap text-xs p-3")

    def change_language(event) -> None:
        previous = current_language["value"]
        saved_code[previous] = editor.value or ""
        current_language["value"] = event.value
        editor.set_value(saved_code[event.value])
        status_label.set_text(f"{event.value.title()} selected.")

    language_select.on_value_change(change_language)

    async def run_selected_strategy() -> None:
        language = current_language["value"]
        code = editor.value or ""
        challenge = int(challenge_select.value)
        saved_code[language] = code
        replay.playing = False
        replay.play_button.set_text("Play")
        run_button.disable()
        status_label.set_text(f"Running {language.title()} challenge {challenge}…")
        output_log.set_text("Compiling/running strategy and recording simulation frames…")
        try:
            trace, process_output = await asyncio.to_thread(generate_trace, language, code, challenge)
            replay.load(trace)
            result = trace["result"]
            outcome = "passed" if result.get("passed") else "failed"
            status = (
                f"Challenge {outcome}: {result.get('transported', 0)} transported, "
                f"{result.get('moves', 0)} moves, {float(result.get('maxWaitTime', 0)):.1f}s max wait."
            )
            if result.get("error"):
                status += f" Error: {result['error']}"
            status_label.set_text(status)
            output_log.set_text(process_output or "Trace recorded successfully.")
            replay.playing = True
            replay.play_button.set_text("Pause")
        except subprocess.TimeoutExpired:
            status_label.set_text(f"{language.title()} execution exceeded {PROCESS_TIMEOUT} seconds.")
            output_log.set_text("Execution timed out.")
            ui.notify("Strategy execution timed out.", type="negative")
        except Exception as exception:
            status_label.set_text(f"Unable to run {language.title()} strategy.")
            output_log.set_text(str(exception))
            ui.notify(str(exception), type="negative", multi_line=True)
        finally:
            run_button.enable()

    run_button.on_click(run_selected_strategy)
    ui.timer(TIMER_INTERVAL, replay.tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Python NiceGUI Elevator Saga visualizer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    ui.run(
        host=args.host,
        port=args.port,
        title="Elevator Saga — Python NiceGUI",
        favicon="🏢",
        reload=False,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
