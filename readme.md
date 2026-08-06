# Project Path Configuration

This project uses relative paths based on the project root directory. 

In most cases, if the project is opened directly from an IDE (e.g. VS Code, PyCharm) or executed from the project root directory, no additional path configuration is required.

If the execution environment cannot automatically recognize the project root directory (e.g. Google Colab, external Python execution, or running scripts from outside the project directory), you may need manually initialize the project path before running the project.

Manually initialize the project path:

## Windows (PowerShell / CMD)

### 1. Enter the project root directory

````powershell
cd <PROJECT_ROOT>
````

Example:

````powershell
cd D:/your/path/to/project_qmy
````

### 2. Initialize Python module path

````powershell
python -c "from core.path_manager import setup_python_path; setup_python_path()"
````

## Linux / WSL2 / Docker / Google Colab

### 1. Enter the project root directory

````bash
cd <PROJECT_ROOT>
````

Example:

````bash
cd /your/path/to/project_qmy
````

### 2. Initialize Python module path

````powershell
python -c "from core.path_manager import setup_python_path; setup_python_path()"
````

# Environment Setup
Please ensure that Python 3.12 or higher is installed.

Please install all Python dependencies listed in `requirements.txt`.

Install Python dependencies according to your environment (After entering the project root directory):

## Windows (PowerShell / CMD)

````powershell
pip install -r requirements.txt
````

## Linux / WSL2 / Docker / Google Colab

````bash
pip install -r requirements.txt
````

After installing the Python dependencies, the environment is not yet fully
prepared. Some tools used in this project require system-level additional resources that cannot be installed through `pip`. 

The following additional setup steps are required:

- spaCy language models
- VecAlign additional dependencies

---

## 1. spaCy Language Model Installation

The `spacy` Python package does not include language models. Download the required language models separately.

### Windows (PowerShell / CMD)

````powershell
python -m spacy download zh_core_web_sm
python -m spacy download es_core_news_sm
````

### Linux / WSL2 / Docker / Google Colab

````bash
python -m spacy download zh_core_web_sm
python -m spacy download es_core_news_sm
````

---

## 2. VecAlign Installation Requirements

VecAlign requires a C++ compiler environment.

### Windows

Install Microsoft C++ Build Tools:

https://visualstudio.microsoft.com/visual-cpp-build-tools/

During installation, make sure that the following component is selected:

- Desktop development with C++

---

### Linux / WSL2 / Docker / Google Colab

Install the required C++ build tools:

Ubuntu:

````bash
sudo apt update
sudo apt install build-essential
````

For other Linux distributions, install the equivalent packages:

- GCC / G++
- Make
- Standard C++ development libraries

---

# Usage Guide

---

## 1. Project entry points

There are two kinds of project entry points:

---

### 1.1 Jupyter Notebook-based execution

In the `notebooks` directory, there are multiple Jupyter Notebook files that serve as entry points for different cases of the project. Users can open these notebooks in a Jupyter environment and execute them step by step.

These notebooks are designed for demonstration and reproducibility. Users who want to integrate individual modules into other Python projects should use the scripts interface instead.

| File | Purpose|
|--------------------|----------------|
| `colab_full_project_on_driver.ipynb` | Upload the project structure on your Google Drive and excute the project in Colab | 
| `colab_git_clone_and_data_on_driver.ipynb` | Git Clone the project structure on your Colab, and link some directory with Google Drive (Optional) |

---

### 1.2 Script-based execution

In the `scripts` directory, there are multiple python excutable files that serve as entry points for different stages of the project. Users can execute these these documents in a python environment, o integrate individual modules into other Python projects(you may need redesign some parts).

The scripts folder provides the recommended entry points. Internal implementation modules are located in src/.

| File | Purpose |
|--------------------|----------------|
| `page_mining_runner.py` | Web page crawling, rendering, alignment, and text segementation to sentences for each page | 
| `corpus_constr_runner.py` | Sentences alignment, filtering, cleaning, deduplication |
| `corpus_evalua_runner.py` | Evaluate the corpus quality by blue and manual check |

---

## 2. Configuration customization

All configurable parameters are stored in the `config` directory.

Users can modify YAML files according to their requirements before execution.

In this directory, `config.yaml` corresponds the general configration in the `core` directory; for other configuration documents, each YAML file corresponds to one sub-directory (which means a sub-module) in `src` directory; urls.txt is for store the inicial websites for web page mining.

| Configuration file | Related module | Module description |
|--------------------|----------------|------------------- |
| `config.yaml` | `core` | None | General Configuration |
| `crawler_config.yaml` | `src/crawler` | Web page crawling and rendering |
| `align_page_config.yaml` | `src/align_page` | Page Alignment |
| `parser_lid_config.yaml` | `src/parser_lid` | Extraction of contents and language identification of web pages |
| `segmentator_config.yaml` | `src/segmentator` | Segementation to sentences for each page |
| `sentence_align_config.yaml` | `src/sentence_align` | Sentences alignment |
| `corpus_biuld_config.yaml` | `src/corpus_biuld` | Preparation of corpus before filtering, cleaning and deduplication |
| `stati_filter_config.yaml` | `src/stati_filter` | Filter of statistic |
| `lid_filter_config.yaml` | `src/lid_filter` | Filter of language identification |
| `perplex_filter_config.yaml` | `src/perplex_filter` | Filter of perplexity or pseudo-perplexity |
| `deduplicator_config.yaml` | `src/deduplicator` | Corpus deduplication |
| `corpus_publi_config.yaml` | `src/corpus_publi` | Final corpus output |
| `evaluator_config.yaml` | `src/evaluator` | Evaluator of the corpus |

---

## 3. Source code customization

The project provides an option to skip the web page mining stage by directly using a document-level aligned corpus and converting it into a sentence-level corpus. (Skip the `Web page mining` block in Jupyter Notebook-based execution, or do not execute `page_mining_runner.py` in script-based execution.) 

Besides, the corpus evaluation stage requires a user-provided reference corpus and a user-provided test corpus to evaluate corpus quality. (It can also be skipped: Skip the block `Corpus evaluation` in the notebook for jupyter Notebook-based execution, or not excuting `corpus_evalua_runner.py` for script-based execution) 

However, different corpora may have different data structures. 

Therefore, some modules can be created or modified as customizable components because they depend on user-specific raw data structures:

---

### 3.1 Skip the web page mining stage：

---

#### Create new modules:

- `src/sentence_align/page_selector_<...>.py` (See the corresponding configuration file for detailed instructions.)
- `src/sentence_align/page_<...>_<...>.py` (See the corresponding configuration file for detailed instructions.)
- `src/sentence_align/extract_<...>_<...>.py` (See the corresponding configuration file for detailed instructions.)

#### Modify existing modules:

- `src/sentence_align/sentence_align_runner.py` (Only customize the function call related to `src/sentence_align/page_selector_<...>.py`, `src/sentence_align/page_<...>_<...>.py` and `src/sentence_align/extract_<...>_<...>.py`)

#### Create new modules:

- `src/corpus_biuld/corpus_biuld_<...>_<...>.py` (See the corresponding configuration file for detailed instructions.)
- `src/corpus_biuld/corpus_biuld_<...>_<...>.py` (See the corresponding configuration file for detailed instructions.)

#### Modify existing modules:

- `src/corpus_biuld/corpus_biuld_runner.py` (Only customize the function call related to `src/corpus_biuld/corpus_biuld_<...>_<...>.py` and `src/corpus_biuld/corpus_biuld_<...>_<...>.py`)

---

### 3.2 Adapt modules for user-provided corpora in corpus evaluation

---

#### Modify existing modules:

- `src/evaluator/sample_corpus_refer.py`
- `src/evaluator/sample_corpus_test.py`

See more information in the part: 4.2 Relationship with the Sectinon 3. Source code customization

---

## 4. Data preparation

In the `data` directory:

---

### 4.1 User-provided data directories

The `external` and `corpus_test` directories store user-provided external language resources.
Users should place their own datasets here before execution, and modify the corresponding configuration files to link them to the project. 

| Directory | Purpose |
|--------------------|----------------|
| `external` | Externally downloaded bilingual document-level aligned corpus (optional) and externally downloaded bilingual reference corpus | 
| `corpus_test` | Bilingue test corpus, it should be smaller the final corpus, but should be a 100% correctly aligned sentence-level corpus |

---

### 4.2 Relationship with the Sectinon 3. Source code customization

As described in Section 3. Source code customization, users can either adapt the source code, or transform their datasets into the following default format:

---

#### 4.2.1 Execution skipping the stage of web page mining：

##### Externally downloaded bilingual document-level aligned corpus:

Default input schema: refer to the file structure of the XML files option provided by the UN Corpus:

https://www.un.org/dgacm/en/content/uncorpus/Download

---

#### 4.2.2 Adaption for user-provided corpus for the stage of corpus evaluation

##### Outside downloaded bilingue reference corpus
Default input schema: TMX document structure (partial example):

````tmx
<?xml version="1.0" encoding="UTF-8" ?>
<tmx version="1.4">
<header creationdate="Wed Jul 24 05:08:28 2019"
          srclang="es"
          adminlang="es"
          o-tmf="unknown"
          segtype="sentence"
          creationtool="Uplug"
          creationtoolversion="unknown"
          datatype="PlainText" />
  <body>
    <tu>
      <tuv xml:lang="es"><seg>RESOLUCIÓN 918 (1994)</seg></tuv>
      <tuv xml:lang="zh"><seg>第918(1994)号决议</seg></tuv>
    </tu>
    <tu>
      <tuv xml:lang="es"><seg>Aprobada por el Consejo de Seguridad en su 3377ª sesión, celebrada el 17 de mayo de 1994</seg></tuv>
      <tuv xml:lang="zh"><seg>1994年5月17日安全理事会第3377次会议通过</seg></tuv>
    </tu>
    ...
````

##### Bilingue test corpus

Default input schema: see `schema/corpus_publi` in the project.

---

### 4.3 Internal directories

Those directories not mentioned in the part 4.1 nor 4.2 are managed by the pipeline.
Users normally should not manually modify their contents.

---

## 5. Run outputs and results

Each sub-directory in the `run` directory stores the outputs generated by one execution of a Python script in the `scripts` directory. Therefore, if you execute all three stages (for example, when you execute the`Web page mining`, `Corpus construction`, and `Corpus evaluation` blocks in the notebook), three corresponding sub-directories will be generated.

Each generated sub-directory contains:

- Snapshots of configuration files
- Backups of generated data (excluding `data/external` and `data/corpus_test`)
- Execution logs 

Run result data:
| Stage | Result data directory | Data schema |
|---------------|--------------------------|----------------------------------------|
| Web page mining | Not directly stored | None |
| Corpus construction | `data/corpus_final` | See `schema/corpus_publi` in the project |
| Corpus evaluation | `data/bleu_result` (automatically evaluated BLEU score compared with the reference corpus) | See `schema/evaluator_schema.yaml` in the project |
|  | `data/manual_check` (CSV for manual check) | Users are recommended to save a copy in XLSX format for manual review. |

---

## 6. Typical workflow

- Prepare external data
- Modify configuration files
- Customize source code modules if necessary
- Execute scripts or notebooks
- Retrieve results from run/

---

# Third-party software

This project uses:

---

## PyYAML

Used for disolve YAML cofig documents.

Citation:

Source repository:

https://github.com/yaml/pyyaml.org

---

## Scrapy

Used for web page crawling.

Citation:

````BibTex
@software{Scrapy_contributors_Scrapy,
author = {{Scrapy contributors}},
title = {{Scrapy}},
url = {https://scrapy.org}
}
````

---

## Playwright

Used for web page rendering.

Citation:

Source repository:

https://github.com/microsoft/playwright-pytest

---

## lxml

Used for web page content extraction.

Citation:

Source repository:

https://github.com/lxml/lxml

---

## langid.py

Used for text language detection.

Citation:

Source repository:

https://github.com/saffsd/langid.py

---

## sentence-transformers

Used for text language detection.

Citation:

````BibTex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
````

---

## scipy

Used for math calculation.

Citation:

Source repository:

https://github.com/scipy/scipy

---

## numpy

Used for math calculation.

Citation:

Source repository:

https://github.com/numpy/numpy

---

## spaCy

Used for text segmentation to sentences.

The following pretrained models are used:

- `zh_core_web_sm`
- `es_core_news_sm`

Citation:

Source repository:

https://github.com/explosion/spaCy

Model references:

- Chinese pipeline:
  `zh_core_web_sm`

- Spanish pipeline:
  `es_core_news_sm`

Source:
https://spacy.io/models

---

## Vecalign

Used for senteces alignment.

Citation:

````BibTex
@inproceedings{thompson-koehn-2019-vecalign,
    title = "{V}ecalign: Improved Sentence Alignment in Linear Time and Space",
    author = "Thompson, Brian and Koehn, Philipp",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)",
    month = nov,
    year = "2019",
    address = "Hong Kong, China",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/D19-1136",
    doi = "10.18653/v1/D19-1136",
    pages = "1342--1348",
}
````

---

## Cython

Used for serving as dependency of Vecalign.

Citation:

Source repository:

https://github.com/cython/cython

---

## PyTorch

Used for serving as dependency of multiple liabrarys and math calculation.

Citation:

Source repository:

https://github.com/pytorch/pytorch

---

## Tranformers

Used for import language-model for perplexity o pseudo perplexity calculation.

The following pretrained model is used:

- `paraphrase-multilingual-mpnet-base-v2`

Citation:

Source repository:

https://github.com/huggingface/transformers?tab=contributing-ov-file

Model references:

- `paraphrase-multilingual-mpnet-base-v2`

Source:
https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2

---

## Hugging Face Hub

Used for serving as dependency of Tranformers.

The following pretrained model is used:

- `hfl/chinese-bert-wwm-ext`

- `dccuchile/bert-base-spanish-wwm-cased`

Citation:

Source repository:

https://github.com/huggingface/transformers?tab=contributing-ov-file

Model references:

Source:

- `hfl/chinese-bert-wwm-ext`

````BibTex
@inproceedings{CaneteCFP2020,
  title={Spanish Pre-Trained BERT Model and Evaluation Data},
  author={Cañete, José and Chaperon, Gabriel and Fuentes, Rodrigo and Ho, Jou-Hui and Kang, Hojin and Pérez, Jorge},
  booktitle={PML4DC at ICLR 2020},
  year={2020}
}
````

- `hfl/chinese-bert-wwm-ext`

````BibTex
@inproceedings{cui-etal-2020-revisiting,
    title = "Revisiting Pre-Trained Models for {C}hinese Natural Language Processing",
    author = "Cui, Yiming  and
      Che, Wanxiang  and
      Liu, Ting  and
      Qin, Bing  and
      Wang, Shijin  and
      Hu, Guoping",
    booktitle = "Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: Findings",
    month = nov,
    year = "2020",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/2020.findings-emnlp.58",
    pages = "657--668",
}
````