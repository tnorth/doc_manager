#!/usr/bin/python
# Requires python3

import os
import sys
import hashlib
import sqlite3
import subprocess

from subprocess import Popen, PIPE


def sha256(fname):
    # Assume that the file fits in memory
    return hashlib.sha256(open(fname, 'rb').read()).hexdigest()


class Database:
    def __init__(self):
        self.db_name="papers.db"
        self.conn = sqlite3.connect(self.db_name)
        self.cur = self.conn.cursor()
    
    def __del__(self):
        self.cur = None
        self.conn.close()
        
    def change_db(self, db_name):
        self.conn.close()
        self.conn = sqlite3.connect(self.db_name)
        self.cur = self.conn.cursor()
    
    def create_database(self, db_name=None, overwrite=False):
        if db_name is None:
            self.change_db(db_name)
        
        if overwrite:
            # Delete table first
            self.cur.execute('''DROP TABLE IF EXISTS papers''')
        
        try:
            self.cur.execute('''CREATE TABLE IF NOT EXISTS papers 
               (id INTEGER PRIMARY KEY AUTOINCREMENT     NOT         NULL,
                path           TEXT    NOT NULL,
                text            TEXT     NOT NULL,
                boxes           TEXT     NOT NULL,
                sha256        CHAR(64)
                );''')
        except sqlite3.OperationalError as oe:
            print("Table probably already exists {}".format(oe))
            raise
        
    def add_paper(self, fpath):
        # From a relative path, extract text and 
        # append it to the DB
        
        # compute sha256sum
        file_hash = sha256(fpath)
        # Extract text
        p = Popen(['pdftotext', fpath, '-'], 
                  stdin=PIPE, stdout=PIPE, stderr=PIPE)
        text, err = p.communicate(b"")
        rc = p.returncode
        # Extract text pos
        p = Popen(['pdftotext', '-bbox', fpath, '-'], 
                  stdin=PIPE, stdout=PIPE, stderr=PIPE)
        text_pos, err = p.communicate(b"")
        rc = p.returncode
        
        # Push to DB
        req = '''INSERT INTO papers VALUES (
            NULL, ?, ?, ?, ?
            );
            '''
        self.cur.execute(req,  (fpath, text, text_pos, file_hash))
        self.conn.commit()
        
        
    def read_all_paper(self):
        req = self.cur.execute('SELECT * FROM papers;')
        for row in req.fetchall():
            yield row
        

if __name__ == "__main__":
    db = Database()
    db.create_database(overwrite=True)
    db.add_paper("papers/hepia/hepia_conf_medical.pdf")
