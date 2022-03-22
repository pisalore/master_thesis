## Layout generation

### Getting started

#### Installation

This project is configured using [Anaconda](https://www.anaconda.com/). Once you have installed it, run

```
conda env create -f environment.yml
```

if you are using Windows, else

```
conda env create -f environment_unix.yml
```

if you are using Linux. this command will prepare a conda environment ready to be used, with everything is needed.

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
   python pdf2xml_converter.py
   ```

#### Generating annotations

Your pdf and xml files must be saved following the same directory structure: the convention to be followed is
`pdf/<directory_id>/<paper_id>` `xml/<directory_id>/<paper_id>`. Notice that directory and paper id must be the
same.

1. Run `main.py` script

   ```
   python main.py
   ```

   You can provide some arguments:

   ```
   usage: main.py [-h] [--pdfs-path PDFS_PATH] [--xml-path XML_PATH] [--annotations-path ANNOTATIONS_PATH] [--debug DEBUG] [--load-instances LOAD_INSTANCES] --pickle-filename PICKLE_FILENAME
   -h, --help            show this help message and exit
   --pdfs-path PDFS_PATH  The path to pdfs. It must be related to an xml-path: a pdf must have a related xml.
   --xml-path XML_PATH    The path to xml. It must be related to an pdfs-path: a xml must have a related xml.
   --annotations-path ANNOTATIONS_PATH  The path where png images from pdf are saved.
   --debug DEBUG         Indicate if png images have to be annotated with annotations bounding boxes.Useful for debugging
   --load-instances LOAD_INSTANCES  The path to pickle file which contains a doc instances dictionary previously populated.Useful for split multiple computations.
   --pickle-filename PICKLE_FILENAME The pickle file name. it must end with
   ```

2. Correct annotations [labelImg](https://github.com/tzutalin/labelImg) (if needed)

   The parsing process will have generated for you an image for each paper page and an XML file with PASCAL
   VOC ANNOTATIONS ready to be consumed by lablImg. Run

   ```
   labelImg data/png/
   ```

   A GUI will be opened to fix annotations.

3. Convert from XML to JSON
   Once annotations are fixed, you must convert them from PASCAL VOC to COCO format, to use them with LayoutTransformer.
   use `converters.xml2json_labels_converter ` function `generate_json_labels(png_dir: Any) `.
   It will generate two JSON files, one for training and one for validation.

#### Layout generation

Starting from COCO annotations, you are now able to generate synthetic layouts.
Login to [WanDB](https://wandb.ai/home) if you want to monitor training, else, hit the following command to deactivate
wandb:

```
wandb off
```

1. Download [LayoutTransformer](https://github.com/kampta/DeepLayout) repository.

2. Start [LayoutTransformer](https://github.com/kampta/DeepLayout) training:

   ```
   python main.py
    --train_json /path/to/annotations/train.json
    --val_json /path/to/annotations/val.json
    --exp <exp_name>
   ```

3. Generate documents

   Using the trained model, run inference script from `lgt` module:

   ```
   inference.py [-h] --model MODEL --json-data-path JSON_DATA_PATH
                    --n-generated N_GENERATED [--debug-imgs DEBUG_IMGS]

   optional arguments:
     -h, --help            show this help message and exit
     --model MODEL         The model obtained by DeepLayout training.
     --json-data-path JSON_DATA_PATH  The path to dataset json annotations.
     --n-generated N_GENERATED The number of layouts (paper pages) to be generated
     --debug-imgs DEBUG_IMGS  A boolean which indicates if debug images must be saved
   ```

4. Generate text

   Run

   ```
   python generators/main.py
   ```

5. Generate documents

   Make sure to have a latex compiler installed on your machine.
   Run document generator:

   ```
   usage: main.py [-h] --pickle-filename PICKLE_FILENAME
               [--load-instances LOAD_INSTANCES]
               [--docs-instances DOCS_INSTANCES] [--categories CATEGORIES]
               [--orgs ORGS]

   optional arguments:
     -h, --help            show this help message and exit
     --pickle-filename PICKLE_FILENAME The pickle file name. it must end with .pickle
     --load-instances LOAD_INSTANCES The path to pickle file which contains generated text
                           instances dictionary previously created.Useful for
                           split multiple computations.
     --docs-instances DOCS_INSTANCES he parsed doc instances.
     --categories CATEGORIES The categories of text to be generated. For
                           organizations, use the related list variable.
     --orgs ORGS           The categories of text to be generated. For
                           organizations, use the related list variable.
   ```

   Then, run document generator:

   ```
   python doclab/doc_generator.py
   ```

   It will generate fake PDFS and their PNG counterpart following the layouts created by LayoutTransformer.

#### Evaluation
   You can check how a ResNeXt performs using your synthetic dataset. Split your data using
   `converters.xml2json_labels_converter ` function `generate_json_labels(png_dir: Any) ` again, then you can download
   [DocBank weights for X101](https://layoutlm.blob.core.windows.net/docbank/model_zoo/X101.zip) and fineutine the network
   with them:

   ```
   python X101/x101_finetuning.py
   ```

   Then test

   ```
   python X101/x101_inference.py
   ```
