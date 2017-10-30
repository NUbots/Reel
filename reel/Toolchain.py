#!/usr/bin/env python3

import os
import platform
import subprocess
from termcolor import cprint

from .download import SmartDownload
from .extract import SmartExtract
from .build import SmartBuild
from .Shell import Shell

from .Library import Library

class Toolchain:

    def __init__(self,
                 name,
                 arch=platform.machine(),
                 triple='',
                 c_flags='',
                 cxx_flags='',
                 fc_flags='',
                 system=False,
                 build_toolchain=None):

        self.name = name
        self.arch = arch

        # If we don't have a triple, work out the systems one
        if not triple:
            self.triple = subprocess.check_output(['cc', '-dumpmachine']).decode('utf-8').strip()
            self.triple = self.triple.replace('gnu', 'musl')
        # Otherwise use the one provided
        else:
            self.triple = triple

        # Global directories
        self.toolchain_dir = 'toolchain'
        self.setup_dir = os.path.join(self.toolchain_dir, 'setup')
        self.archives_dir = os.path.join(self.setup_dir, 'archive')
        self.sources_dir = os.path.join(self.setup_dir, 'src')

        # Toolchain directories
        self.prefix_dir = os.path.join(self.toolchain_dir, self.name)
        self.working_dir = os.path.join(self.setup_dir, self.name if self.name else 'root')
        self.builds_dir = os.path.join(self.working_dir, 'build')
        self.logs_dir = os.path.join(self.working_dir, 'log')

        self.libraries = []

        self.state = {
            'toolchain_name': self.name,
            'arch': self.arch,
            'target_triple': self.triple,
            'toolchain_dir': self.toolchain_dir,
            'setup_dir': self.setup_dir,
            'archives_dir': self.archives_dir,
            'sources_dir': self.sources_dir,
            'prefix_dir': os.path.abspath(self.prefix_dir),
            'working_dir': self.working_dir,
            'builds_dir': self.builds_dir,
            'logs_dir': self.logs_dir,
        }

        # If this is the system toolchain don't build anything but update our env
        if system:
            self.env = {
                'CFLAGS': c_flags,
                'CXXFLAGS': cxx_flags,
                'FCFLAGS': fc_flags
            }

        # Otherwise we need to build our compiler
        else:
            # This env data
            self.env = {
                'PATH': '{}/bin{}{}'.format(self.prefix_dir, os.pathsep, os.environ.get('PATH', '')),
                'CC': '{}-gcc'.format(self.triple),
                'CXX': '{}-g++'.format(self.triple),
                'FC': '{}-gfortran'.format(self.triple),
                'CFLAGS': c_flags,
                'CXXFLAGS': cxx_flags,
                'FCFLAGS': fc_flags,
                'CROSS_COMPILE': ' ',
            }

            build_env = build_toolchain.env if build_toolchain else {
                'CROSS_COMPILE': ' '
            }

            # Add our cross compiling tools
            self.add_library(name='musl',
                             url='https://www.musl-libc.org/releases/musl-1.1.17.tar.gz',
                             configure_args=['--target={arch}',
                                             '--syslibdir={prefix_dir}/lib',
                                             '--disable-shared'],
                             env=build_env)

            self.add_library(name='binutils',
                             url='https://ftpmirror.gnu.org/gnu/binutils/binutils-2.29.tar.xz',
                             configure_args=['--target={target_triple}',
                                             '--with-sysroot',
                                             '--disable-nls',
                                             '--disable-bootstrap',
                                             '--disable-werror'],
                             install_targets=['install-strip'],
                             env=build_env)

            self.add_library(Shell(post_extract='cd {source} && ./contrib/download_prerequisites'),
                             name='gcc7',
                             url='https://ftpmirror.gnu.org/gnu/gcc/gcc-7.2.0/gcc-7.2.0.tar.xz',
                             configure_args=['--target="{target_triple}"',
                                             '--enable-languages=c,c++,fortran',
                                             '--with-sysroot="{prefix_dir}"',
                                             '--disable-nls',
                                             '--disable-multilib',
                                             '--disable-bootstrap',
                                             '--disable-werror',
                                             '--disable-shared'],
                             make_targets=['all-gcc',
                                           'all-target-libgcc',
                                           'all-target-libstdc++-v3'],
                             install_targets=['install-strip-gcc',
                                              'install-strip-target-libgcc',
                                              'install-strip-target-libstdc++-v3'],
                             env=build_env)

            self.add_library(name='libbacktrace',
                             url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
                             configure_args=['--enable-static',
                                             '--disable-shared'],
                             install_targets=['install-strip'],
                             env=build_env)


    def add_library(self, *args, **kwargs):
        self.libraries.append(Library(self, SmartDownload, SmartExtract, SmartBuild, *args, **kwargs))


    def build(self):

        # Make our directories if they do not already exist
        os.makedirs(self.prefix_dir, exist_ok=True)

        if os.path.exists(os.path.join(self.state['prefix_dir'], 'usr')):
            if not os.path.islink(os.path.join(self.state['prefix_dir'], 'usr')):
                os.path.unlink(os.path.join(self.state['prefix_dir'], 'usr'))
                os.symlink(self.state['prefix_dir'], os.path.join(self.state['prefix_dir'], 'usr'))

        else:
            os.symlink(self.state['prefix_dir'], os.path.join(self.state['prefix_dir'], 'usr'))

        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(self.builds_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        cprint('Building toolchain {0} for {1}'.format(self.name, self.triple), 'blue', attrs=['bold'])

        # Build all our libraries
        for l in self.libraries:
            l.build()
