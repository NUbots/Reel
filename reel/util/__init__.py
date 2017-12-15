#!/usr/bin/env python3

import os
import json
import textwrap


def indent(s, length=4):
    return '\n'.join([(' ' * length) + l for l in s.splitlines()])


def dedent(s):
    return textwrap.dedent(s)


def get_status(status_file):
    # Make sure the status directory exists.
    os.makedirs(os.path.dirname(status_file), exist_ok=True)

    # Make sure we have our status file.
    if not os.path.isfile(status_file):
        with open(status_file, 'w') as f:
            f.write('{}')

    with open(status_file, 'r') as f:
        return json.load(f)


def update_status(status_file, args):
    status = get_status(status_file)
    status.update(args)

    with open(status_file, 'w') as f:
        json.dump(status, f, indent=4, separators=(',', ': '), sort_keys=True)

    return status
