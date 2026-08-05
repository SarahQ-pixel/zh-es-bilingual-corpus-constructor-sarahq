from src.evaluator.evaluator_runner import evaluator_runner

from core.run_manager import create_run, backup_data
from core.logging import setup_logging, close_logging
from core.data_clean_corpus_evalua import data_clean


def corpus_evalua_runner():
    run_context = create_run(
        runner_name="corpus_evalua_runner"
    )
    setup_logging(
        run_context["log_path"]
    )

    try:
        print("===== Corpus Evaluation Pipeline Started =====")

        data_clean()

        print("===== Data Initialized =====")

        evaluator_runner()

        print("===== Corpus Evaluation Pipeline Finished =====")

        backup_data(
            run_context
        )

    finally:
        close_logging()


if __name__ == "__main__":
    corpus_evalua_runner()