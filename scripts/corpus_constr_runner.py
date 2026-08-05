from src.sentence_align.sentence_align_runner import sentence_align_runner
from src.corpus_biuld.corpus_biuld_runner import corpus_biuld_runner
from src.stati_filter.stati_filter_runner import stati_filter_runner
from src.perplex_filter.perplex_filter_runner import perplex_filter_runner
from src.deduplicator.deduplicator_runner import deduplicator_runner
from src.corpus_publi.corpus_publi_runner import corpus_publi_runner
from src.lid_filter.lid_filter_runner import lid_filter_runner

from core.run_manager import create_run, backup_data
from core.logging import setup_logging, close_logging
from core.data_clean_corpus_constr import data_clean


def corpus_constr_runner():
    run_context = create_run(
        runner_name="corpus_constr_runner"
    )
    setup_logging(
        run_context["log_path"]
    )

    try:
        print("===== Corpus Construction Pipeline Started =====")

        data_clean()

        print("===== Data Initialized =====")

        sentence_align_runner()

        corpus_biuld_runner()

        stati_filter_runner()

        lid_filter_runner()

        perplex_filter_runner()

        deduplicator_runner()

        corpus_publi_runner()

        print("===== Corpus Construction Pipeline Finished =====")

        backup_data(
            run_context
        )

    finally:
        close_logging()


if __name__ == "__main__":
    corpus_constr_runner()