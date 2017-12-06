#!/usr/bin/env python3

import os
import json
from subprocess import Popen
import multiprocessing
from termcolor import cprint

from ..util import get_status, update_status

class AutotoolsBuild:
    def __init__(self, **build_args):

        # Grab our configure args if they exist
        self.configure_args = build_args.get('configure_args', [])
        self.build_args = build_args.get('build_args', [])
        self.install_args = build_args.get('install_args', [])

        # Grab our make and install targets
        self.build_targets = build_args.get('build_targets', ['all'])
        self.install_targets = build_args.get('install_targets', ['install'])

        # Add our prefix to the args
        self.configure_args.append('--prefix={prefix_dir}')

        # Build our environment variables
        self.env = dict(os.environ)

        # Merge in extra env
        if 'env' in build_args:
            self.env.update(build_args['env'])

    def configure(self, **state):

        # Apply our state
        args = [c.format(**state) for c in self.configure_args]

        # Work out our real full paths
        src_path = state['source']
        base_src = os.path.basename(src_path)
        logs_path = os.path.join(state['logs_dir'], base_src)
        build_path = os.path.join(state['builds_dir'], base_src)
        status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))

        # Load the status file.
        status = get_status(status_path)

        if 'configure' not in status or not status['configure']:
            # Make our build directory and log directory
            os.makedirs(build_path, exist_ok=True)
            os.makedirs(logs_path, exist_ok=True)

            # Open a log file and run configure
            with open(os.path.join(logs_path, '{}_configure.log'.format(base_src)), 'w') as logfile:
                cmd = '{} {}'.format(os.path.abspath(os.path.join(src_path, 'configure')), ' '.join(args))
                print(' $ {}'.format(cmd))
                process = Popen(args=cmd,
                                shell=True,
                                cwd=os.path.abspath(build_path),
                                env=self.env,
                                stdout=logfile,
                                stderr=logfile)
                if process.wait() != 0:
                    raise Exception('Failed to configure')

                else:
                    status = update_status(status_path, {'configure': True})

        else:
            cprint('Configure step for {} complete... Skipping...'.format(base_src), 'yellow', attrs=['bold'])

        return { 'build': build_path, 'logs': logs_path }


    def build(self, **state):

        src_path = state['source']
        base_src = os.path.basename(src_path)
        logs_path = state['logs']
        build_path = state['build']
        status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))

        # Load the status file.
        status = get_status(status_path)

        # Otherwise run make for each of our targets
        for target in self.build_targets:
            if 'make_{}'.format(target) not in status or not status['make_{}'.format(target)]:
                print(' $ {}'.format(' '.join(['make', '-j{} {}'.format(multiprocessing.cpu_count(), ' '.join(a.format(**state) for a in self.build_args)), target])))
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make -j{} {}'.format(multiprocessing.cpu_count(), target)
                    process = Popen(args=cmd,
                                    shell=True,
                                    cwd=os.path.abspath(build_path),
                                    env=self.env,
                                    stdout=logfile,
                                    stderr=logfile)
                    if process.wait() != 0:
                        raise Exception('Failed to run make {}'.format(target))

                    else:
                        status = update_status(status_path, {'make_{}'.format(target): True})

            else:
                cprint('Build step {} for {} complete... Skipping...'.format(target, base_src), 'yellow', attrs=['bold'])

    def install(self, **state):

        src_path = state['source']
        base_src = os.path.basename(src_path)
        logs_path = state['logs']
        build_path = state['build']
        status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))

        # Load the status file.
        status = get_status(status_path)

        # Open a log file and run make install
        for target in self.install_targets:
            if target not in status or not status[target]:
                print(' $ {}'.format(' '.join(['make', target])))
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make {}'.format(target)
                    process = Popen(args=cmd,
                                    shell=True,
                                    cwd=os.path.abspath(build_path),
                                    env=self.env,
                                    stdout=logfile,
                                    stderr=logfile)

                    if process.wait() != 0:
                        raise Exception('Failed to run make {}'.format(target))

                    else:
                        status = update_status(status_path, {target: True})

            else:
                cprint('Install step {} for {} complete... Skipping...'.format(target, base_src), 'yellow', attrs=['bold'])
