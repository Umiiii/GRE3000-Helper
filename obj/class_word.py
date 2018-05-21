from textwrap import wrap
from colorclass import Color
import numpy as np
from helpers.tools import *

class Word(object):
    def parse_report(self):
        if len(self.report) == 0:
            self.recall_cnt = 0
            self.all_cnt = 0
            self.accuracy = 0
        else:
            sp = self.report.split('/')
            self.recall_cnt = int(sp[0])
            self.all_cnt = int(sp[1])
            self.accuracy = 100*float(self.recall_cnt) / float(self.all_cnt)

    def __init__(self, sheet_id, word, meaning,synonym, report):
        self.sheet_id = sheet_id
        self.word = word
        self.meaning = meaning
        self.synonym = synonym
        self.report = report
        #
        self.parse_report()

    def get_meaning(self, wrap_and_center=0, color=None):
        return get_longstring(self.meaning, wrap_and_center, color)

    def get_synonym(self, wrap_and_center=0, color=None):
        return get_longstring(self.synonym, wrap_and_center, color)

    def get_report(self):
        if self.all_cnt == 0: return ''
        return '{}/{}'.format(self.recall_cnt, self.all_cnt)

    def get_accuracy(self):
        if self.all_cnt == 0: return ''
        return '{:.1f}%'.format(self.accuracy)

    def update_recall(self, success):
        self.recall_cnt += success
        self.all_cnt += 1
        self.accuracy = 100 * float(self.recall_cnt) / float(self.all_cnt)

    def to_list(self, with_st_id):
        ret  = []
        if with_st_id: ret.append(self.sheet_id)
        ret.extend([self.word, self.meaning, self.synonym, self.get_report(), self.get_accuracy()])
        return ret


def get_longstring(inp, wrap_and_center=0, color=None):
    if wrap_and_center <= 0: return inp

    ret = wrapped(inp, wrap_and_center)
    if color is not None:
        ret = [Color().colorize(s, color) for s in ret.split('\n')]
        ret = '\n'.join(ret)

    return ret

