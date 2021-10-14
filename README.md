## Layout generation

### Getting started

#### Generating xml from PDFs

XML jointly with PDF are necessary for layout analysis. Supposing you have Docker installed and working on your local
setup, and you have a pdf/ directory inside this repository:

1. Install `Grobid` via Docker Hub
    ```shell
    docker pull grobid/grobid:0.7.0
    ```
2. Run Grobid service
   ```shell
   docker run -t --rm --init -p 8070:8070 lfoppiano/grobid:0.7.0
   ```
3. Run `pdf2xml.py`; it will generate XML files related to PDF, a log file and a txt for further work:
   ```shell
   python pdf2xml.py
   ```