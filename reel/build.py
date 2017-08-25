#!/usr/bin/env python3

import os
from subprocess import Popen
import multiprocessing

def build(toolchain, src, build, args=[], env={}, build_type='auto'):

    # Merge in os.environ
    sys_env = dict(os.environ)
    sys_env.update(env)
    env = sys_env

    # Work out our real full paths
    src_path = os.path.join(toolchain.src_path, src)
    build_path = os.path.join(toolchain.build_path, build)

    # If we are working out the build type
    if build_type == 'auto':

        # First check to see if we have a configure script
        if os.path.isfile(os.path.join(toolchain.src_path, src, 'configure')):
            build_type = 'autotools'
        elif os.path.isfile(os.path.join(toolchain.src_path, src, 'CMakeLists.txt')):
            build_type = 'cmake'
        elif os.path.isfile(os.path.join(toolchain.src_path, src, 'Makefile')):
            build_type = 'make'
        else:
            raise Exception('Could not determine build type for {}'.format(src))

    # Make our build directory
    os.makedirs(build_path, exist_ok=True)

    if build_type == 'autotools':

        # Open a log file and run configure
        with open(os.path.join(toolchain.logs_path, '{}_configure.log'.format(build)), 'w') as logfile:
            process = Popen(args=[os.path.abspath(os.path.join(toolchain.src_path, src, 'configure'))] + args,
                            cwd=os.path.abspath(build_path),
                            env=env,
                            stdout=logfile,
                            stderr=logfile)
            process.wait()

        # Open a log file and run make
        with open(os.path.join(toolchain.logs_path, '{}_make.log'.format(build)), 'w') as logfile:
            process = Popen(args=['make', '-j{}'.format(multiprocessing.cpu_count())],
                            cwd=os.path.abspath(build_path),
                            env=env,
                            stdout=logfile,
                            stderr=logfile)
            process.wait()

        # Open a log file and run make
        with open(os.path.join(toolchain.logs_path, '{}_make_install.log'.format(build)), 'w') as logfile:
            process = Popen(args=['make', 'install'],
                            cwd=os.path.abspath(build_path),
                            env=env,
                            stdout=logfile,
                            stderr=logfile)
            process.wait()

