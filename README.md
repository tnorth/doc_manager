This repository hosts scripts (and hopefully later a GUI) to manage documents, typically scanned administrative papers.

## Concept:

Hypothesis:

* The user has a paper stored as scanned tiff/png into folders and subfolders
* No OCR was used, only pure pictures, scanned at 300 dpi
* New files can be added anywhere in the tree
* Multipage documents are named foo_1.png, foo_2.png, etc.
* Usually, existing files are not modified

Needs:
* Search by keywords
* Suggest name for newly scanned documents
* Add tags. Automatically suggest tags.
* A GUI

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
