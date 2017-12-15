#!/usr/bin/env python3

import requests
import os
import stat
from termcolor import cprint

from ..util import get_status, update_status, indent

# Grab the latest config.sub from the intertubes
req = requests.get('https://raw.githubusercontent.com/gcc-mirror/gcc/master/config.sub', allow_redirects=True)

config_sub_file = req.content


class UpdateConfigSub:

    def __init__(self, **build_args):
        self.path = build_args.get('config_sub_file', 'config.sub')

    def post_extract(self, **state):

        src_path = os.path.basename(state['source'])
        status_path = os.path.join(state['status_dir'], '{}.json'.format(src_path))

        # Load the status file.
        status = get_status(status_path)

        if 'config_sub' not in status or not status['config_sub']:

            cprint(indent('Patching {} for {}'.format(self.path, src_path), 8), 'green', attrs=['bold'])

            dest_file = os.path.join(state['source'], self.path)

            # Correct permissions because some people are asshats!
            os.chmod(dest_file, os.stat(dest_file).st_mode | stat.S_IWUSR)

            with open(dest_file, 'wb') as f:
                f.write(config_sub_file)

            update_status(status_path, {'config_sub': True})

        else:
            cprint(
                indent('{}\'s {} already patched... Skipping...'.format(src_path, self.path), 8),
                'yellow',
                attrs=['bold']
            )
