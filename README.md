This repository hosts scripts (and hopefully later a GUI) to manage documents, typically scanned administrative papers.

# Concepts:

There are two main distinct workflows:

## When scanned document already exist and are placed in folders and subfolders

Hypothesis:

* The user has a paper stored as scanned tiff/png into folders and subfolders
* No OCR was used, only pure pictures, scanned at 300 dpi
* New files can be added anywhere in the tree
* Multipage documents are named foo_1.png, foo_2.png, etc.
* Usually, existing files are not modified

Needs:

* OCR images
* Group them when possible to generate a single PDF
* Index them and enable searches
* A GUI to display them, add tags, etc

## When documents already exist (case above), and new ones are scanned in batch to a dump folder

Hypothesis:

* Images are scanned in batch with an Automatic Document feeder (ADF). In this case, contrary to programs such as Paperwork, the focus is not on the scanning (considered a solved problem), but the organization of documents in the existing filesystem layout.
* Scanned images are always deposited in a folder, for instance `doc_dump/`
* Existing stored documents are placed in a directory structure that the user can browse with his file explorer, with (sub-)directory names that make sense.
* Scanned documents are image with computer-generated filenames, depending on the scanning software.

Needs:

* Text of each image is OCRed
* Based on the existing database of documents, a location in the hierarchy is suggested via a Bayesian classifier.
* Potentially, labels are suggested, based on the content of the document and labels of nearby documents.
* A name must be picked. Suggestions can be made.
* Multipage documents can be grouped. Automatic suggestion can be made via a classifier.
* Destination folder and names are selectable and the file is moved there.

## Implementation

* First workflow requires a command-line tool only.
* Second workflow requires a GUI.


## GUI description

### Adding newly scanned documents

* The document hierarchy on disk is shown, and is browseable
* The `doc_dump` folder can be loaded. In this case, all images belonging to the folder are shown (with pan and zoom)
* OCR is applied on these images
* Images can be deleted (blank pages), moved up and down, and merged down (multipage document).
* File names and location are suggested, files can be moved and renamed.

### Browsing existing documents

* Documents can be searched (containing text), or by label
* Actual PDF is shown in a Tab. Ideally, the search keywords are highlighted

# What can these script do? (at the moment)

## Workflow 1

* Group your individual scans into multipage TIFF files
* Extract text from the images via OCR
* Store it to a database
* Use a Bayesian classifier to find proximity of a text or a document to another

## Workflow 2

* WIP

## Backend

* Use tesseract to extract text and create PDFs.
* Use pdftotext to extract the text from the OCRed PDF
* Store paths to each image file in database, along with the OCRed text

## Dependencies

* Python 3
* simplebayes
* sqlite3
* hashlib

## Example

```python 
from paperscan import PaperScan
# Assume you have a folder named PaperScan.root_dir in the script path
# This folder has subfolders with scanned documents

ps = PaperScan()
# Scan papers just returns present images and missing PDFs.
# it also creates multipage TIFF images from image series.
pdfs, imgs, missing = ps.scan_papers()

# make_ocr calls scan_papers to find missing PDFs.
# It creates new PDFs from these new images
# the force keyword re-executed tesseract on all documents
ps.make_ocr_pdf(force=False)

for k, pdf in enumerate(ps.walk_pdfs()):
    print("Document {}: {}".format(k, pdf))
    
import database
db = database.Database()
db.create_database(overwrite=True)
# Fill the database with all papers
for k, pdf in enumerate(ps.walk_pdfs()):
    db.add_paper(pdf)
    
# train a Bayesian classifier
import documentproximity as dp
bc = dp.DocumentProximity()
for paper in db.read_all_paper():
    bc.train(paper[1], paper[2])

import operator
# See if the last paper actually has the best match
print("Best matches for {}:".format(paper[1]))
scores = bc.get_score(paper[2])
sorted_scores = sorted(scores.items(), key=operator.itemgetter(1))
print(sorted_scores[::-1])
```
