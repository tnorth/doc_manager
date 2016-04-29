#!/usr/bin/python

import os
import sys
import simplebayes


class DocumentProximity:
    def __init__(self):
        self.bayes = simplebayes.SimpleBayes()
    
    def train(self, fname, text):
        self.bayes.train(fname, text.decode('utf8'))
        
    def get_score(self, text):
        return self.bayes.score(text.decode('utf8'))
