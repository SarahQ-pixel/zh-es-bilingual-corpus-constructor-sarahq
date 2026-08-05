from src.crawler.crawler_runner_b import crawler_runner_b
from src.parser_lid.parser_lid_runner import parser_lid_runner
from src.align_page.align_page_runner import align_page_runner
from src.segmentator.segmentator_runner import segmentator_runner

from core.run_manager import create_run, backup_data
from core.logging import setup_logging, close_logging
from core.data_clean_page_mining import data_clean


def page_mining_runner():
    run_context = create_run(
        runner_name="page_mining_runner"
    )
    setup_logging(
        run_context["log_path"]
    )

    try:
        print("===== Page Mining Pipeline Started =====")

        data_clean()

        print("===== Data Initialized =====")

        crawler_runner_b()

        parser_lid_runner()

        align_page_runner()

        segmentator_runner()

        print("===== Page Mining Pipeline Finished =====")

        backup_data(
            run_context
        )

    finally:
        close_logging()


if __name__ == "__main__":
    page_mining_runner()