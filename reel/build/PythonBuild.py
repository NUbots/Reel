#!/usr/bin/env python3

import os
import sys
import shutil
from subprocess import Popen
from termcolor import cprint

from ..util import get_status, update_status, indent, dedent, get_paths


class PythonBuild:

    def __init__(self, **build_args):

        # Build our environment variables
        self.env = dict(os.environ)

        # Merge in extra env
        if 'env' in build_args:
            self.env.update(build_args['env'])

        # Set our default build arguments
        self.build_args = {
            '--parallel': '{cpu_count}',
            '--compiler': 'unix',
            '--executable': os.path.join('{prefix_dir}', 'bin', 'python3')
        }

        # Set our default install arguments
        self.install_args = {'--prefix': '{prefix_dir}'}

        self.src_dir = build_args.get('src_dir', '.')
        self.build_postfix = build_args.get('build_postfix', '')
        self.build_args.update(build_args.get('build_args', {}))
        self.install_args.update(build_args.get('install_args', {}))

    def configure(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Load the status file
        status = get_status(status_path)

        if 'configure' not in status or not status['configure']:
            # Wipe build folder before reconfigure
            if os.path.isdir(build_path):
                shutil.rmtree(build_path)

            # Make our build directory and log directory
            os.makedirs(build_path, exist_ok=True)
            os.makedirs(logs_path, exist_ok=True)

            if 'clone' not in status or not status['clone']:
                with open(os.path.join(logs_path, '{}_clone.log'.format(base_src)), 'w') as logfile:
                    cmd = 'cp -rv {} {}'.format(
                        os.path.abspath(os.path.join(src_path, self.src_dir, '*')), os.path.abspath(build_path)
                    )
                    print(indent(' $ {}'.format(cmd), 8))
                    process = Popen(
                        args=cmd,
                        shell=True,
                        cwd=os.path.abspath(build_path),
                        env={k: v.format(**state)
                             for k, v in self.env.items()},
                        stdout=logfile,
                        stderr=logfile
                    )

                    if process.wait() != 0:
                        raise Exception('Failed to clone')

                    else:
                        status = update_status(status_path, {'clone': True})

            status = update_status(status_path, {'configure': True})

        else:
            cprint(
                indent('Configure step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold']
            )

        return {'build': build_path, 'logs': logs_path}

    def build(self, **state):

        # Work out our real full paths
        _, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Apply our state
        args = [
            '{}{}'.format(k, '={}'.format(v) if v is not True else '').format(**state)
            for k, v in self.build_args.items()
            if v is not None
        ]

        # Load the status file
        status = get_status(status_path)

        if 'build' not in status or not status['build']:
            with open(os.path.join(logs_path, '{}_build.log'.format(base_src)), 'w') as logfile:
                cmd = '{} ./setup.py build {}'.format(sys.executable, ' '.join(args))
                print(indent(' $ {}'.format(cmd), 8))
                process = Popen(
                    args=cmd,
                    shell=True,
                    cwd=os.path.abspath(build_path),
                    env={k: v.format(**state)
                         for k, v in self.env.items()},
                    stdout=logfile,
                    stderr=logfile
                )
                if process.wait() != 0:
                    raise Exception('Failed to run build')

                else:
                    status = update_status(status_path, {'build': True})

        else:
            cprint(indent('Build step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold'])

    def install(self, **state):

        # Work out our real full paths
        _, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Apply our state
        args = [
            '{}{}'.format(k, '={}'.format(v) if v is not True else '').format(**state)
            for k, v in self.install_args.items()
            if v is not None
        ]

        # Load the status file
        status = get_status(status_path)

        # Open a log file and run make install
        if 'install' not in status or not status['install']:
            with open(os.path.join(logs_path, '{}_install.log'.format(base_src)), 'w') as logfile:
                cmd = '{} ./setup.py install {}'.format(sys.executable, ' '.join(args))
                print(indent(' $ {}'.format(cmd), 8))
                process = Popen(
                    args=cmd,
                    shell=True,
                    cwd=os.path.abspath(build_path),
                    env={k: v.format(**state)
                         for k, v in self.env.items()},
                    stdout=logfile,
                    stderr=logfile
                )

                if process.wait() != 0:
                    raise Exception('Failed to run install')

                else:
                    status = update_status(status_path, {'install': True})

        else:
            cprint(indent('Install step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold'])
