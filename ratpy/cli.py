# -*- coding: utf-8 -*-

import sys
import argparse

from ratpy import RatPy as rp


def focus(args):

    rp.update()

    if args.direction == 'left':
        rp.global_focusleft()
    elif args.direction == 'right':
        rp.global_focusright()
    elif args.direction == 'up':
        rp.global_focusup()
    elif args.direction == 'down':
        rp.global_focusdown()
    else:
        print('Invalid argument for "focus"')


def main():
    """ratpy."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    focus_parser = subparsers.add_parser('focus')
    focus_parser.add_argument('direction',
                              type=str,
                              help='direction')
    focus_parser.set_defaults(func=focus)
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
