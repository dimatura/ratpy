from collections import OrderedDict
from collections import defaultdict
import re
import subprocess


class Ratpoison(object):
    def __init__(self):
        pass


def parse_sfdump0(dump):
    out = OrderedDict()

    print(dump)

    frames = dump.strip().split(',')
    for frame in frames:
        frame = frame.strip()
        lp = frame.find('(')
        rp = frame.find(')')
        screen_ix = int(frame[rp+1:])

        tokens = frame[lp+1:rp].split()[1:]

        frame_d = OrderedDict()
        for i in range(0, len(tokens), 2):
            key = tokens[i].replace(':', '')
            val = int(tokens[i+1])
            frame_d[key] = val

        frame_d['bottom'] = frame_d['y'] + frame_d['height']
        frame_d['right'] = frame_d['x'] + frame_d['width']
        frame_d['left'] = frame_d['x']
        frame_d['top'] = frame_d['y']

        if screen_ix in out:
            out[screen_ix].append(frame_d)
        else:
            out[screen_ix] = [frame_d]
    return out


#def tokenize(dump):
#    term_regex = r'''(?mx)
#	\s*(?:
#	    (?P<brackl>\()|
#	    (?P<brackr>\))|
#	    (?P<num>\-?\d+\.\d+|\-?\d+)|
#	    (?P<kw>:[^(^)\s]+)|
#	    (?P<comma>,)|
#	    (?P<s>[^(^)\s]+)
#	   )'''
#    tokens = [[(t,v) for t,v in termtypes.groupdict().items() if v][0] for termtypes in re.finditer(term_regex, dump)]
#    return tokens


def parse_sfdump(dump):
    print(dump)
    term_regex = r'''(?mx)
	\s*(?:
	    \((?P<name>[^(^)\s]+)|
            :(?P<key>[^(^)\s]+)\s(?P<val>\-?\d+\.\d+|\-?\d+)|
            \)\s(?P<framenum>\d+)
	   )'''

    state = 'screen_init'

    frames = []
    for termtypes in re.finditer(term_regex, dump):
        groups = termtypes.groupdict()
        #print(groups)
        if state == 'screen_init':
            if groups['name']:
                frame = {}
                state = 'screen_mid'
            else:
                raise Exception('wrong token')
        elif state == 'screen_mid':
            if groups['framenum']:
                frame['screen'] = int(groups['framenum'])
                frames.append(frame)
                state = 'screen_init'
            elif groups['key']:
                frame[groups['key']] = int(groups['val'])
            else:
                raise Exception('wrong token')

    screens = defaultdict(list)
    for frame in frames:
        screens[frame['screen']].append(frame)
    return screens


def print_sfdump(sfdump, cf_ix = None):
    for k0, frames in sfdump.items():
        print('screen %d' % k0)
        for frame in frames:
            if cf_ix == frame['number']:
                print('\t*frame:')
            else:
                print('\tframe:')
            for k1, v1 in frame.items():
                print('\t\t%s: %s' % (k1, v1))


def get_current_frame(cf_ix, sfdump):
    for screen_ix, screen in sfdump.items():
        for frame in screen:
            if frame['number'] == cf_ix:
                return frame


def find_frame_down(frame, sfdump):
    # based on split.c in ratpoison
    for screen_ix, screen in sfdump.items():
        for cur in screen:
            if frame['bottom'] == cur['top']:
                if frame['right'] >= cur['left'] and frame['left'] <= cur['right']:
                    return cur



def call_sfdump():
    cmd = ['ratpoison', '-c', 'sfdump']
    output = subprocess.check_output(cmd)
    output2 = parse_sfdump(output)
    return output2


def call_curframe():
    cmd = ['ratpoison', '-c', 'curframe']
    output = subprocess.check_output(cmd)
    return int(output)


cf_ix = call_curframe()
sfdump = call_sfdump()
print_sfdump(sfdump, cf_ix = cf_ix)
curframe = get_current_frame(cf_ix, sfdump)
#framedown = find_frame_down(curframe, sfdump)
