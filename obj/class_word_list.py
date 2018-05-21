import obj.class_word
import numpy as np
from colorclass import Color
from terminaltables import AsciiTable
from helpers.configs import *
from helpers.tools import *
import time


class WordList(object):
    def __init__(self):
        self.content = []

    def add(self, word):
        assert type(word) == obj.class_word
        self.content.append(word)

    def extract_by_st_id(self, st_id):
        return [i for i in self.content if st_id == i.sheet_id]

    def shuffle(self):
        np.random.shuffle(self.content)

    def query(self):
        assert len(self.content) > 0
        for i, w in enumerate(self.content):
            title = '{}/{}'.format(i + 1, len(self.content))
            recall_the_word, recall_time = query_word(w, title)



def query_word(word_obj: obj.class_word, counter_title=None):
    def process_inp(inp):
        if inp is None: return False
        if len(inp) == 0: return True
        if len(inp) > 0: return False

    def show_word():
        tb = AsciiTable([[word.center(BANNER_BODY_WIDTH - 4)]], counter_title)
        tx = tb.table
        print(tx)
        return len(tb.table.splitlines())

    def show_meaning(color):
        text = word_obj.get_meaning(wrap_and_center=BANNER_BODY_WIDTH - 8)
        if MEANING_WIT_SYNONYM:
            text += '\n'
            text += '-'.join(['' for _ in range(int(3 * BANNER_BODY_WIDTH / 5))])
            text += '\n{}'.format(word_obj.get_synonmy(BANNER_BODY_WIDTH - 8))
        cl = Color()

        text = '\n'.join(
            [cl.colorize(color, t.encode('gb18030').center(BANNER_BODY_WIDTH - 4).decode('gb18030')) for t in
             text.split('\n')])
        title = ' Meaning [{} ({})]'.format(report, accuracy) if len(report) != 0 else ' Meaning'

        tb = AsciiTable([[text]], title)
        tx = tb.table

        print(tx)
        return len(tx.split('\n'))

    # content: word, meaning, sysnonym, report
    sheet_id = word_obj.sheet_id
    word = word_obj.word
    report = word_obj.get_report()
    accuracy = word_obj.get_accuracy()

    q_nline = show_word()
    recall_time = time.time()
    inp = input_with_timeout("Recall it?    ", INP_TIMEOUT)
    recall_time = time.time() - recall_time

    remove_stdout(2)
    inp = process_inp(inp)
    recall_the_word = False
    if inp:
        m_nline = show_meaning('yellow')
        inp_confirm = input("Consistent?    ")
        remove_stdout(1)
        inp_confirm = process_inp(inp_confirm)
        if inp_confirm:
            recall_the_word = True

    else:
        m_nline = -1

    word_obj.update_recall(recall_the_word)
    accuracy = word_obj.get_accuracy()

    #
    if m_nline > 0: remove_stdout(m_nline)
    if recall_the_word:
        show_meaning('green')
    else:
        show_meaning('red')

    return recall_the_word, recall_time
