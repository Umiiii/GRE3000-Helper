import os
import numpy as np
import argparse
from helpers import workbook_op
from helpers import pipeline_util
from helpers.configs import *
from terminaltables import DoubleTable, AsciiTable
from colorclass import Color
import datetime
import os


this_dir = os.path.dirname(__file__)
DEFAULT_WB = os.path.realpath(os.path.join(this_dir, './user_data/WordList_V2.xlsx'))
TEST_WB = os.path.realpath(os.path.join(this_dir, './user_data/WordList_V2_test.xlsx'))

WB_PATH = None
TESTMODE = False

def get_args():
    global WB_PATH, TESTMODE
    parser = argparse.ArgumentParser(description='GRE3000 Helper')
    parser.add_argument('-f', '--filepath', dest='filepath', type=str, default='',
                        help="Specify a valid workbook path")

    parser.add_argument('-t', '--testmode', dest='testmode', type=bool, default=False,
                        help="Use the test dataset.")



    args = parser.parse_args()
    testmode = True #args.testmode
    wb_path = args.filepath
    if len(wb_path) == 0:
        WB_PATH = TEST_WB if testmode else DEFAULT_WB
    else:
        WB_PATH = wb_path
        if testmode:
            print("Ignoring '-t' flag when a workbook specified.")

    TESTMODE = args.testmode
    return args


def prompt_welcome():
    if TESTMODE:
        print(Color().colorize('red', '[TESTMODE IS ON]'))
    text = "Welcome to GRE3000 Helper. Wordlist from: {}".format(WB_PATH)
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True))


def load_wb():
    text = "Loading, please wait..."
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[0, 1]))
    wb, st_name_dict = workbook_op.open_workbook(WB_PATH)
    return wb, st_name_dict


def ask_list_selection(st_name_dict: dict):
    text = "Load Done!\n"
    text += "Please input one or more index to start:\n"
    text += "Example: 7 or 1,2,4-8,9~10 or 0 or -1 or -2\n"
    st_name_dict[-1] = 'Exit'
    st_name_dict[-2] = 'Review'

    for i, (k, v) in enumerate(st_name_dict.items()):
        text += "{}. {}".format(k, v)

        if i % 2:
            text += '\n'
        else:
            n_space = 4
            text += ''.join([' ' for _ in range(n_space)])

    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[0, 1]))

    while True:
        inp = input("Your Input:").strip()
        if len(inp) == 0: continue
        selected = pipeline_util.parse_user_selection(inp)
        if selected is None: continue
        assert len(selected) > 0, selected
        if -1 in selected:
            assert len(selected) == 1, selected
            print(pipeline_util.get_inbanner_text("See you :D", body_width=BANNER_BODY_WIDTH, fix_width=True,
                                                  canopy_switcher=[1, 1]))
            exit()

        if -2 in selected:
            assert len(selected) == 1, selected
            return -2

        return selected


def prompt_rule(num_words):
    text = "Successfully loaded {} words".format(num_words)
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[1, 1]))

    text = '''RULE
    1. Enter NOTHING to indicate you RECALL this word; Enter SOMETHING to indicate you FORGET it.
    2. Enter NOTHING to indicate your answer is consistent with the given one; vice versa.\n'''
    if INP_TIMEOUT > 0:
        text += \
            '''3. Give an input in {}s, or it will be consider as a failure of recall.'''.format(INP_TIMEOUT)
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[0, 1]))
    input()


def prompt_oblivious():
    text = '''Review oblivious words
    This section will help you review the words UNTIL you can correctly recall them all.
    '''
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[1, 1]))


def save_new_content(wb, all_content, selected, st_name_dict):
    def extract_sheet_content(sheet_idx):
        row_indces = np.where(all_content[:, 0] == sheet_idx)[0]
        st_content = all_content[row_indces, 1:]
        return st_content

    for sheet_idx in selected:
        sheet_name = st_name_dict[sheet_idx]
        st = wb.get_sheet_by_name(sheet_name)
        st_content = extract_sheet_content(sheet_idx)
        workbook_op.fill_sheet_with_new_content(st, st_content)

    saved_to = workbook_op.save_workbook(wb, WB_PATH)
    text = 'Work Saved to:\n{}'.format(saved_to)
    print(pipeline_util.get_inbanner_text(text, body_width=BANNER_BODY_WIDTH, fix_width=True, canopy_switcher=[1, 1]))


def query_synonmy():
    pass


def reset_records(wb, st_name_dict):
    exit()


def recall_summary(recall_bitmap):
    def get_color(rate):
        if rate <= 0.5: return 'red'
        if rate > 0.5 and rate < 0.8: return 'yellow'
        if rate >= 0.8: return 'green'

    recall_num = len(np.where(recall_bitmap == 1)[0])
    all_num = len(recall_bitmap)
    recall_rate = float(recall_num) / all_num
    cl = get_color(recall_rate)
    title = Color.colorize(cl, 'Report')

    color_str_a_b = Color.colorize(cl, '{}/{}'.format(recall_num, all_num))
    color_str_rate = Color.colorize(cl, '{:.1f}%'.format(100 * recall_rate))

    data = (['Recall Num : {}'.format(color_str_a_b).center(BANNER_BODY_WIDTH + 6)],
            ['Recall Rate: {}'.format(color_str_rate).center(BANNER_BODY_WIDTH + 6)])

    tb = DoubleTable(data, title)
    print(tb.table)
    print()


def save_oblivious_by_recall_bitmap(all_content, bitmap, selected):
    indces = np.where(bitmap == 0)[0]

    oblivious_content = all_content[indces, :]
    error_num = oblivious_content.shape[0]
    all_num = all_content.shape[0]
    correct_num = all_num - error_num
    name = '{}_[{}]_{}of{}_{:.1f}%.npy'.format(datetime.datetime.now().strftime("%Y%m%d"),
                                           ','.join( [str(i) for i in sorted(selected)]),
                                          correct_num, all_num,
                                          100 * float(correct_num) / float(all_num))

    path = os.path.join(this_dir, 'user_data/ghost', name)
    np.save(path, oblivious_content)
    print("Oblivious words save to {}\n".format(path))


def normal_query(wb, selected, st_name_dict):
    # parse sheets into np.array
    all_content = workbook_op.parse_sheets(wb, selected, st_name_dict)
    num_words = all_content.shape[0]

    # query: show the rule, query, show summary
    prompt_rule(num_words)
    all_content, recall_bitmap = pipeline_util.query_list(all_content)
    recall_summary(recall_bitmap)

    if len(np.where(recall_bitmap == 0)[0]) != 0:
        save_oblivious_by_recall_bitmap(all_content, recall_bitmap, selected)

        # review: show the info, query oblivious
        prompt_oblivious()
        all_content = pipeline_util.review_oblivious(all_content, recall_bitmap)

    # save
    save_new_content(wb, all_content, selected, st_name_dict)


def review_ghost():
    ghost_dir = os.path.join(this_dir, 'user_data/ghost')
    names = os.listdir(ghost_dir)
    names = sorted(names)
    offset = 9
    data = [[str(i + 1).rjust(2), names[i].center(BANNER_BODY_WIDTH - offset)] for i in range(len(names))]
    data.append(['-1', 'Exit'.center(BANNER_BODY_WIDTH - offset)])

    tb = AsciiTable(data, 'Selected to review')
    tb.inner_row_border = True
    print(tb.table)
    while True:
        inp = input('Your Input:').strip()
        try:
            inpp = int(inp)
            if inpp == -1: return 0
            if inpp in range(1, len(names) + 1):
                break
            else:
                print('{} is out of bound.'.format(inpp))
        except:
            continue
    ob_content = np.load(os.path.join(ghost_dir, names[inpp - 1]))
    ob_content, recall_bitmap = pipeline_util.query_list(ob_content)
    recall_summary(recall_bitmap)

    if len(np.where(recall_bitmap == 0)[0]) != 0:
        pipeline_util.review_oblivious(ob_content, recall_bitmap)


def main():
    # init: welcome, load
    get_args()
    prompt_welcome()
    wb, st_name_dict = load_wb()

    # ask for list selection
    selected = ask_list_selection(st_name_dict)
    if type(selected) is list:
        normal_query(wb, selected, st_name_dict)
    if selected == -2:
        review_ghost()


if __name__ == '__main__':
    main()
