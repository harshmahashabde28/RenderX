"""Run the real RenderX application loop with deterministic headless input."""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
from math import isfinite
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback


def _arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--dt", type=float, default=1 / 60)
    parser.add_argument("--initial", default="1920x1080",
                        help="virtual desktop size, WIDTHxHEIGHT")
    parser.add_argument("--events", type=Path,
                        help="JSON schedule: [{frame, events: [{type, ...}]}]")
    parser.add_argument("--capture", default="1",
                        help="comma-separated frame numbers, or 'destinations'")
    parser.add_argument("--scenario", choices=("app", "idle", "orbit", "largest"),
                        default="app")
    parser.add_argument("--skip-landing", action="store_true",
                        help="start the app in Explore")
    parser.add_argument("--mode", choices=("explore", "challenge", "maze", "shooter"),
                        help="start a specific destination directly")
    parser.add_argument("--fuzz-seed", type=int)
    parser.add_argument("--output", type=Path, default=Path("tools/qa/output/latest"))
    parser.add_argument("--expect-destination")
    parser.add_argument("--expect-help-closed", action="store_true")
    parser.add_argument("--expect-no-drag", action="store_true")
    parser.add_argument("--expect-hover-clear", action="store_true")
    parser.add_argument("--expect-pressed-clear", action="store_true")
    parser.add_argument("--expect-cursor", action="store_true")
    parser.add_argument("--expect-shape")
    parser.add_argument("--expect-position-x", type=float)
    parser.add_argument("--expect-display-size")
    parser.add_argument("--expect-window-icon", action="store_true")
    parser.add_argument("--audit-text", action="store_true",
                        help="record UI text draw bounds and bundled-font usage")
    parser.add_argument("--audit-memory", action="store_true",
                        help="sample the process working set during the run")
    parser.add_argument("--pace", action="store_true",
                        help="wait dt seconds per frame for real-time stability runs")
    return parser.parse_args()


def _event_from_description(pygame, description):
    kind = str(description["type"]).lower().replace("-", "_")
    types = {
        "mouse_move": pygame.MOUSEMOTION,
        "mouse_down": pygame.MOUSEBUTTONDOWN,
        "mouse_up": pygame.MOUSEBUTTONUP,
        "wheel": pygame.MOUSEWHEEL,
        "key_down": pygame.KEYDOWN,
        "key_up": pygame.KEYUP,
        "resize": pygame.VIDEORESIZE,
        "focus_lost": pygame.WINDOWFOCUSLOST,
        "focus_gained": pygame.WINDOWFOCUSGAINED,
        "window_leave": pygame.WINDOWLEAVE,
        "minimize": pygame.WINDOWMINIMIZED,
        "restore": pygame.WINDOWRESTORED,
        "quit": pygame.QUIT,
        "drop_file": pygame.DROPFILE,
    }
    if kind not in types:
        raise ValueError(f"Unknown input event: {kind}")
    values = {key: value for key, value in description.items() if key != "type"}
    if "pos" in values:
        values["pos"] = tuple(map(int, values["pos"]))
    if "rel" in values:
        values["rel"] = tuple(map(int, values["rel"]))
    if "buttons" in values:
        values["buttons"] = tuple(values["buttons"])
    if "key" in values and isinstance(values["key"], str):
        raw_key = values["key"].replace(" ", "")
        key_name = raw_key.lower() if len(raw_key) == 1 and raw_key.isalpha() else raw_key.upper()
        values["key"] = getattr(pygame, "K_" + key_name)
    if kind == "resize":
        width, height = map(int, values.get("size", (values.get("w", 1280),
                                                       values.get("h", 720))))
        values.update(w=width, h=height, size=(width, height))
    return pygame.event.Event(types[kind], values)


def _scheduled_events(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result = {}
    for entry in data:
        result.setdefault(int(entry["frame"]), []).extend(entry.get("events", ()))
    return result


def _safe_name(value):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value)).strip("_").lower()


def _memory_snapshot():
    """Return resident and peak resident bytes where the OS exposes them."""
    if os.name == "nt":
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        try:
            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            get_memory = psapi.GetProcessMemoryInfo
            get_memory.argtypes = (wintypes.HANDLE,
                                   ctypes.POINTER(ProcessMemoryCounters),
                                   wintypes.DWORD)
            get_memory.restype = wintypes.BOOL
            success = get_memory(kernel.GetCurrentProcess(), ctypes.byref(counters),
                                 counters.cb)
            if success:
                return {"resident_bytes": int(counters.WorkingSetSize),
                        "peak_resident_bytes": int(counters.PeakWorkingSetSize)}
        except (AttributeError, OSError):
            return None
    statm = Path("/proc/self/statm")
    if statm.exists():
        try:
            resident_pages = int(statm.read_text().split()[1])
            resident = resident_pages * os.sysconf("SC_PAGE_SIZE")
            return {"resident_bytes": resident, "peak_resident_bytes": None}
        except (OSError, ValueError, IndexError):
            return None
    return None


class HarnessClock:
    def __init__(self, pygame, frames, dt, schedule, fuzz_seed=None,
                 dashboard_ref=None, pace=False):
        self.pygame = pygame
        self.limit = max(1, frames)
        self.dt = max(0.0, dt)
        self.schedule = schedule
        self.fuzz_seed = fuzz_seed
        self.rng = random.Random(fuzz_seed) if fuzz_seed is not None else None
        self.dashboard_ref = dashboard_ref
        self.pace = pace
        self.frame = 0
        self.generated_events = 0
        self.frame_started = None

    def tick(self, _target_fps=0):
        self.frame += 1
        events = list(self.schedule.get(self.frame, ()))
        if self.rng is not None and self.frame < self.limit:
            events.extend(self._fuzz_events())
        for description in events:
            action_event = description.get("type")
            if action_event in ("click_action", "mouse_down_action", "move_to_action"):
                dashboard = self.dashboard_ref()
                action = tuple(description.get("action", ()))
                rect = getattr(dashboard, "buttons", {}).get(action)
                if rect is None:
                    raise ValueError(f"No live UI action to click: {action}")
                position = (rect.centerx, rect.centery)
                event_descriptions = [{
                    "type": "mouse_move", "pos": position, "rel": (0, 0),
                    "buttons": (0, 0, 0),
                }]
                if action_event in ("click_action", "mouse_down_action"):
                    event_descriptions.append({"type": "mouse_down", "pos": position,
                                               "button": 1})
                if action_event == "click_action":
                    event_descriptions.append({"type": "mouse_up", "pos": position,
                                               "button": 1})
                for event_description in event_descriptions:
                    self.pygame.mouse.set_pos(position)
                    self.pygame.event.post(_event_from_description(
                        self.pygame, event_description))
                    self.generated_events += 1
                continue
            if "pos" in description:
                try:
                    self.pygame.mouse.set_pos(tuple(map(int, description["pos"])))
                except self.pygame.error:
                    pass
            self.pygame.event.post(_event_from_description(self.pygame, description))
            self.generated_events += 1
        if self.frame >= self.limit:
            self.pygame.event.post(self.pygame.event.Event(self.pygame.QUIT))
        if self.pace and self.dt:
            time.sleep(self.dt)
        self.frame_started = time.perf_counter()
        return round(self.dt * 1000)

    def get_fps(self):
        return round(1 / self.dt) if self.dt > 0 else 0

    def _fuzz_events(self):
        pygame = self.pygame
        dashboard = self.dashboard_ref()
        layout = getattr(dashboard, "app_layout", None) if dashboard else None
        roll = self.rng.random()
        if layout and roll < 0.27:
            if dashboard and dashboard.active_destination == "Landing" and dashboard.buttons:
                action = self.rng.choice(tuple(dashboard.buttons))
                target = dashboard.buttons[action]
                position = (target.centerx, target.centery)
                return [
                    {"type": "mouse_move", "pos": position, "rel": (0, 0),
                     "buttons": (0, 0, 0)},
                    {"type": "mouse_down", "pos": position, "button": 1},
                    {"type": "mouse_up", "pos": position, "button": 1},
                ]
            # Click a live navigation or toolbar target using current geometry.
            candidates = list(layout.navigation.values())
            candidates.extend((layout.projection, layout.render_mode,
                               layout.theme_toggle, layout.help_button,
                               layout.music_toggle))
            target = self.rng.choice(candidates)
            position = (target.centerx, target.centery)
            return [
                {"type": "mouse_move", "pos": position, "rel": (0, 0),
                 "buttons": (0, 0, 0)},
                {"type": "mouse_down", "pos": position, "button": 1},
                {"type": "mouse_up", "pos": position, "button": 1},
            ]
        if layout and roll < 0.42:
            box = layout.viewport
            position = (self.rng.randint(box.left, max(box.left, box.right - 1)),
                        self.rng.randint(box.top, max(box.top, box.bottom - 1)))
            button = self.rng.choice((1, 2, 3))
            return [
                {"type": "mouse_down", "pos": position, "button": button},
                {"type": "mouse_move", "pos": (position[0] + 7, position[1] + 4),
                 "rel": (7, 4), "buttons": (int(button == 1), int(button == 2),
                                               int(button == 3))},
                {"type": "mouse_up", "pos": (-12, -12), "button": button},
            ]
        if layout and roll < 0.52:
            panel = dashboard.scene_panel.list_rect
            return [{"type": "wheel", "x": 0,
                     "y": self.rng.choice((-4, -1, 1, 4)),
                     "pos": (panel.centerx, panel.centery)}]
        if roll < 0.72:
            key = self.rng.choice(("left", "right", "up", "down", "q", "e",
                                   "w", "a", "s", "d", "p", "x", "m",
                                   "space", "tab", "f1", "o"))
            return [{"type": "key_down", "key": key},
                    {"type": "key_up", "key": key}]
        if roll < 0.82:
            return [{"type": "resize", "size": self.rng.choice(
                ((1024, 640), (1280, 720), (1366, 768), (1920, 1080),
                 (1024, 1500), (2200, 720)))}]
        if roll < 0.9:
            return [{"type": "focus_lost"}, {"type": "focus_gained"}]
        return [{"type": "mouse_up", "pos": (-20, -20),
                 "button": self.rng.choice((1, 2, 3))}]


def main():
    args = _arguments()
    repository_root = Path(__file__).resolve().parents[2]
    if str(repository_root) not in sys.path:
        sys.path.insert(0, str(repository_root))
    desktop = tuple(int(value) for value in args.initial.lower().split("x", 1))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    state_root = output / "state"
    state_root.mkdir(exist_ok=True)
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["SDL_RENDER_DRIVER"] = "software"
    os.environ["LOCALAPPDATA"] = str(state_root)
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    log_path = output / "run.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=(logging.FileHandler(log_path, encoding="utf-8"),
                                  logging.StreamHandler(sys.stdout)), force=True)
    logger = logging.getLogger("renderx.qa")
    schedule = _scheduled_events(args.events)
    captures = ({int(value) for value in args.capture.split(",") if value.strip()}
                if args.capture not in ("", "destinations") else set())
    capture_destinations = args.capture == "destinations"

    import pygame
    warnings_action = "error"
    import warnings
    warnings.simplefilter(warnings_action, DeprecationWarning)
    pygame.display.get_desktop_sizes = lambda: [desktop]
    dashboard_ref = {"dashboard": None}
    controls_ref = {"controls": None}
    scene_ref = {"scene": None}
    timings = []
    frame_timings = []
    memory_samples = []
    original_draw = None
    original_events = None
    original_update = None

    from renderx.dashboard import Dashboard
    from renderx.input import Controls
    from renderx.ui import fonts as ui_fonts
    import renderx.quest_ui as quest_ui

    text_audit = {"calls": 0, "roles": set(), "violations": [],
                  "font_requests": 0, "font_cache_misses_max": 0}
    original_font = ui_fonts.font
    original_draw_text = ui_fonts.draw_text
    original_draw_wrapped = ui_fonts.draw_wrapped
    original_quest_text = quest_ui._text
    original_quest_wrapped = quest_ui._draw_wrapped
    font_cache_misses = original_font.cache_info().misses

    def check_text_bounds(surface, rect, description):
        text_audit["calls"] += 1
        bounds = surface.get_rect()
        if not bounds.contains(rect):
            text_audit["violations"].append(
                f"{description} at {tuple(rect)} falls outside {tuple(bounds)}")

    def observed_font(role, *positional, **keywords):
        nonlocal font_cache_misses
        text_audit["roles"].add(str(role))
        if role not in ui_fonts.theme.TYPE_SCALE:
            text_audit["violations"].append(f"Unknown text role: {role!r}")
        result = original_font(role, *positional, **keywords)
        text_audit["font_requests"] += 1
        current_misses = original_font.cache_info().misses
        if current_misses < font_cache_misses:
            font_cache_misses = 0
        else:
            font_cache_misses = current_misses
        text_audit["font_cache_misses_max"] = max(
            text_audit["font_cache_misses_max"], font_cache_misses)
        return result

    # The application clears font caches during normal shutdown.
    observed_font.cache_clear = original_font.cache_clear
    observed_font.cache_info = original_font.cache_info

    def observed_draw_text(surface, value, position, role="body", color=None,
                           *, anchor="topleft", bold=False, max_width=None):
        rect = original_draw_text(surface, value, position, role, color,
                                  anchor=anchor, bold=bold,
                                  max_width=max_width)
        check_text_bounds(surface, rect, f"draw_text({value!r})")
        if max_width is not None and rect.width > max_width:
            text_audit["violations"].append(
                f"draw_text({value!r}) width {rect.width} exceeds {max_width}")
        return rect

    def observed_draw_wrapped(surface, value, position, width, role="body",
                              color=None, *, line_gap=None):
        typeface = original_font(role)
        max_width = max(1, int(width))
        words, rows, row = str(value).split(), [], ""
        for word in words:
            candidate = word if not row else row + " " + word
            if typeface.size(candidate)[0] <= max_width or not row:
                row = candidate
            else:
                rows.append(row)
                row = word
        if row:
            rows.append(row)
        gap = ui_fonts.theme.SPACE["xs"] if line_gap is None else line_gap
        y = position[1]
        for text in rows:
            width_px, height_px = typeface.size(text)
            rect = pygame.Rect(position[0], y, width_px, height_px)
            check_text_bounds(surface, rect, f"draw_wrapped({text!r})")
            if width_px > max_width:
                text_audit["violations"].append(
                    f"draw_wrapped({text!r}) width {width_px} exceeds {max_width}")
            y += max(typeface.get_linesize(), height_px) + gap
        return original_draw_wrapped(surface, value, position, width, role,
                                      color, line_gap=line_gap)

    def observed_quest_text(surface, value, position, typeface, color,
                            center=False, right=False):
        rect = typeface.render(str(value), True, color).get_rect()
        if center:
            rect.center = position
        elif right:
            rect.midright = position
        else:
            rect.topleft = position
        check_text_bounds(surface, rect, f"quest_text({value!r})")
        return original_quest_text(surface, value, position, typeface, color,
                                   center=center, right=right)

    def observed_quest_wrapped(surface, value, x, y, width, typeface, color,
                               line_gap=5):
        start_y = y
        words, rows, row = str(value).split(), [], ""
        for word in words:
            candidate = word if not row else row + " " + word
            if typeface.size(candidate)[0] <= width or not row:
                row = candidate
            else:
                rows.append(row)
                row = word
        if row:
            rows.append(row)
        for text in rows:
            rect = pygame.Rect(x, y, *typeface.size(text))
            check_text_bounds(surface, rect, f"quest_wrapped({text!r})")
            if rect.width > width:
                text_audit["violations"].append(
                    f"quest_wrapped({text!r}) width {rect.width} exceeds {width}")
            y += max(typeface.get_linesize(), rect.height) + line_gap
        return original_quest_wrapped(surface, value, x, start_y,
                                      width, typeface, color,
                                      line_gap=line_gap)

    if args.audit_text:
        ui_fonts.font = observed_font
        ui_fonts.draw_text = observed_draw_text
        ui_fonts.draw_wrapped = observed_draw_wrapped
        quest_ui._text = observed_quest_text
        quest_ui._draw_wrapped = observed_quest_wrapped

    original_draw = Dashboard.draw
    original_events = Dashboard.events
    original_update = Controls.update

    def _log_wrapped(label, function):
        def call(self, *positional, **keywords):
            try:
                return function(self, *positional, **keywords)
            except Exception:
                logger.exception("Exception in %s at frame %s", label, clock.frame)
                raise
        return call

    def observed_draw(self, target, mesh, scene, *positional, **keywords):
        dashboard_ref["dashboard"] = self
        scene_ref["scene"] = scene
        if clock.frame == 0 and args.scenario in ("idle", "orbit", "largest"):
            self.active_destination = "Explore"
            if args.scenario == "largest":
                scene.select("Signal wave")
        if args.audit_memory and clock.frame and clock.frame % 600 == 0:
            snapshot = _memory_snapshot()
            if snapshot:
                memory_samples.append({"frame": clock.frame, **snapshot})
        started = time.perf_counter()
        try:
            return original_draw(self, target, mesh, scene, *positional, **keywords)
        except Exception:
            logger.exception("Exception drawing dashboard at frame %s", clock.frame)
            raise
        finally:
            timings.append((time.perf_counter() - started) * 1000)

    Dashboard.draw = observed_draw
    Dashboard.events = _log_wrapped("event handlers", original_events)

    def observed_update(self, *positional, **keywords):
        controls_ref["controls"] = self
        try:
            return original_update(self, *positional, **keywords)
        except Exception:
            logger.exception("Exception updating input at frame %s", clock.frame)
            raise

    Controls.update = observed_update

    clock = HarnessClock(pygame, args.frames, args.dt, schedule,
                         fuzz_seed=args.fuzz_seed,
                         dashboard_ref=lambda: dashboard_ref["dashboard"],
                         pace=args.pace)
    pygame.time.Clock = lambda: clock
    original_flip = pygame.display.flip
    original_set_icon = pygame.display.set_icon
    original_set_cursor = pygame.mouse.set_cursor
    captured_destinations = set()
    window_identity = {}
    icon_calls = []
    cursor_calls = []

    def observed_set_icon(surface):
        icon_calls.append(surface.get_size())
        pygame.image.save(surface, output / "window-icon.png")
        return original_set_icon(surface)

    def observed_set_cursor(*cursor):
        constants = {getattr(pygame, name): name for name in (
            "SYSTEM_CURSOR_ARROW", "SYSTEM_CURSOR_HAND", "SYSTEM_CURSOR_IBEAM",
            "SYSTEM_CURSOR_SIZEWE", "SYSTEM_CURSOR_SIZEALL")}
        label = constants.get(cursor[0], str(cursor[0])) if cursor else "unknown"
        def record(supported):
            entry = {"cursor": label, "supported": supported}
            if entry not in cursor_calls:
                cursor_calls.append(entry)
        try:
            result = original_set_cursor(*cursor)
        except pygame.error:
            record(False)
            raise
        record(True)
        return result

    pygame.display.set_icon = observed_set_icon
    pygame.mouse.set_cursor = observed_set_cursor

    def observed_flip():
        original_flip()
        if clock.frame_started is not None:
            frame_timings.append((time.perf_counter() - clock.frame_started) * 1000)
        display = pygame.display.get_surface()
        if display is None:
            return
        if not window_identity:
            window_identity["caption"] = pygame.display.get_caption()
        window_identity["display_size"] = display.get_size()
        if clock.frame in captures:
            path = output / f"frame-{clock.frame:06d}.png"
            pygame.image.save(display, path)
            logger.info("Screenshot saved: %s", path)
        if capture_destinations:
            dashboard = dashboard_ref["dashboard"]
            destination = getattr(dashboard, "active_destination", None)
            if destination and destination not in captured_destinations:
                captured_destinations.add(destination)
                path = output / f"destination-{_safe_name(destination)}.png"
                pygame.image.save(display, path)
                logger.info("Destination screenshot saved: %s", path)

    pygame.display.flip = observed_flip
    if args.scenario == "orbit":
        # Capture the current viewport after the initial dashboard geometry is known.
        schedule.setdefault(1, []).extend((
            {"type": "mouse_down", "button": 1, "pos": (700, 400)},
            {"type": "mouse_move", "pos": (770, 448), "rel": (70, 48),
             "buttons": (1, 0, 0)},
            {"type": "mouse_up", "button": 1, "pos": (770, 448)},
        ))

    run_started = time.perf_counter()
    if args.audit_memory:
        initial_memory = _memory_snapshot()
        if initial_memory:
            memory_samples.append({"frame": 0, **initial_memory})
    status = "passed"
    error = None
    try:
        from renderx.app import run
        run(skip_landing=args.skip_landing, mode=args.mode)
    except Exception as exception:
        status = "error"
        error = f"{type(exception).__name__}: {exception}"
        logger.error("Application failed:\n%s", traceback.format_exc())
    finally:
        Dashboard.draw = original_draw
        Dashboard.events = original_events
        Controls.update = original_update
        ui_fonts.font = original_font
        ui_fonts.draw_text = original_draw_text
        ui_fonts.draw_wrapped = original_draw_wrapped
        quest_ui._text = original_quest_text
        quest_ui._draw_wrapped = original_quest_wrapped
        pygame.display.flip = original_flip
        pygame.display.set_icon = original_set_icon
        pygame.mouse.set_cursor = original_set_cursor

    elapsed = time.perf_counter() - run_started
    if args.audit_memory:
        final_memory = _memory_snapshot()
        if final_memory:
            memory_samples.append({"frame": clock.frame, **final_memory})
    ordered = sorted(timings)
    def percentile(q):
        if not ordered:
            return None
        return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * q))]

    dashboard = dashboard_ref["dashboard"]
    active_destination = getattr(dashboard, "active_destination", None)
    controls = controls_ref["controls"]
    scene = scene_ref["scene"]
    scene_state = None
    if scene is not None:
        scene_state = {
            "shape": scene.shape,
            "position": list(scene.position),
            "angles": list(scene.angles),
            "scale": scene.scale,
            "projection": scene.projection,
        }
    interaction_state = None
    if controls is not None:
        interaction_state = {
            "focused": controls.focused,
            "drag": controls.drag,
            "drag_button": controls.drag_button,
        }
    if dashboard is not None:
        interaction_state = interaction_state or {}
        interaction_state.update({
            "dashboard_focused": dashboard.focused,
            "pressed": dashboard.pressed,
            "hover": dashboard.hover,
            "drag_action": dashboard.drag_action,
            "drag_splitter": dashboard.drag_splitter,
            "focused_field": dashboard.focused_field,
            "scene_scroll": dashboard.scene_panel.scroll,
            "help_open": dashboard.help_open,
        })
    if scene_state is not None:
        scene_values = (scene_state["position"] + scene_state["angles"] +
                        [scene_state["scale"]])
        if not all(isfinite(float(value)) for value in scene_values):
            status = "error"
            error = "Non-finite value in the final scene state"
            logger.error("%s: %s", error, scene_state)
    summary = {
        "status": status,
        "error": error,
        "scenario": args.scenario,
        "seed": args.fuzz_seed,
        "target_frames": args.frames,
        "frames_advanced": clock.frame,
        "events_injected": clock.generated_events,
        "simulated_seconds": round(clock.frame * args.dt, 2),
        "wall_seconds": round(elapsed, 3),
        "draw_calls": len(timings),
        "draw_ms_avg": round(sum(timings) / len(timings), 3) if timings else None,
        "draw_ms_p95": round(percentile(.95), 3) if timings else None,
        "draw_ms_p99": round(percentile(.99), 3) if timings else None,
        "frame_ms_avg": round(sum(frame_timings) / len(frame_timings), 3)
                         if frame_timings else None,
        "frame_ms_p95": round(sorted(frame_timings)[min(
            len(frame_timings) - 1, round((len(frame_timings) - 1) * .95))], 3)
                         if frame_timings else None,
        "frame_ms_p99": round(sorted(frame_timings)[min(
            len(frame_timings) - 1, round((len(frame_timings) - 1) * .99))], 3)
                         if frame_timings else None,
        "measured_frames": len(frame_timings),
        "destination": active_destination,
        "active_navigation_state": (dashboard.state(("destination", active_destination))
                                    if dashboard and active_destination else None),
        "window_identity": window_identity,
        "window_icon_set_calls": icon_calls,
        "cursor_set_calls": cursor_calls,
        "typography_audit": ({
            "calls": text_audit["calls"],
            "roles": sorted(text_audit["roles"]),
            "violations": text_audit["violations"],
            "font_files": {family: {"path": str(path), "exists": path.is_file()}
                           for family, path in ui_fonts.FONT_FILES.items()},
            "font_cache": {"misses_during_run": text_audit["font_cache_misses_max"],
                           "font_requests": text_audit["font_requests"],
                           "maxsize": original_font.cache_info().maxsize},
        } if args.audit_text else None),
        "memory_audit": ({
            "samples": memory_samples,
            "resident_delta_bytes": (memory_samples[-1]["resident_bytes"] -
                                     memory_samples[0]["resident_bytes"])
                                    if len(memory_samples) >= 2 else None,
            "peak_resident_bytes": max(
                (sample["peak_resident_bytes"] for sample in memory_samples
                 if sample["peak_resident_bytes"] is not None), default=None),
        } if args.audit_memory else None),
        "scene_state": scene_state,
        "interaction_state": interaction_state,
        "screenshots": sorted(path.name for path in output.glob("*.png")),
    }
    failures = []
    if args.expect_destination and active_destination != args.expect_destination:
        failures.append(f"destination={active_destination!r}, expected {args.expect_destination!r}")
    if args.expect_help_closed and dashboard and dashboard.help_open:
        failures.append("help overlay remained open")
    if args.expect_no_drag and interaction_state and any((
            interaction_state.get("drag"), interaction_state.get("drag_button"),
            interaction_state.get("drag_action"), interaction_state.get("drag_splitter"),
            interaction_state.get("pressed"))):
        failures.append("a drag or pressed state remained active")
    if args.expect_hover_clear and interaction_state and interaction_state.get("hover"):
        failures.append(f"hover remained active: {interaction_state['hover']!r}")
    if args.expect_pressed_clear and interaction_state and interaction_state.get("pressed"):
        failures.append(f"pressed action remained active: {interaction_state['pressed']!r}")
    if args.expect_cursor and not cursor_calls:
        failures.append("the app did not set a contextual cursor")
    if args.expect_shape and scene_state and scene_state["shape"] != args.expect_shape:
        failures.append(f"shape={scene_state['shape']!r}, expected {args.expect_shape!r}")
    if (args.expect_position_x is not None and scene_state and
            abs(scene_state["position"][0] - args.expect_position_x) > 1e-9):
        failures.append(f"position X={scene_state['position'][0]!r}, expected {args.expect_position_x!r}")
    if args.expect_display_size:
        expected_size = [int(value) for value in args.expect_display_size.lower().split("x", 1)]
        if list(window_identity.get("display_size", ())) != expected_size:
            failures.append(f"display size={window_identity.get('display_size')!r}, expected {expected_size!r}")
    if args.expect_window_icon and not icon_calls:
        failures.append("the app did not set a window icon")
    if args.audit_text:
        if text_audit["violations"]:
            failures.append(f"text audit found {len(text_audit['violations'])} issue(s)")
        missing_fonts = [family for family, path in ui_fonts.FONT_FILES.items()
                         if not path.is_file()]
        if missing_fonts:
            failures.append(f"bundled font files are missing: {missing_fonts!r}")
    if failures:
        summary["status"] = status = "error"
        summary["error"] = error = "; ".join(failures)
        logger.error("Expectation failures: %s", error)
    (output / "summary.json").write_text(json.dumps(summary, indent=2),
                                          encoding="utf-8")
    logger.info("Run summary: %s", json.dumps(summary, sort_keys=True))
    return 1 if status != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
