# -*- coding: utf-8 -*-

from collections import defaultdict
import subprocess
import re


def _call_sdump():
    return subprocess.check_output(['ratpoison', '-c', 'sdump'])

def _call_sfdump():
    return subprocess.check_output(['ratpoison', '-c', 'sfdump'])

def _call_curframe():
    return subprocess.check_output(['ratpoison', '-c', 'curframe'])

def _call_focusleft():
    return subprocess.check_output(['ratpoison', '-c', 'focusleft'])

def _call_focusleft():
    return subprocess.check_output(['ratpoison', '-c', 'focusright'])

def _call_focusup():
    return subprocess.check_output(['ratpoison', '-c', 'focusup'])

def _call_focusdown():
    return subprocess.check_output(['ratpoison', '-c', 'focusdown'])

def _call_nextscreen():
    return subprocess.check_output(['ratpoison', '-c', 'nextscreen'])

def _call_prevscreen():
    return subprocess.check_output(['ratpoison', '-c', 'prevscreen'])

def _call_sselect(num):
    return subprocess.check_output(['ratpoison', '-c', 'sselect %d' % num])

def _call_fselect(num):
    return subprocess.check_output(['ratpoison', '-c', 'fselect %d' % num])


class Frame(object):
    def __init__(self, fdict):
	self.dedicated = fdict['dedicated']
	self.screen_num = fdict['screen_num']
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
    def screen(self):
        return RatPy.screens[self.screen_num]

    @property
    def bottom(self):
        return self.gy + self.height

    @property
    def right(self):
        return self.gx + self.width

    @property
    def left(self):
        return self.x

    @property
    def top(self):
        return self.y

    @property
    def gx(self):
        return self.x + self.screen.x

    @property
    def gy(self):
        return self.y + self.screen.y

    @property
    def gbottom(self):
        return self.gy + self.height

    @property
    def gright(self):
        return self.gx + self.width

    @property
    def gleft(self):
        return self.gx

    @property
    def gtop(self):
        return self.gy

    def __str__(self):
        s = []
        for prop in ('number', 'x', 'y', 'gx', 'gy', 'width', 'height'):
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
    def update():
        RatPy.update_screens()
        RatPy.update_frames()
        RatPy.curframe_num = int(_call_curframe())

    @staticmethod
    def update_screens():
        sdump = _call_sdump()
        sdicts = RatPy._parse_sdump(sdump)
        for snum, sdict in sdicts.items():
            screen = Screen(sdict)
            RatPy.screens[screen.number] = screen

    @staticmethod
    def update_frames():
        sfdump = _call_sfdump()
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
        cf_ix = int(_call_curframe())
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if fnum == cf_ix:
                    return frame

    @staticmethod
    def frame_gen():
        for snum, screen in RatPy.screens.iteritems():
            for fnum, frame in screen.frames:
                yield frame

    @staticmethod
    def _frames_overlap_vertical(f1, f2):
        return (f1.gtop < f2.gbottom) and (f2.gtop < f1.gbottom)

    @staticmethod
    def _frames_overlap_horizontal(f1, f2):
        return (f1.gleft < f2.gright) and (f2.gleft < f1.gright)

    @staticmethod
    def global_find_frame_left():
        cur_frame = RatPy.current_frame()
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if cur_frame.gleft == frame.gright:
                    if RatPy._frames_overlap_vertical(cur_frame, frame):
                        return frame

    @staticmethod
    def global_find_frame_right():
        cur_frame = RatPy.current_frame()
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if cur_frame.gright == frame.gleft:
                    if RatPy._frames_overlap_vertical(cur_frame, frame):
                        return frame

    @staticmethod
    def global_find_frame_up():
        cur_frame = RatPy.current_frame()
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if cur_frame.gtop == frame.gbottom:
                    if RatPy._frames_overlap_horizontal(cur_frame, frame):
                        return frame

    @staticmethod
    def global_find_frame_bottom():
        cur_frame = RatPy.current_frame()
        for snum, screen in RatPy.screens.items():
            for fnum, frame in screen.frames.items():
                if cur_frame.gbottom == frame.gtop:
                    if RatPy._frames_overlap_horizontal(cur_frame, frame):
                        return frame

    @staticmethod
    def global_focusleft():
        frame = RatPy.global_find_frame_left()
        _call_fselect(frame.number)

    @staticmethod
    def global_focusright():
        frame = RatPy.global_find_frame_right()
        _call_fselect(frame.number)

    @staticmethod
    def global_focusup():
        frame = RatPy.global_find_frame_up()
        _call_fselect(frame.number)

    @staticmethod
    def global_focusdown():
        frame = RatPy.global_find_frame_down()
        _call_fselect(frame.number)
