#!/usr/bin/env python

# from __future__ import print_function
import re

import sys
from argparse import ArgumentParser
from os import path
from pygit2 import *

pattern = re.compile(r'(?:bug|issue|fix|resolve|close)\s*\#?\s?(\d+)', re.IGNORECASE)


def getch():
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def find_issues(repo, since=None, until=None, reverse=False, interactive=False):
    walker = repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL)
    # walker.simplify_first_parent()

    if reverse:
        walker.sort(GIT_SORT_REVERSE | GIT_SORT_TOPOLOGICAL)
    if until:
        walker.reset()
        walker.push(until)
    if since:
        walker.hide(since)

    for commit in walker:
        match = pattern.search(commit.message)
        if match:
            if interactive:
                print('Save commit? [y]es [n]o [q]uit\n{0}'.decode('string_escape').format(
                    commit.message.decode('string_escape')), file=sys.stderr)
                ch = getch()
                if 'y' != ch:
                    continue
                elif 'q' == ch:
                    break
            print('{0} issue {1} ({2})'.format(commit.hex[:7], match.group(1), commit.commit_time))


def main():
    parser = ArgumentParser()
    parser.add_argument('--since', metavar='<revision>',
                        help='only consider commits from revision')
    parser.add_argument('--until', metavar='<revision>',
                        help='only consider commits to revision')
    parser.add_argument('--reverse', action='store_true',
                        help='output commits in reverse order')
    parser.add_argument('--interactive', action='store_true',
                        help='ask whether to save each matching commit')
    parser.add_argument('path',
                        help='the repository path')

    args = parser.parse_args()

    if not path.exists(args.path):
        parser.error("invalid path argument")

    repo = Repository(args.path)
    find_issues(repo, args.since, args.until, args.reverse, args.interactive)


if __name__ == '__main__':
    main()
