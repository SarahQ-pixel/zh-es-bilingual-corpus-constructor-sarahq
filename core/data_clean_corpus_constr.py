from pathlib import Path


EXEMPT_PATHS = [
    "data/external",
    "data/align_pages",
    "data/extracted_pages",
    "data/pages_chunked",
    "data/raw_html",
    "data/rendered_html",
    "data/segmentated_pages",
    "data/corpus_test",
]


def get_project_root():
    return Path(__file__).resolve().parents[1]


def get_exempt_paths():
    project_root = get_project_root()
    return [
        project_root / Path(path)
        for path in EXEMPT_PATHS
    ]


def is_exempt(path, exempt_paths):
    for exempt_path in exempt_paths:
        try:
            path.relative_to(exempt_path)
            return True
        except ValueError:
            continue

    return False


def clean_files(root_path):
    exempt_paths = get_exempt_paths()

    for current_path in root_path.rglob("*"):
        if is_exempt(current_path, exempt_paths):
            continue
        if current_path.is_file():
            current_path.unlink()


def data_clean():
    project_root = get_project_root()

    data_path = project_root / "data"

    if not data_path.exists():
        return

    clean_files(data_path)