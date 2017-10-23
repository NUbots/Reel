#!/usr/bin/env python3

import os
from subprocess import Popen
from functools import partial

class Shell:
    class Command:
        def execute(self, command, build_args, **state):

            # Build our environment variables
            env = dict(os.environ)

            # Merge in extra env
            if 'env' in build_args:
                env.update(build_args['env'])

            print(' $ {}'.format(command.format(**state)))
            process = Popen(args=command.format(**state),
                            shell=True,
                            env=env)
            process.wait()

    def __init__(self, **commands):
        self.commands = commands

    def __call__(self, **build_args):

        v = Shell.Command()

        for k in self.commands:
            setattr(v, k, partial(v.execute, self.commands[k], build_args))

        return v
