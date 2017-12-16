#!/usr/bin/env python3

import os
from subprocess import Popen
from termcolor import cprint

from ..util import get_status, update_status, indent


class MakeBuild:

    def __init__(self, **build_args):

        # Set our default configuration arguments.
        self.configure_args = {
            '--prefix': '{prefix_dir}',
            '--host': '{target_triple}',
            '--build': '{parent_target_triple}'
        }

        self.src_dir = build_args.get('src_dir', '.')
        self.build_postfix = build_args.get('build_postfix', '')
        self.build_args = build_args.get('build_args', [])
        self.install_args = build_args.get('install_args', [])

        # Grab our make and install targets
        self.build_targets = build_args.get('build_targets', ['all'])
        self.install_targets = build_args.get('install_targets', ['install'])

        # Build our environment variables
        self.env = dict(os.environ)

        # Merge in extra env
        if 'env' in build_args:
            self.env.update(build_args['env'])

    def configure(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = self.get_paths(state)

        # Load the status file.
        status = get_status(status_path)

        if 'configure' not in status or not status['configure']:
            # Make our build directory and log directory
            os.makedirs(build_path, exist_ok=True)
            os.makedirs(logs_path, exist_ok=True)

            with open(os.path.join(logs_path, '{}_configure.log'.format(base_src)), 'w') as logfile:
                cmd = 'cp -r {} {}/'.format(
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
                    raise Exception('Failed to run configure')

                else:
                    status = update_status(status_path, {'configure': True})

        else:
            cprint(
                indent('Configure step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold']
            )

        return {'build': build_path, 'logs': logs_path}

    def build(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = self.get_paths(state)

        # Load the status file.
        status = get_status(status_path)

        # Otherwise run make for each of our targets
        for target in self.build_targets:
            if 'make_{}'.format(target) not in status or not status['make_{}'.format(target)]:
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make -j{} {} {}'.format(
                        state['cpu_count'], ' '.join(a.format(**state) for a in self.build_args), target
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
                        raise Exception('Failed to run make {}'.format(target))

                    else:
                        status = update_status(status_path, {'make_{}'.format(target): True})

            else:
                cprint(
                    indent('Build step {} for {} complete... Skipping...'.format(target, base_src), 8),
                    'yellow',
                    attrs=['bold']
                )

    def install(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = self.get_paths(state)

        # Load the status file.
        status = get_status(status_path)

        # Open a log file and run make install
        for target in self.install_targets:
            if target not in status or not status[target]:
                print(indent(' $ {}'.format(' '.join(['make', target])), 8))
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make PREFIX={} {} {}'.format(
                        state['prefix_dir'], ' '.join(a.format(**state) for a in self.install_args), target
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
                        raise Exception('Failed to run make {}'.format(target))

                    else:
                        status = update_status(status_path, {target: True})

            else:
                cprint(
                    indent('Install step {} for {} complete... Skipping...'.format(target, base_src), 8),
                    'yellow',
                    attrs=['bold']
                )

    def get_paths(self, state):
        src_path = state['source']
        base_src = '{}{}'.format(os.path.basename(src_path), self.build_postfix)
        logs_path = os.path.join(state['logs_dir'], base_src)
        build_path = os.path.join(state['builds_dir'], base_src)
        status_path = os.path.join(state['status_dir'], '{}.json'.format(base_src))

        return src_path, base_src, logs_path, build_path, status_path
