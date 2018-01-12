#!/usr/bin/env python3

import os
import sys
import traceback
from subprocess import Popen
from functools import partial
from termcolor import cprint

from .util import indent, get_status, update_status


class Python:

    class Command:

        def execute(self, phase, command, build_args, **state):

            # Build our environment variables
            env = dict(os.environ)

            # Merge in extra env
            if 'env' in build_args:
                env.update(build_args['env'])

            if 'source' in state:
                src_path = state['source']
                base_src = os.path.basename(src_path)
                status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))
                logs_path = os.path.join(state['logs_dir'], base_src)

            else:
                src_path = state['archive']
                base_src = os.path.basename(src_path)
                status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))
                logs_path = os.path.join(state['logs_dir'], base_src)

            # Load the status file
            status = get_status(status_path)

            if phase not in status or not status[phase]:
                os.makedirs(logs_path, exist_ok=True)

                with open(os.path.join(logs_path, '{}_{}.log'.format(base_src, phase)), 'w') as logfile:
                    try:
                        logfile.write('Attempting execution of python command ...\n')
                        new_state = command({k: v.format(**state) for k, v in env.items()}, log_file=logfile, **state)

                    except:
                        logfile.write('\n\nException: {} - {}\n'.format(sys.exc_info()[0], sys.exc_info()[1]))
                        traceback.print_tb(sys.exc_info()[2], file=logfile)
                        print(sys.exc_info()[0])
                        raise Exception('Failed to run phase {}'.format(phase))

                    else:
                        status = update_status(status_path, {phase: True})
                        return new_state

            else:
                cprint(
                    indent('{} step for {} complete... Skipping...'.format(phase, base_src), 8),
                    'yellow',
                    attrs=['bold']
                )

    def __init__(self, **commands):
        self.commands = commands

    def __call__(self, **build_args):

        v = Python.Command()

        for k in self.commands:
            setattr(v, k, partial(v.execute, k, self.commands[k], build_args))

        return v
