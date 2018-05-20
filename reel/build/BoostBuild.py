#!/usr/bin/env python3

import os
import shutil
from subprocess import Popen
from termcolor import cprint

from ..util import get_status, update_status, indent, parse_args, dedent, get_paths


class BoostBuild:

    def __init__(self, **build_args):

        # Build our environment variables
        self.env = dict(os.environ)

        # Merge in extra env
        if 'env' in build_args:
            self.env.update(build_args['env'])

        # Set our default configuration arguments.
        self.configure_args = {'--prefix': '{prefix_dir}', '--with-toolset': 'gcc'}

        self.build_args = {
            'include': [os.path.join('{prefix_dir}', 'include'),
                        os.path.join('{prefix_dir}', 'include', 'python3.6m')],
            'library-path': '{prefix_dir}/lib',
            '-q': True,
            '-a': True,
            '--python-buildid': 'py36',
        }

        self.install_args = {
            '--prefix': '{prefix_dir}',
            'include': [os.path.join('{prefix_dir}', 'include'),
                        os.path.join('{prefix_dir}', 'include', 'python3.6m')],
            'library-path': '{prefix_dir}/lib',
            '-q': True,
            '--python-buildid': 'py36',
        }

        self.configure_args.update(build_args.get('configure_args', {}))
        self.src_dir = build_args.get('src_dir', '.')
        self.build_postfix = build_args.get('build_postfix', '')
        self.build_args.update(build_args.get('build_args', {}))
        self.install_args.update(build_args.get('install_args', {}))

        self.bjam_path = build_args.get('use_bjam', None)

        if self.bjam_path:
            self.configure_args.update({'--with-bjam': self.bjam_path})

        # Grab our make and install targets
        self.build_targets = build_args.get('build_targets', ['all'])
        self.install_targets = build_args.get('install_targets', ['install'])

        # Because asshats.
        self.in_source_build = build_args.get('in_source_build', False)

    def configure(self, **state):

        # Work out our real full paths
        src_path, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Apply our state
        args = parse_args(self.configure_args, **state)

        # Load the status file.
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

            # Make sure boost is going to use our compiler.
            template = dedent(
                """\
                # Configure specific gcc version, giving alternative name to use.
                using gcc : : {CXX} ;
                """
            ).format(CXX=os.path.join(state['prefix_dir'], 'bin', '{}-g++'.format(state['target_triple'])))

            with open(os.path.join(os.path.abspath(src_path), 'user-config.jam'), 'w') as config:
                config.write(template)

            # Open a log file and run configure
            with open(os.path.join(logs_path, '{}_configure.log'.format(base_src)), 'w') as logfile:
                cmd = '{}/bootstrap.sh {}'.format(os.path.abspath(os.path.join(src_path, self.src_dir)), ' '.join(args))
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
        args = parse_args(self.build_args, **state)

        # Load the status file.
        status = get_status(status_path)

        # Otherwise run make for each of our targets
        if len(self.build_targets) > 0:
            if 'make' not in status or not status['make']:
                with open(os.path.join(logs_path, '{}_make.log'.format(base_src)), 'w') as logfile:
                    cmd = '{} -j{} {}'.format(
                        self.bjam_path.format(**state)
                        if self.bjam_path else './bjam', state['cpu_count'], ' '.join(args)
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
                        raise Exception('Failed to run make')

                    else:
                        status = update_status(status_path, {'make': True})

            else:
                cprint(
                    indent('Build step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold']
                )

    def install(self, **state):

        # Work out our real full paths
        _, base_src, logs_path, build_path, status_path = get_paths(self.build_postfix, **state)

        # Apply our state
        args = parse_args(self.install_args, **state)

        # Load the status file.
        status = get_status(status_path)

        # Open a log file and run make install
        if len(self.install_targets) > 0:
            if 'install' not in status or not status['install']:
                with open(os.path.join(logs_path, '{}_install.log'.format(base_src)), 'w') as logfile:
                    cmd = '{} -j{} {} install'.format(
                        self.bjam_path.format(**state)
                        if self.bjam_path else './bjam', state['cpu_count'], ' '.join(args)
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
                        raise Exception('Failed to run install')

                    else:
                        status = update_status(status_path, {'install': True})

            else:
                cprint(
                    indent('Install step for {} complete... Skipping...'.format(base_src), 8), 'yellow', attrs=['bold']
                )
