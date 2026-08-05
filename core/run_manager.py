from pathlib import Path
from datetime import datetime
import shutil
import json


def get_project_root():
    return Path(__file__).resolve().parents[1]


def generate_run_id(runner_name):
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"{runner_name}_{timestamp}"


def create_run_directory(runner_name):
    project_root = get_project_root()

    run_id = generate_run_id(runner_name)

    run_dir = (
        project_root
        / "run"
        / run_id
    )

    config_dir = run_dir / "config"
    data_dir = run_dir / "data"
    logs_dir = run_dir / "logs"

    config_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    logs_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "config_dir": config_dir,
        "data_dir": data_dir,
        "logs_dir": logs_dir,
        "log_path": logs_dir / "run.log",
    }


def backup_config(run_context):
    project_root = get_project_root()

    source = (
        project_root
        / "config"
    )

    target = (
        run_context["config_dir"]
    )

    if not source.exists():
        return

    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
    )


EXEMPT_PATHS = [
    "data/external",
]


def get_backup_ignore_paths():
    ignore_paths = []

    for path in EXEMPT_PATHS:
        path = Path(path)
        parts = path.parts
        if len(parts) > 1 and parts[0] == "data":
            ignore_paths.append(
                Path(*parts[1:])
            )

    return ignore_paths


def backup_data(run_context):
    project_root = get_project_root()

    source = (
        project_root
        / "data"
    )

    target = (
        run_context["data_dir"]
    )

    if not source.exists():
        return

    ignore_paths = get_backup_ignore_paths()

    def ignore_function(directory, contents):
        ignored = []
        directory = Path(directory)
        for item in contents:
            item_path = (
                directory
                / item
            )
            relative_path = (
                item_path.relative_to(source)
            )
            for ignore_path in ignore_paths:
                if (
                    relative_path == ignore_path
                    or ignore_path in relative_path.parents
                ):
                    ignored.append(item)
                    break

        return ignored

    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=ignore_function,
    )


def save_run_metadata(run_context,extra_info=None):
    metadata = {
        "run_id": run_context["run_id"],
        "run_dir": str(
            run_context["run_dir"]
        ),
    }

    if extra_info:
        metadata.update(
            extra_info
        )

    metadata_path = (
        run_context["run_dir"]
        / "metadata.json"
    )

    with open(metadata_path,"w",encoding="utf-8",) as f:
        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False,
        )


def create_run(
    runner_name,
):
    run_context = (
        create_run_directory(
            runner_name
        )
    )

    backup_config(
        run_context
    )

    save_run_metadata(
        run_context
    )

    return run_context