#!/usr/bin/env python3

import os
from subprocess import Popen
from functools import partial
from termcolor import cprint

from .util import indent, get_status, update_status


class Shell:
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
                status_path = os.path.join(state['status_dir'],
                                           '{}.json'.format(base_src))

            else:
                src_path = state['archive']
                base_src = os.path.basename(src_path)
                status_path = os.path.join(state['status_dir'],
                                           '{}.json'.format(base_src))

            # Load the status file.
            status = get_status(status_path)

            if phase not in status or not status[phase]:
                with open(
                        os.path.join(state['logs_dir'], '{}_{}.log'.format(
                            base_src, phase)), 'w') as logfile:
                    print(indent(' $ {}'.format(command.format(**state)), 8))
                    process = Popen(
                        args=command.format(**state),
                        shell=True,
                        env=env,
                        stdout=logfile,
                        stderr=logfile)

                    if process.wait() != 0:
                        raise Exception('Failed to run phase {}'.format(phase))

                    else:
                        status = update_status(status_path, {phase: True})

            else:
                cprint(
                    indent('{} step for {} complete... Skipping...'.format(
                        phase, base_src), 8),
                    'yellow',
                    attrs=['bold'])

    def __init__(self, **commands):
        self.commands = commands

    def __call__(self, **build_args):

        v = Shell.Command()

        for k in self.commands:
            setattr(v, k, partial(v.execute, k, self.commands[k], build_args))

        return v
