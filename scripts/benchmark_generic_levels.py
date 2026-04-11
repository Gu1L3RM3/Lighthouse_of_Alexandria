import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path


# Keep benchmark headless/non-intrusive by default.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import pygame

from game import Game


@dataclass
class BenchResult:
    name: str
    frames: int
    avg_fps: float
    one_percent_low_fps: float
    avg_frame_ms: float
    avg_input_ms: float
    avg_update_ms: float
    avg_render_ms: float
    avg_flip_ms: float


def p99(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    idx = int(0.99 * (len(sorted_values) - 1))
    return sorted_values[idx]


def benchmark_scene(scene, frames: int, dt: float, warmup: int) -> BenchResult:
    # Some scenes print extra debug logs; disable if present.
    if hasattr(scene, "debug_panel_logs"):
        scene.debug_panel_logs = False

    frame_times_ms: list[float] = []
    input_ms = 0.0
    update_ms = 0.0
    render_ms = 0.0
    flip_ms = 0.0

    for frame_idx in range(frames + warmup):
        frame_start = time.perf_counter()

        t0 = time.perf_counter()
        events = pygame.event.get()
        scene.process_input(events)
        t1 = time.perf_counter()
        scene.update(dt)
        t2 = time.perf_counter()
        scene.render()
        t3 = time.perf_counter()
        pygame.display.flip()
        t4 = time.perf_counter()

        if frame_idx >= warmup:
            frame_times_ms.append((t4 - frame_start) * 1000.0)
            input_ms += (t1 - t0) * 1000.0
            update_ms += (t2 - t1) * 1000.0
            render_ms += (t3 - t2) * 1000.0
            flip_ms += (t4 - t3) * 1000.0

    total_ms = sum(frame_times_ms)
    avg_frame_ms = total_ms / max(1, len(frame_times_ms))
    avg_fps = 1000.0 / avg_frame_ms if avg_frame_ms > 0 else 0.0
    p99_ms = p99(frame_times_ms)
    one_percent_low_fps = 1000.0 / p99_ms if p99_ms > 0 else 0.0
    measured = max(1, len(frame_times_ms))

    return BenchResult(
        name=scene.__class__.__name__,
        frames=measured,
        avg_fps=avg_fps,
        one_percent_low_fps=one_percent_low_fps,
        avg_frame_ms=avg_frame_ms,
        avg_input_ms=input_ms / measured,
        avg_update_ms=update_ms / measured,
        avg_render_ms=render_ms / measured,
        avg_flip_ms=flip_ms / measured,
    )


def print_report(results: list[BenchResult]):
    print("=== Generic Levels Benchmark (headless) ===")
    print(
        "scene".ljust(18),
        "avg_fps".rjust(9),
        "1%low".rjust(9),
        "frame_ms".rjust(10),
        "input_ms".rjust(10),
        "update_ms".rjust(10),
        "render_ms".rjust(10),
        "flip_ms".rjust(9),
    )
    for r in results:
        print(
            r.name.ljust(18),
            f"{r.avg_fps:9.2f}",
            f"{r.one_percent_low_fps:9.2f}",
            f"{r.avg_frame_ms:10.3f}",
            f"{r.avg_input_ms:10.3f}",
            f"{r.avg_update_ms:10.3f}",
            f"{r.avg_render_ms:10.3f}",
            f"{r.avg_flip_ms:9.3f}",
        )


def main():
    parser = argparse.ArgumentParser(description="Benchmark generic levels performance headlessly.")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--dt", type=float, default=1.0 / 60.0)
    args = parser.parse_args()

    # Game() already initializes pygame/display and registers all scenes.
    _ = args.width
    _ = args.height
    game = Game()
    scene_manager = game.scene_manager
    target_scene_names = ["fase_3", "fase_4", "fase_5", "fase_6", "fase_7"]

    results: list[BenchResult] = []
    for scene_name in target_scene_names:
        scene = scene_manager.scenes.get(scene_name)
        if scene is None:
            print(f"[WARN] Scene '{scene_name}' not found, skipping.")
            continue
        result = benchmark_scene(scene, frames=args.frames, dt=args.dt, warmup=args.warmup)
        result.name = scene_name
        results.append(result)

    print_report(results)
    pygame.quit()


if __name__ == "__main__":
    main()
