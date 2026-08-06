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
cd D:\your\path\to\project_qmy
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