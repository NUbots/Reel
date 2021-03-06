#!/usr/bin/env python3

import os
from subprocess import Popen
from termcolor import cprint

from ..util import get_status, update_status, indent, get_paths


class AutotoolsBuild:

    def __init__(self, **build_args):

        # Set our default configuration arguments
        self.configure_args = {
            '--prefix': '{prefix_dir}',
            '--host': '{target_triple}',
            '--build': '{parent_target_triple}',
        }

        self.configure_args.update(build_args.get('configure_args', {}))

        # Unless specified otherwise, we always want to build static and shared versions of libraries
        if '--enable-shared' not in self.configure_args and '--disable-shared' not in self.configure_args:
            self.configure_args.update({'--enable-shared': True})

        if '--enable-static' not in self.configure_args and '--disable-static' not in self.configure_args:
            self.configure_args.update({'--enable-static': True})

        self.src_dir = build_args.get('src_dir', '.')
        self.build_postfix = build_args.get('build_postfix', '')
        self.build_args = build_args.get('build_args', {})
        self.install_args = build_args.get('install_args', {})

        # Grab our make and install targets
        self.build_targets = build_args.get('build_targets', ['all'])
        self.install_targets = build_args.get('install_targets', ['install'])

        # Because asshats
        self.in_source_build = build_args.get('in_source_build', False)

        # Build our environment variables
        self.env = dict(os.environ)

        # Merge in extra env
        if 'env' in build_args:
            self.env.update(build_args['env'])

    def autogen(self, **state):
        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        if os.path.isfile(os.path.join(src_path, 'autogen.sh')):
            # Load the status file.
            status = get_status(status_path)

            if 'autogen_pre_configure' not in status or not status['autogen_pre_configure']:
                # Make our build directory and log directory
                os.makedirs(build_path, exist_ok=True)
                os.makedirs(logs_path, exist_ok=True)

                # Open a log file and run configure
                with open(os.path.join(logs_path, '{}_autogen_pre_configure.log'.format(base_src)), 'w') as logfile:
                    self.env.update({'NOCONFIGURE': '1'})
                    cmd = os.path.abspath(os.path.join(src_path, 'autogen.sh'))
                    print(indent(' $ {}'.format(cmd), 8))
                    process = Popen(
                        args=cmd,
                        shell=True,
                        cwd=os.path.abspath(src_path),
                        env={k: v.format(**state)
                             for k, v in self.env.items()},
                        stdout=logfile,
                        stderr=logfile
                    )
                    if process.wait() != 0:
                        raise Exception('Failed to the autogen pre-configure step for {}'.format(base_src))

                    else:
                        status = update_status(status_path, {'autogen_pre_configure': True})

            else:
                cprint(
                    indent('Autogen pre-configure step for {} complete... Skipping...'.format(base_src), 8),
                    'yellow',
                    attrs=['bold']
                )

        return {'build': build_path, 'logs': logs_path}

    def configure(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Generate configure file if it does not already exist
        if not os.path.isfile(os.path.join(src_path, self.src_dir, 'configure')):
            self.autogen(**state)

        # Apply our state
        args = [
            '{}{}'.format(k, '={}'.format(v) if v is not True else '').format(**state)
            for k, v in self.configure_args.items()
            if v is not None
        ]

        # Load the status file
        status = get_status(status_path)

        if 'configure' not in status or not status['configure']:
            # Make our build directory and log directory
            os.makedirs(build_path, exist_ok=True)
            os.makedirs(logs_path, exist_ok=True)

            if 'clone' not in status or not status['clone']:
                if self.in_source_build:
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

            # Open a log file and run configure
            with open(os.path.join(logs_path, '{}_configure.log'.format(base_src)), 'w') as logfile:
                cmd = '{} {}'.format(
                    os.path.abspath(
                        os.path.join(src_path if not self.in_source_build else build_path, self.src_dir, 'configure')
                    ), ' '.join(args)
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
                    raise Exception('Failed to configure')

                else:
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

        # Otherwise run make for each of our targets
        for target in self.build_targets:
            if 'make_{}'.format(target) not in status or not status['make_{}'.format(target)]:
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make -j{} {} {}'.format(state['cpu_count'], ' '.join(args), target)
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
        for target in self.install_targets:
            if target not in status or not status[target]:
                with open(os.path.join(logs_path, '{}_make_{}.log'.format(base_src, target)), 'w') as logfile:
                    cmd = 'make {} {}'.format(' '.join(args), target)
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
