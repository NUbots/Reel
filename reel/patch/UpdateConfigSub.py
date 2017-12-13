#!/usr/bin/env python3

import requests
import os
from termcolor import cprint

from ..util import get_status, update_status, indent

# Grab the latest config.sub from the intertubes
req = requests.get('https://raw.githubusercontent.com/gcc-mirror/gcc/master/config.sub', allow_redirects=True)

config_sub_file = req.content


class UpdateConfigSub:

    def __init__(self, config_sub_file, **build_args):
        self.path = config_sub_file

    def post_extract(self, **state):

        src_path = os.path.basename(state['source'])
        status_path = os.path.join(state['status_dir'], '{}.json'.format(src_path))

        # Load the status file.
        status = get_status(status_path)

        if 'config_sub' not in status or not status['config_sub']:

            cprint(indent('Patching {} for {}'.format(self.path, src_path), 8), 'green', attrs=['bold'])

            with open(os.path.join(state['source'], self.path), 'wb') as f:
                f.write(config_sub_file)

            update_status(status_path, {'config_sub': True})

        else:
            cprint(
                indent('{}\'s {} already patched... Skipping...'.format(src_path, self.path), 8),
                'yellow',
                attrs=['bold']
            )
