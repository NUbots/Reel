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


def get_paths(build_postfix, **state):
    src_path = state['source']
    base_src = '{}{}'.format(os.path.basename(src_path), build_postfix)
    logs_path = os.path.join(state['logs_dir'], base_src)
    build_path = os.path.join(state['builds_dir'], base_src)
    status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))

    return src_path, base_src, logs_path, build_path, status_path


def update_status(status_file, args):
    status = get_status(status_file)
    status.update(args)

    with open(status_file, 'w') as f:
        json.dump(status, f, indent=4, separators=(',', ': '), sort_keys=True)

    return status


def is_sequence(item):
    if not hasattr(item, "strip") and hasattr(item, "__getitem__") or hasattr(item, "__iter__"
                                                                              ) and not isinstance(item, str):
        return True
    else:
        return False


def parse_args(dict_args, **state):
    args = []

    for k, v in dict_args.items():
        if v is not None:
            if is_sequence(v):
                args = args + ['{}={}'.format(k, val).format(**state) for val in v]
            elif v is not True:
                args.append('{}={}'.format(k, v).format(**state))
            else:
                args.append(k)

    return args


def is_sequence(item):
    if isinstance(item, (str, bytes)):
        return False
    elif not hasattr(item, "strip") and hasattr(item, "__getitem__") or hasattr(item, "__iter__"):
        return True
    else:
        return False
