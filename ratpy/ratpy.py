# -*- coding: utf-8 -*-

from collections import defaultdict
import subprocess
import re


class Frame(object):
    def __init__(self, fdict):
	self.dedicated = fdict['dedicated']
	self.screen = fdict['screen_num']
	self.screenh = fdict['screenh']
	self.number = fdict['number']
	self.height = fdict['height']
	self.width = fdict['width']
	self.window = fdict['window']
	self.screenw = fdict['screenw']
	self.y = fdict['y']
	self.x = fdict['x']
	self.last_access = fdict['last-access']

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def right(self):
        return self.x + self.width

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    def __str__(self):
        s = []
        for prop in ('x', 'y', 'width', 'height'):
            s.append('%s: %d' % (prop, getattr(self, prop)))
        return ', '.join(s)


class Screen(object):
    def __init__(self, sdict):
        self.name = sdict['name']
        self.number = sdict['number']
        self.height = sdict['height']
        self.width = sdict['width']
        self.x = sdict['x']
        self.y = sdict['y']
        self.selected = sdict['selected']

    def __str__(self):
        s = []
        for prop in ('name', 'x', 'y', 'width', 'height'):
            s.append('%s: %r' % (prop, getattr(self, prop)))
        return ', '.join(s)


class RatPy(object):
    screens = {}

    @staticmethod
    def _parse_sfdump(dump):
        # print(dump)
        term_regex = r'''(?mx)
            \s*(?:
                \((?P<name>[^(^)\s]+)|
                :(?P<key>[^(^)\s]+)\s(?P<val>\-?\d+\.\d+|\-?\d+)|
                \)\s(?P<screen_num>\d+)
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
                if groups['screen_num']:
                    frame['screen_num'] = int(groups['screen_num'])
                    frames.append(frame)
                    state = 'screen_init'
                elif groups['key']:
                    frame[groups['key']] = int(groups['val'])
                else:
                    raise Exception('wrong token')

        screens = defaultdict(list)
        for frame in frames:
            screens[frame['screen_num']].append(frame)
        return screens

    @staticmethod
    def _parse_sdump(dump):
        screens = {}
        elts = [e.strip() for e in dump.split(',')]
        for e in elts:
            elts2 = e.split()
            sdict = {}
            sdict['name'] = elts2[0]
            sdict['number'] = int(elts2[1])
            sdict['x'] = int(elts2[2])
            sdict['y'] = int(elts2[3])
            sdict['width'] = int(elts2[4])
            sdict['height'] = int(elts2[5])
            sdict['selected'] = int(elts2[6])
            screens[sdict['number']] = sdict
        return screens

    @staticmethod
    def _call_sdump():
        return subprocess.check_output(['ratpoison', '-c', 'sdump'])

    @staticmethod
    def _call_sfdump():
        return subprocess.check_output(['ratpoison', '-c', 'sfdump'])

    @staticmethod
    def _call_curframe():
        output = subprocess.check_output(['ratpoison', '-c', 'curframe'])
        return int(output)

    @staticmethod
    def update():
        RatPy.update_screens()
        RatPy.update_frames()
        RatPy.curframe_num = RatPy._call_curframe()

    @staticmethod
    def update_screens():
        sdump = RatPy._call_sdump()
        sdicts = RatPy._parse_sdump(sdump)
        for snum, sdict in sdicts.items():
            screen = Screen(sdict)
            RatPy.screens[screen.number] = screen

    @staticmethod
    def update_frames():
        sfdump = RatPy._call_sfdump()
        sfdict = RatPy._parse_sfdump(sfdump)
        for snum, fdicts in sfdict.items():
            frames = {}
            for fdict in fdicts:
                frame = Frame(fdict)
                frames[fdict['number']] = frame
            RatPy.screens[snum].frames = frames

    @staticmethod
    def debug_dump():
        for snum, screen in RatPy.screens.items():
            if screen.selected:
                print('*screen %d' % snum)
            else:
                print('screen %d' % snum)
            print('\t%s' % str(screen))
            for fnum, frame in screen.frames.items():
                if RatPy.curframe_num == frame.number:
                    print('\t*frame %d' % frame.number)
                else:
                    print('\tframe %d' % frame.number)
                print('\t\t%s' % str(frame))

    @staticmethod
    def current_frame():
        cf_ix = RatPy._call_curframe()
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if fnum == cf_ix:
                    return frame

    @staticmethod
    def frame_gen():
        for snum, screen in RatPy.screens.iteritems():
            for fnum, frame in screen.frames:
                yield frame

    #def find_frame_left_global():
    #    cur_frame = RatPy.current_frame()

    #    for snum, screen in RatPy.screens:
    #        for fnum, frame in screen.frames:
    #            for cur in screen:
    #                if frame['bottom'] == cur['top']:
    #                    if frame['right'] >= cur['left'] and frame['left'] <= cur['right']:
    #                        return cur
