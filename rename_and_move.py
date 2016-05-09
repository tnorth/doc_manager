#!/usr/bin/python3

import os
import argparse
import database
import operator
import documentproximity as dp

from paperscan import PaperScan
from subprocess import Popen, PIPE
from collections import Counter

if __name__ == "__main__":
    # Assume the script is run in the document dump folder
    
    
    parser = argparse.ArgumentParser(description='Add newly scanned documents')
    parser.add_argument('--db', help='Path to an existing database of papers')
    args = parser.parse_args()
    
    ps = PaperScan(root_dir=os.getcwd())
    # Scan papers just returns present images and missing PDFs.
    # it creates multipage TIFF images from image series.
    pdfs, imgs, missing = ps.scan_papers()

    # make_ocr calls scan_papers to find missing PDFs.
    # It creates new PDFs from these new images
    ps.make_ocr_pdf(force=False)

    # Open the existing database for comparison
    db = database.Database(args.db)
    # Train 
    print("Training existing DB...")
    bc = dp.DocumentProximity()
    for paper in db.read_all_paper():
        bc.train(paper[1], paper[2])

    for k, pdf in enumerate(ps.walk_pdfs()):
        print("New document {}: {}".format(k, pdf))
        # Get proximity to existing documents of the DB
        # Extract text
        p = Popen(['pdftotext', pdf, '-'], 
                  stdin=PIPE, stdout=PIPE, stderr=PIPE)
        text, err = p.communicate(b"")
        rc = p.returncode
        scores = bc.get_score(text)
        print("Path suggestion:")
        #print(scores)
        folders = [(os.path.sep.join(ppath.split(os.path.sep)[:-1]), score) for ppath, score in scores.items()]
        scores_per_folder = {}
        for folder, score in folders:
            if not folder in scores_per_folder:
                scores_per_folder[folder]=score
            else:
                scores_per_folder[folder]+=score
        sorted_scores_per_folder = sorted(scores_per_folder.items(), key=operator.itemgetter(1))[::-1]
        for kk, (fd, score) in enumerate(sorted_scores_per_folder):
            if kk > 3: break
            print("[{}] Move into folder: {} (score {:.1f})".format(kk, fd, score))
    """
    for k, pdf in enumerate(ps.walk_pdfs()):
        db.add_paper(pdf)
        
    
    
    
    import operator
    print("Best matches for {}:".format(paper[1]))
    scores = bc.get_score(paper[2])
    sorted_scores = sorted(scores.items(), key=operator.itemgetter(1))
    print(sorted_scores[::-1])
    """
    
