from pathlib import Path
import sys
import logging as python_logging


class TeeStream:
    def __init__(self, original_stream, log_file):
        self.original_stream = original_stream
        self.log_file = log_file

    def write(self, message):
        self.original_stream.write(message)
        self.log_file.write(message)

    def flush(self):
        self.original_stream.flush()
        self.log_file.flush()


def setup_logging(log_path):
    log_path = Path(log_path)

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = open(
        log_path,
        "a",
        encoding="utf-8",
    )

    sys.stdout = TeeStream(
        sys.stdout,
        log_file,
    )

    sys.stderr = TeeStream(
        sys.stderr,
        log_file,
    )

    python_logging.basicConfig(
        level=python_logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            python_logging.StreamHandler(sys.stdout),
            python_logging.FileHandler(
                log_path,
                encoding="utf-8",
            ),
        ],
    )


def close_logging():
    if isinstance(sys.stdout, TeeStream):
        sys.stdout.log_file.close()
        sys.stdout = (
            sys.stdout.original_stream
        )

    if isinstance(sys.stderr, TeeStream):
        sys.stderr = (
            sys.stderr.original_stream
        )