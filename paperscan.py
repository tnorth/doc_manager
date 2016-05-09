#!/usr/bin/python

import os
import sys
import fnmatch
import subprocess

class PaperScan:
    def __init__(self, root_dir="papers"):
        self.root_dir = root_dir
        self.img_ext = ["png", "tif", "tiff", "jpg"]
        self.lang = "fra"
    
    def scan_papers(self):
        # Look for image files and PDFs
        img_files = []
        pdf_files = []
        for root, dirnames, filenames in sorted(os.walk(self.root_dir)):
            # Look for images files of various extensions
            for ext in self.img_ext:
                ff_in_dir = []
                for filename in fnmatch.filter(filenames, 
                                            '*.{}'.format(ext)):
                    ff_in_dir.append(os.path.join(root, filename))
                # Look for image series
                dir_imgs = self.find_series(ff_in_dir)
                img_files += dir_imgs
                    
            # Look for PDFs
            for filename in fnmatch.filter(filenames, '*.pdf'):
                pdf_files.append(os.path.join(root, filename))
        
        self.img_files = img_files
        self.pdf_files = pdf_files
        img_files_basename = {''.join(i.split(".")[:-1]):i for i in img_files}
        pdf_files_basename = [''.join(i.split(".")[:-1]) for i in pdf_files]
    
        missing_pdfs = set(img_files_basename.keys()) - set(pdf_files_basename)
        
        return pdf_files, img_files, [img_files_basename[k] for k in missing_pdfs]
        
    # TODO: this in parallel with joblib, or with GNU parallel
    def make_ocr_pdf(self, force=False):
        # Find missing PDFs and OCR them
        
        _, all_images, missing = self.scan_papers()
        
        images = all_images if force else missing
        
        for img in images:
            ext_len = len(img.split(".")[-1]) + 1
            print("Making PDF for {}".format(img))
            print("tesseract -l {} {} {} pdf".format(
                            self.lang, img, img[:-ext_len]))
            subprocess.call("tesseract -l {} {} {} pdf".format(
                            self.lang, img, img[:-ext_len]),
                            shell=True)
            
    def walk_pdfs(self):
        # Re-scan
        all_pdfs, all_images, missing = self.scan_papers()
        if missing:
            print("Warning: not all images have corresponding PDFs!")
        
        for pdf in all_pdfs:
            yield pdf
            
    def find_series(self, imgs):
        # images called foo_1.png, foo_2.png, foo_3.png must be
        # transformed into a multipage tiff
        
        # Remove extensions
        imgs_noext =  [''.join(i.split(".")[:-1]) for i in imgs]
        imgs_ext = [''.join(i.split(".")[-1]) for i in imgs]
        
        # Form a list of unique base names (excluding _ij)
        names = set([])
        names_dict = {}
        for img, ext in zip(imgs_noext, imgs_ext):
            # basename, without number
            name_wo_num = '_'.join(img.split("_")[:-1])

            # number only
            num = img.split(name_wo_num + "_")[-1]
            
            if name_wo_num in names_dict:
                # Already have something
                names_dict[name_wo_num]['num'].append(num)
                names_dict[name_wo_num]['ext'].append(ext)
                
            else:
                names_dict[name_wo_num] = {'num': [num,], 'ext':[ext,]}
            names.add(name_wo_num)
        
        # Now keep only the series that contain increasing numbers starting at 1.
        # Exclude: - values of names_dict that have less than 2 items
        #          - values of names_dict that don't convert to int
        #          - values of names_dict that do not start at 1
        #          - values that do not follow each other
        #          - files that have different extension
        new_files = []
        del_files = []
        
        for basename, num_ext in names_dict.items():
            num = num_ext['num']
            ext = num_ext['ext']
            # length criteria
            if len(num) < 2:
                continue
            # conversion to int criteria
            num_ints = []
            for ii in num:
                try:
                    num_ints.append(int(ii))
                except ValueError:
                    continue
            # start at 1 criteria
            ints_sorted = sorted(num_ints)
            if (ints_sorted[0] != 1):
                continue
            # values following criteria
            n_num = len(ints_sorted)
            if (sum(ints_sorted) != n_num*(n_num+1) / 2) or ints_sorted[-1] != n_num:
                continue
            # values with different extensions
            if (len(set(ext)) > 1):
                continue
            
            print("Valid series: {}".format(basename), ints_sorted, ext)
            new_file, deleted_files = self.group_files(basename, ints_sorted, ext[0])
            new_files.append(new_file)
            del_files += deleted_files
            
        remaining_files = set(imgs) - set(del_files)
        return new_files + list(remaining_files)
            
    
    def group_files(self, basename, nums, ext):
        # Make a multipage tiff and delete these source files
        # return the new tif file name, and the list of deleted files.
    
        grouped_files = ['{}_{}.{}'.format(basename, nn, ext) for nn in nums]
        file_list = ' '.join(grouped_files)
        
        #print("Will join ", file_list)
        ret = subprocess.call("convert  {} {}.tiff".format(
                            file_list, basename),
                            shell=True)
        if ret != 0:
            # Something append
            raise Exception("Conversion to multipage TIFF impossible for {}".format(
                basename))
        
        # Otherwise delete source files
        for ff_name in grouped_files:
            print("Deleting deprecated file {}".format(ff_name))
            os.remove(ff_name)
            
        return "{}.tiff".format(basename), grouped_files
        
if __name__ == "__main__":
    # Assume you have a folder named PaperScan.root_dir in the script path
    # This folder has subfolders with scanned documents
    
    ps = PaperScan()
    # Scan papers just returns present images and missing PDFs.
    # it creates multipage TIFF images from image series.
    pdfs, imgs, missing = ps.scan_papers()

    # make_ocr calls scan_papers to find missing PDFs.
    # It creates new PDFs from these new images
    ps.make_ocr_pdf(force=False)
    
    for k, pdf in enumerate(ps.walk_pdfs()):
        print("Document {}: {}".format(k, pdf))
        
    import database
    db = database.Database()
    db.create_database(overwrite=True)
    for k, pdf in enumerate(ps.walk_pdfs()):
        db.add_paper(pdf)
        
    import documentproximity as dp
    bc = dp.DocumentProximity()
    for paper in db.read_all_paper():
        bc.train(paper[1], paper[2])
    
    
    import operator
    print("Best matches for {}:".format(paper[1]))
    scores = bc.get_score(paper[2])
    sorted_scores = sorted(scores.items(), key=operator.itemgetter(1))
    print(sorted_scores[::-1])
    
    
