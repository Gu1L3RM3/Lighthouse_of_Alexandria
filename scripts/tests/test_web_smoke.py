import io
import tarfile

from PIL import Image, ImageDraw

from web_smoke import PageRun, bundle_leaks, changed_ratio, failure_reason, is_blank, to_page


def png(color=(0, 0, 0), boxes=0) -> bytes:
    image = Image.new("RGB", (320, 180), color)
    draw = ImageDraw.Draw(image)
    for index in range(boxes):
        draw.rectangle((index * 8, 0, index * 8 + 7, 179), fill=(index * 6, 90, 255 - index * 6))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def test_a_finished_boot_with_a_drawn_frame_passes():
    assert failure_reason(PageRun(boot="done", frame=png(boxes=40))) is None


def test_a_python_crash_wins_over_everything_else():
    run = PageRun(boot="done", crash="KeyError: 'door'", frame=png(boxes=40))

    assert "KeyError: 'door'" in failure_reason(run)


def test_a_javascript_error_fails():
    run = PageRun(boot="done", page_errors=["boot is not defined"], frame=png(boxes=40))

    assert "boot is not defined" in failure_reason(run)


def test_a_boot_that_never_finishes_names_the_last_state():
    assert "unpack" in failure_reason(PageRun(boot="unpack"))


def test_a_blank_canvas_fails():
    assert "blank" in failure_reason(PageRun(boot="done", frame=png()))


def test_a_tap_that_changes_nothing_fails():
    frame = png(boxes=40)
    run = PageRun(boot="done", frame=frame, after_tap=frame)

    assert "tap" in failure_reason(run)


def test_a_tap_that_opens_another_screen_passes():
    run = PageRun(boot="done", frame=png(boxes=40), after_tap=png((200, 40, 40)))

    assert failure_reason(run) is None


def test_blank_and_changed_ratio_compare_pixels():
    assert is_blank(png())
    assert not is_blank(png(boxes=40))
    assert changed_ratio(png(), png()) == 0
    assert changed_ratio(png(), png((255, 255, 255))) == 1


def test_game_coordinates_follow_the_letterboxed_canvas():
    canvas = {"x": 75.0, "y": 0.0, "width": 640.0, "height": 360.0}

    assert to_page((640, 360), canvas) == (395.0, 180.0)


def test_local_only_folders_in_the_bundle_are_reported(tmp_path):
    archive = tmp_path / "game.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for name in ("assets/main.py", "assets/.claude/settings.json", "assets/scripts/ralph.sh"):
            tar.addfile(tarfile.TarInfo(name), io.BytesIO())

    assert bundle_leaks(archive) == [".claude", "scripts"]
