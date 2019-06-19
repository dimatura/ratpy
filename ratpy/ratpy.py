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
    def __init__(self):
        self.screens = {}

    def _parse_sfdump(self, dump):
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

    def _parse_sdump(self, dump):
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

    def _call_sdump(self):
        return subprocess.check_output(['ratpoison', '-c', 'sdump'])

    def _call_sfdump(self):
        return subprocess.check_output(['ratpoison', '-c', 'sfdump'])

    def _call_curframe(self):
        output = subprocess.check_output(['ratpoison', '-c', 'curframe'])
        return int(output)

    def update(self):
        self.update_screens()
        self.update_frames()
        self.curframe_num = self._call_curframe()

    def update_screens(self):
        sdump = self._call_sdump()
        sdicts = self._parse_sdump(sdump)
        for snum, sdict in sdicts.items():
            screen = Screen(sdict)
            self.screens[screen.number] = screen

    def update_frames(self):
        sfdump = self._call_sfdump()
        sfdict = self._parse_sfdump(sfdump)
        for snum, fdicts in sfdict.items():
            frames = {}
            for fdict in fdicts:
                frame = Frame(fdict)
                frames[fdict['number']] = frame
            self.screens[snum].frames = frames

    def debug_dump(self):
        for snum, screen in self.screens.items():
            if screen.selected:
                print('*screen %d' % snum)
            else:
                print('screen %d' % snum)
            print('\t%s' % str(screen))
            for fnum, frame in screen.frames.items():
                if self.curframe_num == frame.number:
                    print('\t*frame %d' % frame.number)
                else:
                    print('\tframe %d' % frame.number)
                print('\t\t%s' % str(frame))

    def current_frame(self):
        cf_ix = self._call_curframe()
        for snum, screen in self.screens.items():
            for fnum, frame in screen.frames.items():
                if fnum == cf_ix:
                    return frame
