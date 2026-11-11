from pathlib import Path
import subprocess
import sys
from collections import Counter
import re
import argparse

ADITION_EVAL_DIR = Path(__file__).resolve().parent
VECALIGN_REPO_DIR = ADITION_EVAL_DIR / "vecalign-main"
VENV_DIR = ADITION_EVAL_DIR / ".venv"

VECALIGN_URL = "https://github.com/thompsonb/vecalign.git"
REQUIRED_IMPORTS = (
    "vecalign.dp_core",
    "sentence_transformers",
    "pandas",
)

BLEUALIGN_DIR = VECALIGN_REPO_DIR / "bleualign_data"

UN_OFI_LINK_GOLD_DIR = ADITION_EVAL_DIR / "un_ofi_link_gold"
UN_OFI_LINK_GOLD_VE_DIR = ADITION_EVAL_DIR / "un_ofi_link_gold_ve"
UN_OFI_TXT_ES_DIR = ADITION_EVAL_DIR / "un_ofi_txt_es"
UN_OFI_TXT_ZH_DIR = ADITION_EVAL_DIR / "un_ofi_txt_zh"
UN_OFI_XML_ES_DIR = ADITION_EVAL_DIR / "un_ofi_xml_es"
UN_OFI_XML_ZH_DIR = ADITION_EVAL_DIR / "un_ofi_xml_zh"
PIPELINE_ALIGN_DIR = ADITION_EVAL_DIR / "pipeline_align"
PIPELINE_ALIGN_VE_DIR = ADITION_EVAL_DIR / "pipeline_align_ve"
DISCREPANCY_DIR = ADITION_EVAL_DIR / "discrepancy"
BASELINE_LENGTH_DIR = ADITION_EVAL_DIR / "baseline_length"
ZH_LINES_DIR = ADITION_EVAL_DIR / "lines_zh"
ES_LINES_DIR = ADITION_EVAL_DIR / "lines_es"

# Complite information for each pair
UN_OFI_LINK_GOLD_DOC = ".lnk"
PIPELINE_ALIGN_DOC = ".jsonl"
UN_OFI_XML_ES_DOC = ".xml"
UN_OFI_XML_ZH_DOC = ".xml"


def preparar_venv_python():
    """Return the Python executable in the dedicated virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def colonar_vecalign():
    """Clone Vecalign if the repository is not present."""
    if VECALIGN_REPO_DIR.exists():
        if not (VECALIGN_REPO_DIR / ".git").exists():
            raise RuntimeError(
                f"The directory exists but is not a Git repository: "
                f"{VECALIGN_REPO_DIR}"
            )
        return

    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            VECALIGN_URL,
            str(VECALIGN_REPO_DIR),
        ],
        check=True,
    )


def crear_env_virtual():
    """Create the dedicated virtual environment if necessary."""
    venv_python = preparar_venv_python()

    if venv_python.is_file():
        return venv_python

    VENV_DIR.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [sys.executable, "-m", "venv", str(VENV_DIR)],
        check=True,
    )

    if not venv_python.is_file():
        raise RuntimeError(
            f"Virtual environment creation failed: {VENV_DIR}"
        )

    return venv_python


def chequear_dependencias(venv_python):
    """Check whether all required packages can be imported."""
    check_code = "; ".join(
        f"import {module}" for module in REQUIRED_IMPORTS
    )

    result = subprocess.run(
        [str(venv_python), "-c", check_code],
        cwd=ADITION_EVAL_DIR.parent,
        check=False,
    )

    return result.returncode == 0


def instalar_dependencias(venv_python):
    """Install Vecalign and the supplementary evaluation dependencies."""
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--timeout", "120",
            "--retries", "10",
            str(VECALIGN_REPO_DIR),
        ],
        check=True,
    )

    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--timeout", "120",
            "--retries", "10",
            "sentence-transformers",
            "pandas",
        ],
        check=True,
    )


def preparar_env():
    """Ensure the repository, virtual environment, and dependencies exist."""
    colonar_vecalign()
    venv_python = crear_env_virtual()

    if not chequear_dependencias(venv_python):
        instalar_dependencias(venv_python)

    if not chequear_dependencias(venv_python):
        raise RuntimeError(
            "Vecalign or one of the required dependencies "
            "could not be imported after installation."
        )

    return venv_python


def chequear_vecalign():
    """Check the compiled Vecalign extension."""
    venv_python = preparar_env()

    subprocess.run(
        [
            str(venv_python),
            "-c",
            (
                "import vecalign.dp_core; "
                "print('dp_core compiled/imported successfully')"
            ),
        ],
        cwd=ADITION_EVAL_DIR.parent,
        check=True,
    )
    return venv_python


def ejecutar_en_venv(pipeline_name):
    """
    Run a pipeline in the dedicated virtual environment.
    Return True if the pipeline was launched in a subprocess.
    Return False if the current interpreter already uses the venv.
    """
    venv_python = chequear_vecalign()

    current_env = Path(sys.prefix).resolve()
    target_env = VENV_DIR.resolve()

    # Continue directly if the current process already uses this venv.
    if current_env == target_env:
        return False

    # Launch the requested pipeline in the dedicated environment.
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "adition_eval.run_eval",
            "--pipeline",
            pipeline_name,
        ],
        cwd=ADITION_EVAL_DIR.parent,
        check=True,
    )

    return True


def test_referencia(python_executable=None):
    """Run the original German-French Vecalign reference test."""
    if python_executable is None:
        python_executable = sys.executable

    src_files = sorted(BLEUALIGN_DIR.glob("test*.de"))
    tgt_files = sorted(BLEUALIGN_DIR.glob("test*.fr"))
    gold_files = sorted(BLEUALIGN_DIR.glob("test*.defr"))

    # Check that the reference files are available.
    if not src_files or not tgt_files or not gold_files:
        raise FileNotFoundError(
            f"Vecalign reference files not found in: {BLEUALIGN_DIR}"
        )

    src_embed = BLEUALIGN_DIR / "overlaps.de"
    src_embed_data = BLEUALIGN_DIR / "overlaps.de.emb"
    tgt_embed = BLEUALIGN_DIR / "overlaps.fr"
    tgt_embed_data = BLEUALIGN_DIR / "overlaps.fr.emb"

    for input_path in (
        src_embed,
        src_embed_data,
        tgt_embed,
        tgt_embed_data,
    ):
        if not input_path.is_file():
            raise FileNotFoundError(
                f"Vecalign reference embedding file not found: {input_path}"
            )

    command = [
        str(python_executable),
        "-m",
        "vecalign.vecalign",
        "--alignment_max_size",
        "8",
        "--src",
        *[str(path) for path in src_files],
        "--tgt",
        *[str(path) for path in tgt_files],
        "--gold",
        *[str(path) for path in gold_files],
        "--src_embed",
        str(src_embed),
        str(src_embed_data),
        "--tgt_embed",
        str(tgt_embed),
        str(tgt_embed_data),
    ]

    subprocess.run(
        command,
        cwd=ADITION_EVAL_DIR.parent,
        stdout=subprocess.DEVNULL,
        check=True,
    )


def evaluacion_vecalign(test_path, gold_path):
    """Run a Vecalign alignment evaluation."""

    from .un_eval import puntuar, tabla_metricas

    test_path = Path(test_path)
    gold_path = Path(gold_path)

    if not test_path.is_file():
        raise FileNotFoundError(
            f"Test alignment file not found: {test_path}"
        )

    if not gold_path.is_file():
        raise FileNotFoundError(
            f"Gold alignment file not found: {gold_path}"
        )

    result = puntuar(
        test_path,
        gold_path,
    )

    metrics = tabla_metricas(result)

    print(metrics)

    return metrics

def informacion_discrepancias(
    test_path,
    gold_path,
    src_lines,
    tgt_lines,
    out_txt,
    etiqueta="",
):
    """Construct information of discrepancies between a test and gold alignment."""

    from .un_eval import volcar_discrepancias

    test_path = Path(test_path)
    gold_path = Path(gold_path)

    if not test_path.is_file():
        raise FileNotFoundError(
            f"Test alignment file not found: {test_path}"
        )

    if not gold_path.is_file():
        raise FileNotFoundError(
            f"Gold alignment file not found: {gold_path}"
        )

    disc = volcar_discrepancias(
        test_path, gold_path,
        src_lines, tgt_lines,
        out_txt,
        etiqueta,
    )

    print(f"{len(disc)} discrepancias")
    print("por origen:", dict(Counter(d["origen"] for d in disc)))

def mostrar_discrepancias(out_txt):
    """
    Read a manually annotated discrepancy report and generate
    statistical tables based on the assigned CAUSE labels.

    Unannotated cases and unknown labels are reported separately
    and excluded from the category percentages.

    Returns:
        conteos: Number of cases for each recognized cause.
        tabla: Detailed statistical table.
        resumen: Summary grouped by attribution.
    """

    import pandas as pd
    from .un_eval import CAUSAS

    out_txt = Path(out_txt)

    if not out_txt.is_file():
        raise FileNotFoundError(
            f"Discrepancy report not found: {out_txt}"
        )

    # Define the attribution categories.
    ATRIBUCION = {
        "PIPE-SEG": "pipeline",
        "PIPE-ALIGN": "pipeline",
        "PIPE-GRAN": "pipeline",

        "REF-SEG": "referencia UNPC",
        "REF-ALIGN": "referencia UNPC",
        "REF-CONT": "referencia UNPC",

        "GRAN-COMP": "divergencia estructural",

        "TIPO-LONG": "divergencia tipológica",
        "TIPO-PUNT": "divergencia tipológica",
        "TIPO-DISC": "divergencia tipológica",

        "AMBIGUO": "indeterminado",
    }

    # Initialize all cause counts to zero.
    conteos = {
        cause: 0
        for cause in CAUSAS
    }

    casos_sin_anotar = 0
    etiquetas_desconocidas = []

    # Read and analyze the annotated TXT file.
    with out_txt.open("r", encoding="utf-8") as file:
        for line in file:
            match = re.match(
                r"^\s*CAUSE:\s*(.*?)\s*(?:NOTE:|$)",
                line,
            )

            if not match:
                continue

            cause = match.group(1).strip()

            if not cause or set(cause) == {"_"}:
                casos_sin_anotar += 1

            elif cause in conteos:
                conteos[cause] += 1

            else:
                etiquetas_desconocidas.append(cause)

    # Calculate the number of recognized annotations.
    total = sum(conteos.values()) or 1

    # Generate the detailed statistical table.
    tabla = pd.DataFrame([
        {
            "causa": cause,
            "descripción": CAUSAS[cause],
            "atribuible a": ATRIBUCION[cause],
            "casos": count,
            "%": round(100 * count / total, 1),
        }
        for cause, count in conteos.items()
    ])

    # Generate the summary grouped by attribution.
    resumen = (
        tabla.groupby("atribuible a", as_index=False)["casos"]
        .sum()
    )

    # Display the results.
    print("Tabla de tipología de errores (para la tesis):")
    print(tabla.to_string(index=False))

    print("\nResumen por atribución:")
    print(resumen.to_string(index=False))

    print("\nAnnotation status:")
    print(f"  Recognized annotations: {sum(conteos.values())}")
    print(f"  Unannotated cases:      {casos_sin_anotar}")
    print(f"  Unknown labels:         {len(etiquetas_desconocidas)}")

    if etiquetas_desconocidas:
        print("\n[WARNING] Unknown CAUSE labels detected:")
        for cause in etiquetas_desconocidas:
            print(f"  - {cause}")

    return conteos, tabla, resumen


def mostrar_descripciones(test_path, src_lines, tgt_lines):
    """
    Show descriptive statistics of the alignment by Vecalign in the pipeline.
    """

    from .un_eval import descriptivas

    d = descriptivas(test_path, len(src_lines), len(tgt_lines))
    for k, v in d.items():
        print(f"   {k:28} {v}")


def longitud_comparacion(test_path, gold_path, src_lines, tgt_lines, out_path, max_bead=2):
    """
    Show comparation with the length_only alignment result.
    """

    from .un_eval import baseline_longitud, puntuar, descriptivas

    baseline_longitud(src_lines, tgt_lines, out_path, max_bead=max_bead)

    r_pipe = puntuar(test_path, gold_path)
    r_base = puntuar(out_path, gold_path)

    print(f"{'alineador':26}{'F1 strict':>11}{'F1 lax':>10}")
    print(f"{'Vecalign (pipeline)':26}{r_pipe['f1_strict']:>11.3f}{r_pipe['f1_lax']:>10.3f}")
    print(f"{'solo longitud':26}{r_base['f1_strict']:>11.3f}{r_base['f1_lax']:>10.3f}")

    print("\ndistribución de beads de cada uno:")
    print("  Vecalign:  ", descriptivas(test_path)["beads"])
    print("  longitud:  ", descriptivas(out_path)["beads"])


# Main pipelines functions
def probar_referencia_vecalign():
    """
    Prepare the Vecalign environment and run its original reference test.
    """
    if ejecutar_en_venv("referencia"):
        return

    # Run the original German-French reference test.
    test_referencia(chequear_vecalign())
    print("Vecalign reference test completed successfully.")


def comparar_par_vecalign():
    """
    Prepare the Vecalign environment, convert one UN reference pair,
    evaluate the pipeline alignment, and analyze discrepancies.
    """

    if ejecutar_en_venv("comparar"):
        return

    from .pipeline_to_vecalign import convert_pipeline_file
    from .un_ofi_to_vecalign import convert_lnk_file

    # Ask whether to run the smoke test.
    while True:
        smoke_test_choice = input("Smoke test? Y/N: ").strip().upper()

        if smoke_test_choice in ("Y", "N"):
            break

        print("Please enter Y or N.")

    # Define the Spanish and Chinese input file paths.
    es_tei_path = UN_OFI_XML_ES_DIR / UN_OFI_XML_ES_DOC
    es_txt_path = UN_OFI_TXT_ES_DIR / Path(UN_OFI_XML_ES_DOC).with_suffix(".es")

    zh_tei_path = UN_OFI_XML_ZH_DIR / UN_OFI_XML_ZH_DOC
    zh_txt_path = UN_OFI_TXT_ZH_DIR / Path(UN_OFI_XML_ZH_DOC).with_suffix(".zh")

    # Define the UN reference alignment file paths.
    input_lnk_path = UN_OFI_LINK_GOLD_DIR / UN_OFI_LINK_GOLD_DOC

    gold_zh_es_filename = (
        Path(UN_OFI_LINK_GOLD_DOC).with_suffix(".align").name
    )

    gold_zh_es_path = UN_OFI_LINK_GOLD_VE_DIR / gold_zh_es_filename

    # Create the UN reference alignment.
    conversion_result = convert_lnk_file(
        es_tei_path,
        es_txt_path,
        zh_tei_path,
        zh_txt_path,
        input_lnk_path,
        gold_zh_es_path,
    )

    # Keep the extracted sentences in memory for discrepancy analysis.
    src_lines = conversion_result["zh_lines"]
    tgt_lines = conversion_result["es_lines"]

    # Save the extracted Chinese and Spanish sentences.
    zh_lines_filename = (
        Path(PIPELINE_ALIGN_DOC).with_suffix("").name + "_zh.txt"
    )
    es_lines_filename = (
        Path(PIPELINE_ALIGN_DOC).with_suffix("").name + "_es.txt"
    )

    zh_lines_path = ZH_LINES_DIR / zh_lines_filename
    es_lines_path = ES_LINES_DIR / es_lines_filename

    for output_path, lines in (
        (zh_lines_path, src_lines),
        (es_lines_path, tgt_lines),
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            for line in lines:
                file.write(line.rstrip("\r\n") + "\n")

    # Define the pipeline alignment file paths.
    input_jsonl = PIPELINE_ALIGN_DIR / PIPELINE_ALIGN_DOC

    test_align_filename = (
        Path(PIPELINE_ALIGN_DOC).with_suffix(".align").name
    )

    test_path = PIPELINE_ALIGN_VE_DIR / test_align_filename

    # Convert the pipeline JSONL into Vecalign alignment format.
    convert_pipeline_file(
        input_jsonl,
        test_path,
        src_file_filtro=None,
    )

    # Optionally run the smoke test.
    smoke_test_metrics = None

    if smoke_test_choice == "Y":
        print(
            "Smoke test (If all the score are 1.00, it means the test tool function is OK): \n"
        )

        smoke_test_metrics = evaluacion_vecalign(
            test_path,
            test_path,
        )

        print("\n")

        print(
            "Real Test: \n"
        )

    # Evaluate the pipeline alignment against the UN reference.
    evaluation_metrics = evaluacion_vecalign(
        test_path,
        gold_zh_es_path,
    )

    # Define the discrepancy report path.
    discrepancy_filename = (
        Path(PIPELINE_ALIGN_DOC).with_suffix(".txt").name
    )

    out_txt = DISCREPANCY_DIR / discrepancy_filename

    # Analyze discrepancies using the extracted Chinese and Spanish sentences.
    informacion_discrepancias(
        test_path,
        gold_zh_es_path,
        src_lines,
        tgt_lines,
        out_txt,
        etiqueta="",
    )

    return {
        "conversion_result": conversion_result,
        "test_path": str(test_path),
        "gold_path": str(gold_zh_es_path),
        "smoke_test_metrics": smoke_test_metrics,
        "evaluation_metrics": evaluation_metrics,
        "discrepancy_report": str(out_txt),
        "src_lines": src_lines,
        "tgt_lines": tgt_lines,
        "zh_lines_path": str(zh_lines_path),
        "es_lines_path": str(es_lines_path),
    }


def integrar_estadisticas_discrepancias():
    """
    Integrate discrepancy statistics and alignment descriptions
    using the previously generated evaluation files.
    """

    if ejecutar_en_venv("estadisticas"):
        return

    # Define the input file names.
    base_filename = Path(PIPELINE_ALIGN_DOC).with_suffix("").name

    discrepancy_path = (
        DISCREPANCY_DIR / f"{base_filename}.txt"
    )

    test_path = (
        PIPELINE_ALIGN_VE_DIR / f"{base_filename}.align"
    )

    zh_lines_path = (
        ZH_LINES_DIR / f"{base_filename}_zh.txt"
    )

    es_lines_path = (
        ES_LINES_DIR / f"{base_filename}_es.txt"
    )

    # Check that all required files exist.
    for input_path in (
        discrepancy_path,
        test_path,
        zh_lines_path,
        es_lines_path,
    ):
        if not input_path.is_file():
            raise FileNotFoundError(
                f"Required input file not found: {input_path}"
            )

    # Load the manually annotated discrepancy report.
    conteos, tabla, resumen = mostrar_discrepancias(
        discrepancy_path
    )

    # Load the Chinese and Spanish sentence lists.
    src_lines = zh_lines_path.read_text(
        encoding="utf-8"
    ).splitlines()

    tgt_lines = es_lines_path.read_text(
        encoding="utf-8"
    ).splitlines()

    # Display descriptive statistics of the pipeline alignment.
    mostrar_descripciones(
        test_path,
        src_lines,
        tgt_lines,
    )

    return {
        "discrepancy_path": str(discrepancy_path),
        "test_path": str(test_path),
        "zh_lines_path": str(zh_lines_path),
        "es_lines_path": str(es_lines_path),
        "src_lines": src_lines,
        "tgt_lines": tgt_lines,
        "conteos": conteos,
        "tabla": tabla,
        "resumen": resumen,
    }

def comparar_baseline_longitud():
    """
    Compare the Vecalign alignment with a length-based baseline.
    """

    if ejecutar_en_venv("baseline"):
        return

    # Define the input file names.
    base_filename = Path(PIPELINE_ALIGN_DOC).with_suffix("").name

    # Define the pipeline alignment file.
    test_path = (
        PIPELINE_ALIGN_VE_DIR / f"{base_filename}.align"
    )

    # Define the UN reference alignment file.
    gold_filename = (
        Path(UN_OFI_LINK_GOLD_DOC).with_suffix(".align").name
    )

    gold_path = UN_OFI_LINK_GOLD_VE_DIR / gold_filename

    # Define the sentence files.
    zh_lines_path = (
        ZH_LINES_DIR / f"{base_filename}_zh.txt"
    )

    es_lines_path = (
        ES_LINES_DIR / f"{base_filename}_es.txt"
    )

    # Define the length-based baseline output file.
    out_path = (
        BASELINE_LENGTH_DIR / f"{base_filename}_length.align"
    )

    # Check that all required input files exist.
    for input_path in (
        test_path,
        gold_path,
        zh_lines_path,
        es_lines_path,
    ):
        if not input_path.is_file():
            raise FileNotFoundError(
                f"Required input file not found: {input_path}"
            )

    # Load the Chinese and Spanish sentence lists.
    src_lines = zh_lines_path.read_text(
        encoding="utf-8"
    ).splitlines()

    tgt_lines = es_lines_path.read_text(
        encoding="utf-8"
    ).splitlines()

    # Compare Vecalign with the length-based baseline.
    longitud_comparacion(
        test_path,
        gold_path,
        src_lines,
        tgt_lines,
        out_path,
        max_bead=2,
    )

    return {
        "test_path": str(test_path),
        "gold_path": str(gold_path),
        "zh_lines_path": str(zh_lines_path),
        "es_lines_path": str(es_lines_path),
        "baseline_path": str(out_path),
        "src_lines": src_lines,
        "tgt_lines": tgt_lines,
    }


def ejecutar_pipeline(pipeline_name):
    """Dispatch the requested pipeline."""
    pipelines = {
        "referencia": probar_referencia_vecalign,
        "comparar": comparar_par_vecalign,
        "estadisticas": integrar_estadisticas_discrepancias,
        "baseline": comparar_baseline_longitud,
    }

    if pipeline_name not in pipelines:
        raise ValueError(f"Unknown pipeline: {pipeline_name}")

    return pipelines[pipeline_name]()


def main():
    """Run a pipeline requested through the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pipeline",
        required=True,
        choices=[
            "referencia",
            "comparar",
            "estadisticas",
            "baseline",
        ],
    )
    args = parser.parse_args()

    ejecutar_pipeline(args.pipeline)


if __name__ == "__main__":
    main()