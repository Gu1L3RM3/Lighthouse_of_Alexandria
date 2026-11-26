from smoke_scenes import failure_reason, select_scenes


def test_a_clean_run_with_a_screenshot_passes(tmp_path):
    screenshot = tmp_path / "scene.png"
    screenshot.write_bytes(b"png")

    assert failure_reason(0, "[ALEX_PROFILE] auto-stop scene=help", screenshot) is None


def test_a_crash_is_reported_with_its_last_line(tmp_path):
    output = "Traceback (most recent call last):\n  File 'x'\nKeyError: 'door'\n"

    assert failure_reason(1, output, tmp_path / "scene.png") == "KeyError: 'door'"


def test_a_traceback_fails_even_with_exit_zero(tmp_path):
    screenshot = tmp_path / "scene.png"
    screenshot.write_bytes(b"png")
    output = "Traceback (most recent call last):\nValueError: swallowed\n"

    assert failure_reason(0, output, screenshot) == "ValueError: swallowed"


def test_an_unregistered_scene_fails(tmp_path):
    screenshot = tmp_path / "scene.png"
    screenshot.write_bytes(b"png")
    output = "[ALEX_PROFILE] warning: scene 'fase_99' not found"

    assert "not found" in failure_reason(0, output, screenshot)


def test_a_run_without_a_screenshot_fails(tmp_path):
    assert "screenshot" in failure_reason(0, "", tmp_path / "missing.png")


def test_requested_scenes_must_be_registered():
    registered = ["help", "level_1"]

    assert select_scenes(registered, []) == registered
    assert select_scenes(registered, ["level_1"]) == ["level_1"]
    try:
        select_scenes(registered, ["fase_99"])
    except ValueError as error:
        assert "fase_99" in str(error)
    else:
        raise AssertionError("an unknown scene must be rejected")
