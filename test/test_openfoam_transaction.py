"""Public OpenFOAM exports publish complete cases without changing user files."""

from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from threading import Barrier, Event

import pytest

from MoosasPy.model.io.foam import exportFoam
from MoosasPy.transform import transform


@pytest.fixture(scope="module")
def models():
    cases = Path(__file__).parent / "caseFile"
    return {
        "building": transform(str(cases / "test0_6spacesIntersection.geo"),
                              input_type="geo", stdout=StringIO()),
        "indoor": transform(str(cases / "test6_twoVolumes.geo"),
                            input_type="geo", stdout=StringIO()),
    }


def export_options(models, scenario):
    if scenario == "mesh":
        return models["building"], dict(space_index=0, grid_size=2)
    conditions = dict(viscosity=1.5e-5, turbulence_intensity=0.05,
                      turbulence_length=1.0, iterations=10)
    if scenario == "indoor":
        conditions.update(inlet={"opening": "gls_g_80", "velocity": [0.409451, 0.286966, 0]},
                          outlet={"opening": "gls_g_79", "pressure": 0.0})
        return models["indoor"], dict(scenario=scenario, space_index=37,
                                      grid_size=2, conditions=conditions)
    conditions.update(velocity=[2.0, 0.0, 0.0], domain=[[-100, 120, 0], [0, 240, 45]],
                      inside_point=[-90, 130, 5])
    return models["building"], dict(scenario=scenario, grid_size=4, conditions=conditions)


@pytest.mark.parametrize("scenario", ["mesh", "indoor", "outdoor"])
@pytest.mark.parametrize("existing_empty", [False, True])
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
def test_failed_write_leaves_no_partial_case(models, tmp_path, monkeypatch,
                                           scenario, existing_empty, error_type):
    model, options = export_options(models, scenario)
    case_dir = tmp_path / "case"
    if existing_empty:
        case_dir.mkdir()
    neighbor = tmp_path / "user-data"
    neighbor.mkdir()
    (neighbor / "notes.txt").write_text("keep")
    original_open = Path.open

    def failing_open(path, *args, **kwargs):
        if path.name == ("owner" if scenario == "mesh" else "controlDict"):
            raise error_type("simulated interrupted write")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", failing_open)
    with pytest.raises(error_type, match="simulated interrupted write"):
        exportFoam(model, case_dir / "room.foam", **options)

    assert case_dir.exists() == existing_empty
    if existing_empty:
        assert list(case_dir.iterdir()) == []
    assert (neighbor / "notes.txt").read_text() == "keep"
    assert set(tmp_path.iterdir()) == ({neighbor, case_dir} if existing_empty else {neighbor})


@pytest.mark.parametrize("scenario", ["mesh", "indoor", "outdoor"])
def test_nonempty_case_is_unchanged(models, tmp_path, scenario):
    model, options = export_options(models, scenario)
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    (case_dir / "notes.txt").write_bytes(b"user notes")
    (case_dir / "empty-user-directory").mkdir()

    with pytest.raises(FileExistsError):
        exportFoam(model, case_dir / "room.foam", **options)

    assert (case_dir / "notes.txt").read_bytes() == b"user notes"
    assert set(case_dir.iterdir()) == {case_dir / "notes.txt", case_dir / "empty-user-directory"}
    assert list(tmp_path.iterdir()) == [case_dir]


@pytest.mark.parametrize("scenario", ["mesh", "indoor", "outdoor"])
@pytest.mark.parametrize("existing_empty", [False, True])
def test_competing_exports_have_one_complete_winner(models, tmp_path, monkeypatch,
                                                  scenario, existing_empty):
    model, options = export_options(models, scenario)
    case_dir = tmp_path / "case"
    if existing_empty:
        case_dir.mkdir()
    started, release = Event(), Event()
    original_open = Path.open

    def paused_open(path, *args, **kwargs):
        if path.name == ("points" if scenario == "mesh" else "model.stl") and not started.is_set():
            started.set()
            if not release.wait(20):
                raise TimeoutError("competing export did not release writer")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", paused_open)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(exportFoam, model, case_dir / "loser.foam", **options)
        try:
            assert started.wait(20), "export did not start writing"
            # Readers see the original empty directory or no case while writing.
            assert case_dir.exists() == existing_empty
            if existing_empty:
                assert list(case_dir.iterdir()) == []
            result = exportFoam(model, case_dir / "winner.foam", **options)
            winner_files = {path.relative_to(case_dir): path.read_bytes()
                            for path in result.generated_paths}
        finally:
            release.set()
        with pytest.raises(FileExistsError):
            pending.result(timeout=20)

    assert result.primary_path == case_dir / "winner.foam"
    assert result.primary_path.read_bytes() == b""
    assert not (case_dir / "loser.foam").exists()
    assert set(result.generated_paths) == {path for path in case_dir.rglob("*") if path.is_file()}
    assert all(path.is_relative_to(case_dir) for path in result.generated_paths)
    assert winner_files == {path.relative_to(case_dir): path.read_bytes()
                            for path in result.generated_paths}
    assert list(tmp_path.iterdir()) == [case_dir]


@pytest.mark.parametrize("scenario", ["mesh", "indoor", "outdoor"])
def test_relative_target_returns_final_relative_paths(models, tmp_path, monkeypatch, scenario):
    model, options = export_options(models, scenario)
    monkeypatch.chdir(tmp_path)
    target = Path("case") / "room.foam"
    result = exportFoam(model, target, **options)
    assert result.primary_path == target
    assert target in result.generated_paths
    assert all(path.is_relative_to(target.parent) and path.is_file()
               for path in result.generated_paths)
    assert len(result.generated_paths) == len(set(result.generated_paths))
    assert list(tmp_path.iterdir()) == [tmp_path / "case"]


@pytest.mark.parametrize("existing_empty", [False, True])
def test_failed_publish_preserves_original_empty_destination(models, tmp_path, monkeypatch,
                                                           existing_empty):
    model, options = export_options(models, "mesh")
    case_dir = tmp_path / "case"
    if existing_empty:
        case_dir.mkdir()

    def fail_publish(*args, **kwargs):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "rename", fail_publish)
    with pytest.raises(OSError, match="simulated rename failure"):
        exportFoam(model, case_dir / "room.foam", **options)

    assert case_dir.exists() == existing_empty
    assert set(tmp_path.iterdir()) == ({case_dir} if existing_empty else set())
    if existing_empty:
        assert list(case_dir.iterdir()) == []


def test_user_file_created_during_export_is_preserved(models, tmp_path, monkeypatch):
    model, options = export_options(models, "mesh")
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    original_open = Path.open

    def intervening_open(path, *args, **kwargs):
        if path.name == "points":
            (case_dir / "user.txt").write_text("arrived during export")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", intervening_open)
    with pytest.raises(FileExistsError):
        exportFoam(model, case_dir / "room.foam", **options)

    assert (case_dir / "user.txt").read_text() == "arrived during export"
    assert list(case_dir.iterdir()) == [case_dir / "user.txt"]
    assert list(tmp_path.iterdir()) == [case_dir]


def test_unrelated_staging_directory_is_never_removed(models, tmp_path):
    model, options = export_options(models, "mesh")
    stale_stage = tmp_path / ".case.moosas-interrupted"
    stale_stage.mkdir()
    (stale_stage / "user.txt").write_text("keep")

    exportFoam(model, tmp_path / "case" / "room.foam", **options)

    assert (stale_stage / "user.txt").read_text() == "keep"
    assert set(tmp_path.iterdir()) == {stale_stage, tmp_path / "case"}


@pytest.mark.parametrize("dangling", [False, True])
def test_case_directory_symlink_is_not_followed(models, tmp_path, dangling):
    model, options = export_options(models, "mesh")
    user_dir = tmp_path / "user-directory"
    if not dangling:
        user_dir.mkdir()
    case_dir = tmp_path / "case"
    try:
        case_dir.symlink_to(user_dir, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Directory symlinks are unavailable: {error}")

    with pytest.raises(FileExistsError):
        exportFoam(model, case_dir / "room.foam", **options)

    assert case_dir.is_symlink()
    assert user_dir.exists() == (not dangling)
    if not dangling:
        assert list(user_dir.iterdir()) == []


def test_interrupt_after_removing_empty_destination_restores_it(models, tmp_path, monkeypatch):
    model, options = export_options(models, "mesh")
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    original_rmdir = Path.rmdir

    def interrupt_rmdir(path):
        original_rmdir(path)
        if path == case_dir:
            raise KeyboardInterrupt("interrupted publication")

    monkeypatch.setattr(Path, "rmdir", interrupt_rmdir)
    with pytest.raises(KeyboardInterrupt, match="interrupted publication"):
        exportFoam(model, case_dir / "room.foam", **options)

    assert case_dir.is_dir()
    assert list(case_dir.iterdir()) == []
    assert list(tmp_path.iterdir()) == [case_dir]


def test_simultaneous_publish_into_empty_directory_has_one_winner(models, tmp_path, monkeypatch):
    model, options = export_options(models, "mesh")
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    removing, publishing = Barrier(2), Barrier(2)
    original_rmdir, original_rename = Path.rmdir, Path.rename

    def competing_rmdir(path):
        if path == case_dir:
            removing.wait(timeout=5)
        return original_rmdir(path)

    def competing_rename(path, target):
        publishing.wait(timeout=5)
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rmdir", competing_rmdir)
    monkeypatch.setattr(Path, "rename", competing_rename)
    successes, errors = [], []
    with ThreadPoolExecutor(max_workers=2) as executor:
        pending = [executor.submit(exportFoam, model, case_dir / name, **options)
                   for name in ("first.foam", "second.foam")]
        for future in pending:
            try:
                successes.append(future.result(timeout=20))
            except Exception as error:
                errors.append(error)

    assert len(successes) == 1, errors
    assert len(errors) == 1
    result = successes[0]
    assert list(case_dir.glob("*.foam")) == [result.primary_path]
    assert all(path.is_file() for path in result.generated_paths)
    assert list(tmp_path.iterdir()) == [case_dir]
