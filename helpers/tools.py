from textwrap import wrap
import signal


CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'

def wrapped(s, max_len):
    ret = []
    sp = s.split('\n')
    for i in sp:
        wi = wrap(i, max_len)
        ret.extend(wi)
    for i in range(len(ret)):
        ret[i] = ret[i].encode('gb18030').center(max_len).decode('gb18030')

    return '\n'.join(ret)


def remove_stdout(nline):
    [print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE) for _ in range(nline)]


def input_with_timeout(inp_prompt, amount):
    signal.alarm(amount)
    try:
        inp = input(inp_prompt).strip()
        signal.alarm(0)
        return inp
    except:
        return None


