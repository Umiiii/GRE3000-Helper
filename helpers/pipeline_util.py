import numpy as np
from textwrap import wrap
import signal
from helpers.configs import *
from colorclass import Color
from terminaltables import *
import time


def input_interrupt(signum, frame):
    raise TimeoutError("TIMEOUT")


CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'


def remove_stdout(nline):
    [print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE) for _ in range(nline)]


signal.signal(signal.SIGALRM, input_interrupt)


def long_str_wrap(s, width):
    sp = s.split('\n')
    ret = []
    for i in sp:
        ret.extend(wrap(i, width))
    return ret


def get_inbanner_text(inp: str, title=None, repeater="=", body_width=25, padding=2, fix_width=False,
                      canopy_switcher=(1, 1)):
    inp = inp.strip()
    inp = inp.split('\n')
    max_len = max([len(i) for i in inp])
    text_len = body_width - (1 + padding) * 2
    assert body_width > 0, "{} - (1+{})*2 = {} <= 0".format(body_width, padding, text_len)

    if max_len >= text_len:

        tmp = []
        for i in inp:
            tmp.extend(wrap(i, text_len))
        inp = tmp
    else:
        if not fix_width:
            body_width = max_len + (1 + padding) * 2

    canopy = ''.join([repeater for _ in range(body_width)])
    re_str = []
    if canopy_switcher[0]:
        if title is not None:
            title = ' {} '.format(title)
            canopy_with_title = "{:{rep}^{body_width}}".format(title, rep=repeater, body_width=body_width)
            re_str.append(canopy_with_title)
        else:
            re_str.append(canopy)
    for i in inp:
        re_str.append(
            "{head}{:^{text_width_with_padding}}{tail}".format(i, head=repeater,
                                                               text_width_with_padding=body_width - 2,
                                                               tail=repeater))
    if canopy_switcher[1]: re_str.append(canopy)
    re_str = '\n'.join(re_str)
    return re_str


def parse_user_selection(inp: str, min=1, max=31, delimiter=',', connector=('-', '~')):
    def __parse_one_segment(seg: str):
        def ___parse_single(s: str):
            try:
                re = int(s)
                return [re]
            except:
                return None

        # case: ...,14,...
        re = ___parse_single(seg)

        if re is not None:
            if re[0] < min or re[0] > max:
                print("Input {} is out of bound: [{}, {}]".format(re[0], min, max))
            return re

        # case: ...,3~5... or 3-5
        for cn in connector:
            sp = [i.strip() for i in seg.split(cn)]
            if len(sp) != 2: continue
            a = ___parse_single(sp[0])[0]
            b = ___parse_single(sp[1])[0]

            if a is None or b is None: continue
            if a < min or a > max or b < min or b > max:
                print("Input {} is out of bound: [{}, {}]".format(seg, min, max))
                return None
            if a > b:
                print("Input {} is invalid. Example: 1,3,5-7,10~11".format(seg))
                return None

            return list(range(a, b + 1))

        # all cases failed
        print("Input {} is invalid. Example: 1,3,5-7,10~11".format(seg))
        return None

    selected_list = []
    sp_list = [i.strip() for i in inp.split(delimiter)]

    # if there is a single input without delimiters
    if len(sp_list) == 1:
        if sp_list[0] == '0':
            selected_list = list(range(min, max + 1))
            return selected_list
        if sp_list[0] in ['-1', '-2']:
            selected_list = [int(sp_list[0])]
            return selected_list
    # else
    for seg in sp_list:
        seg_re = __parse_one_segment(seg)
        if seg_re is None: return None
        selected_list.extend(seg_re)

    return list(np.unique(selected_list))


def show_time_summary(recall_times):
    title = 'Average Recall Time'
    title = Color.colorize('yellow', title)

    avg = '{:.2f}s'.format(sum(recall_times) / len(recall_times))
    len_old = len(avg)
    avg = Color.colorize('green', avg)

    content = "{} per word".format(avg).center(BANNER_BODY_WIDTH + 6)
    tb = DoubleTable([[content]], title=title)
    print(tb.table)


def query_list(all_content):
    recall_times = []
    recall_bitmap = np.zeros(all_content.shape[0], dtype=np.int)
    num_words = all_content.shape[0]
    for idx in range(num_words):
        content = all_content[idx, :]
        recall_the_word, new_content, recall_time = __query_word(content, '{:d}/{:d}'.format(idx + 1, num_words))
        recall_bitmap[idx] = recall_the_word
        all_content[idx, :] = new_content
        recall_times.append(recall_time)

    show_time_summary(recall_times)
    return all_content, recall_bitmap


def review_oblivious(all_content, recall_bitmap):
    def prompt_round_info(n_round, n_word):

        title = 'Round {}'.format(n_round)

        text = 'Review {} words'.format(n_word)
        tx = get_inbanner_text(text, title, repeater='=',
                               body_width=BANNER_BODY_WIDTH,
                               fix_width=True,
                               canopy_switcher=(1, 1))

        tx = Color.colorize('yellow', tx)
        print('\n' + tx)

    round = 1
    recall_times = []
    while True:
        indces = np.where(recall_bitmap == 0)[0]
        if len(indces) == 0: break
        prompt_round_info(n_round=round, n_word=len(indces))
        np.random.shuffle(indces)
        for e, idx in enumerate(indces):
            content = all_content[idx, :]
            recall_the_word, new_content, recall_time = __query_word(content, '{}/{}'.format(e + 1, len(indces)))
            recall_bitmap[idx] = recall_the_word
            all_content[idx, :] = new_content
            recall_times.append(recall_time)
        round += 1

    if len(recall_times):  show_time_summary(recall_times)
    return all_content


def wrapped(s, max_len):
    ret = []
    sp = s.split('\n')
    for i in sp:
        wi = wrap(i, max_len)
        ret.extend(wi)
    for i in range(len(ret)):
        ret[i] = ret[i].encode('gb18030').center(max_len).decode('gb18030')

    return '\n'.join(ret)


def __query_word(content, counter=None):
    def process_inp(inp):
        if inp is None: return False
        if len(inp) == 0: return True
        if len(inp) > 0: return False

    def show_word():
        tb = AsciiTable([[word.center(BANNER_BODY_WIDTH - 4)]], counter)
        tx = tb.table
        print(tx)
        return len(tb.table.splitlines())

    def show_meaning(color):
        text = wrapped(meaning, BANNER_BODY_WIDTH-8)
        if MEANING_WIT_SYNONYM:
            text += '\n'
            text += '-'.join(['' for _ in range(int(3 * BANNER_BODY_WIDTH / 5))])
            text += '\n{}'.format(wrapped(synonmy, BANNER_BODY_WIDTH-8))
            #text += '\n'.join(wrap(synonmy, BANNER_BODY_WIDTH - 8))
        cl = Color()

        text = '\n'.join(
            [cl.colorize(color, t.encode('gb18030').center(BANNER_BODY_WIDTH - 4).decode('gb18030')) for t in
             text.split('\n')])
        title = ' Meaning [{} ({})]'.format(report, accuracy) if len(report) != 0 else None

        tb = AsciiTable([[text]], title)

        tx = tb.table

        print(tx)
        return len(tx.split('\n'))

    # content: word, meaning, sysnonym, report, accuracy
    sheet_id = content[0]
    word = content[1]
    meaning = content[2]
    synonmy = content[3]
    report = content[4]
    accuracy = content[5]

    q_nline = show_word()
    recall_time = time.time()
    inp = __input_with_timeout("Recall it?    ")
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

    # update report
    if len(report) == 0:  # init report
        report = '{:d}/{}'.format(recall_the_word, 1)
        true_cnt = int(recall_the_word)
        all_cnt = 1
    else:
        sp = report.split('/')
        true_cnt = int(sp[0]) + recall_the_word
        all_cnt = int(sp[1]) + 1
        report = '{}/{}'.format(true_cnt, all_cnt)

    # update accruacy
    accuracy = '{:.1f}%'.format(100 * float(true_cnt) / all_cnt)

    #
    if m_nline > 0: remove_stdout(m_nline)
    if recall_the_word:
        show_meaning('green')
    else:
        show_meaning('red')

    new_content = [sheet_id, word, meaning, synonmy, report, accuracy]
    return recall_the_word, new_content, recall_time



def __input_with_timeout(prompt):
    signal.alarm(INP_TIMEOUT)
    try:
        inp = input(prompt).strip()
        signal.alarm(0)
        return inp
    except:
        return None


if __name__ == '__main__':
    # content = [1, 'good', 'HAOHAOHAO', '1 well\n2 excellent', '1/3', '33.33']
    # __query_word(content, counter='(1/2)')

    # tms = list(np.random.uniform(0,1,(100,)))
    # show_time_summary(tms)


    print("[{}]".format(wrapped(
        "FileNotFoundError: [Errno 2] No such file or directory:\n'/Users/microos/Desktop/DFA_graph/c-minus-scanner-2016-id.jff'", 30)))
