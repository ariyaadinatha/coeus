# coeus

Coeus is a static analysis tools made for final thesis capstone project

## Description

Static analysis tools that able to perform static analysis for multiple programming language and find 4 types vulnerabilities
* Dependency vulnerability
* Injection vulnerability
* Session and control vulnerability
* Secret detection

## Getting Started

### Dependencies

* Python3
* requests
* tree-sitter

### Installing

* Clone and navigate into the repository
```
git clone git@github.com:ariyaadinatha/coeus.git
cd coeus
```
* Create environtment and install required dependencies
```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
* Create folder named `vendor` inside `src`
```
mkdir src/vendor
```
* Clone tree-sitter implementation for python, php, java, javascript on `vendor`
```
git clone https://github.com/tree-sitter/tree-sitter-python src/vendor/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-java src/vendor/tree-sitter-java
git clone https://github.com/tree-sitter/tree-sitter-javascript src/vendor/tree-sitter-javascript
git clone https://github.com/tree-sitter/tree-sitter-php src/vendor/tree-sitter-php
```

### Executing program

* Navigate inside `src` folder
```
cd src
```
* Run `main.py`
```
python3 main.py
```

## Help

Any advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Contributors names and contact info

Ariya Adinatha


## Acknowledgments

Inspiration, code snippets, etc.
* [tree-sitter](https://github.com/tree-sitter/tree-sitter)
