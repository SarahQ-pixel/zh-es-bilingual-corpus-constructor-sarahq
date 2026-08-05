# Project Path Configuration

This project uses relative paths based on the project root directory. 

For example:

project_qmy/
├── core/
├── config/
├── data/
├── src/
└── scripts/

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

## <Third-party software name>

Used for <Third_party software's usement>.

Cite:

<reference>
