"""The security session: required before shipping website work, and only then."""

from pathlib import Path

import pytest

from test_ralph import git, make_repo, ralph_refs, run_ralph, summary_rows

ONE_TASK = "- [ ] T-01 a site page — done when: test passes\n"


def run_site_task(tmp_path, needed=True, **changes):
    repo, env, calls, _ = make_repo(tmp_path, "success", ONE_TASK)
    env.update({"HARNESS_SHIP": "1", **changes})
    if needed:
        env["FAKE_SECURITY_NEEDED"] = "1"
    result = run_ralph(repo, env)
    return repo, env, calls.read_text(), result


def results(env):
    return {row["task"]: row["result"] for row in summary_rows(env)}


def verified_marker(repo):
    marker = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "harness-security-passed"))
    return marker.read_text().strip() if marker.exists() else ""


def test_game_work_ships_without_a_security_session(tmp_path):
    _, env, calls, result = run_site_task(tmp_path, needed=False)

    assert result.returncode == 0, result.stderr
    assert "web-security/SKILL.md" not in calls
    assert results(env) == {"T-01": "passed", "ship": "shipped"}


def test_website_work_ships_after_the_security_session_passes(tmp_path):
    repo, env, calls, result = run_site_task(tmp_path)

    assert result.returncode == 0, result.stderr
    assert calls.index("web-security/SKILL.md") < calls.index("ship-branch/SKILL.md")
    assert results(env) == {"T-01": "passed", "security": "passed", "ship": "shipped"}
    assert verified_marker(repo) == git(repo, "rev-parse", "HEAD")


@pytest.mark.parametrize("verdict", ["blocked", "missing", "buried", "crash"])
def test_anything_but_a_final_pass_blocks_the_ship(tmp_path, verdict):
    repo, env, calls, result = run_site_task(tmp_path, FAKE_SECURITY=verdict)

    assert result.returncode == 1
    assert "ship-branch/SKILL.md" not in calls
    assert results(env)["security"] == "blocked"
    assert "ship" not in results(env)
    assert verified_marker(repo) == ""
    # The work stays on the branch for a human to look at.
    assert (repo / "result.txt").exists()


def test_the_security_session_may_not_change_the_code(tmp_path):
    repo, env, calls, result = run_site_task(tmp_path, FAKE_SECURITY="edit")

    assert result.returncode == 1
    assert "ship-branch/SKILL.md" not in calls
    assert not (repo / "patched.txt").exists()
    assert any(ref.startswith("refs/ralph/security/") for ref in ralph_refs(repo))


def test_security_runs_even_when_shipping_is_disabled(tmp_path):
    _, env, calls, result = run_site_task(tmp_path, HARNESS_SHIP="0")

    assert result.returncode == 0, result.stderr
    assert "web-security/SKILL.md" in calls
    assert results(env)["security"] == "passed"


@pytest.mark.parametrize(("chosen", "expected"), [({}, "origin/main"), ({"HARNESS_BASE": "HEAD~1"}, "HEAD~1")])
def test_the_security_session_is_told_what_to_compare_against(tmp_path, chosen, expected):
    _, _, calls, _ = run_site_task(tmp_path, **chosen)

    assert f"Base da revisão: {expected}." in calls
