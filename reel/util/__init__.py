#!/usr/bin/env python3

import os
import json

def get_status(status_file):
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

