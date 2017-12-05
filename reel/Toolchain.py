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
                 triple='',
                 c_flags=[],
                 cxx_flags=[],
                 fc_flags=[],
                 static=False,
                 parent_toolchain=None):

        self.name = name
        self.parent_toolchain = parent_toolchain

        # If we don't have a triple, work out the systems one
        if not triple:
            self.triple = subprocess.check_output(['cc', '-dumpmachine']).decode('utf-8').strip()

            # Non system toolchains are musl based
            if parent_toolchain != None:
                self.triple = self.triple.replace('gnu', 'musl')

        # Otherwise use the one provided
        else:
            self.triple = triple

        # Our arch is the first part of the triple
        self.arch = triple.split('-')[0]

        # If we are doing a static build, add -static to our flags
        if static:
            c_flags.insert(0, '-static')
            cxx_flags.insert(0, '-static')
            fc_flags.insert(0, '-static')

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
            'toolchain_name': self.name if self.name else 'root',
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
        if parent_toolchain == None:
            self.env = dict(os.environ.copy())

            # Update our path to include where we build binaries too
            self.env['PATH'] = '{}{}{}'.format(os.path.join(self.state['prefix_dir'], 'bin'), os.pathsep,
                                               self.env['PATH'])
            self.env['CROSS_COMPILE'] = ''
            self.env['CFLAGS'] = ' '.join(c_flags)
            self.env['CXXFLAGS'] = ' '.join(cxx_flags)
            self.env['FCFLAGS'] = ' '.join(fc_flags)

        # Otherwise we need to build our compiler
        else:
            # Take our environment from our parent toolchain and update it
            self.env = self.parent_toolchain.env.copy()

            self.env.update({
                # Extend the path
                'PATH': '{}{}{}'.format(os.path.join(self.state['prefix_dir'], 'bin'), os.pathsep,
                                        self.parent_toolchain.env['PATH']),

                # Overwrite the compiler and compiler flags
                'CC': '{}-gcc'.format(self.triple),
                'CXX': '{}-g++'.format(self.triple),
                'FC': '{}-gfortran'.format(self.triple),
                'AR': '{}-ar'.format(self.triple),
                'RANLIB': '{}-ranlib'.format(self.triple),
                'NM': '{}-nm'.format(self.triple),
                'CFLAGS': '{} --sysroot={} {}'.format(self.env['CFLAGS'], self.state['prefix_dir'], c_flags),
                'CXXFLAGS': '{} --sysroot={} {}'.format(self.env['CXXFLAGS'], self.state['prefix_dir'], cxx_flags),
                'FCFLAGS': '{} --sysroot={} {}'.format(self.env['FCFLAGS'], self.state['prefix_dir'], fc_flags),

                # Let all makes know they should treat this as a cross compilation
                'CROSS_COMPILE': '{}-'.format(self.triple),
            })

            # If we are not the system compiler, we are building a compiler
            self.add_tool(name='binutils',
                          url='https://ftpmirror.gnu.org/gnu/binutils/binutils-2.29.tar.xz',
                          configure_args=['--target={target_triple}',
                                          '--with-sysroot',
                                          '--disable-nls',
                                          '--disable-bootstrap',
                                          '--disable-werror',
                                          '--enable-shared',
                                          '--enable-static'],
                          install_targets=['install-strip'])

            self.add_tool(Shell(post_extract='cd {source} && ./contrib/download_prerequisites'),
                          name='gcc7',
                          url='https://ftpmirror.gnu.org/gnu/gcc/gcc-7.2.0/gcc-7.2.0.tar.xz',
                          configure_args=['--target="{target_triple}"',
                                          '--enable-languages=c,c++,fortran',
                                          '--with-sysroot="{prefix_dir}"',
                                          '--disable-nls',
                                          '--disable-multilib',
                                          '--disable-bootstrap',
                                          '--disable-werror',
                                          '--enable-shared',
                                          '--enable-static'],
                          build_targets=['all-gcc'],
                          install_targets=['install-strip-gcc'])

            self.add_library(name='musl',
                             url='https://www.musl-libc.org/releases/musl-1.1.18.tar.gz',
                             configure_args=['--target={arch}',
                                             '--syslibdir={prefix_dir}/lib',
                                             '--enable-shared'
                                             '--enable-static'])

            self.add_tool(Shell(post_extract='cd {source} && ./contrib/download_prerequisites'),
                          name='gcc7',
                          url='https://ftpmirror.gnu.org/gnu/gcc/gcc-7.2.0/gcc-7.2.0.tar.xz',
                          configure_args=['--target="{target_triple}"',
                                          '--enable-languages=c,c++,fortran',
                                          '--with-sysroot="{prefix_dir}"',
                                          '--disable-nls',
                                          '--disable-multilib',
                                          '--disable-bootstrap',
                                          '--disable-werror',
                                          '--enable-shared',
                                          '--enable-static'],
                          build_targets=['all-target-libgcc', 'all-target-libstdc++-v3'],
                          install_targets=['install-strip-target-libgcc', 'install-strip-target-libstdc++-v3'])

            self.add_library(name='libbacktrace',
                         url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
                         configure_args=['--target={target_triple}',
                                         '--enable-static',
                                         '--enable-shared'
                                         '--enable-static'],
                         install_targets=['install-strip'])


    # Build a tool we can run (Use our state but parents env)
    def add_tool(self, *args, **kwargs):

        # Update our own env with one if it's provided
        env = self.parent_toolchain.env.copy()
        if 'env' in kwargs:
            env.update(kwargs['env'])
        kwargs['env'] = env

        self.libraries.append(Library(self, SmartDownload, SmartExtract, SmartBuild, *args, **kwargs))


    # Build a library using our toolchain
    def add_library(self, *args, **kwargs):

        # Update our own env with one if it's provided
        env = self.env.copy()
        if 'env' in kwargs:
            env.update(kwargs['env'])
        kwargs['env'] = env

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

        for d in ['bin', 'include', 'lib']:
          try:
            os.makedirs(os.path.join(self.state['prefix_dir'], d), exist_ok=True)
          except:
            pass

        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(self.builds_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        cprint('Building toolchain {0} for {1}'.format(self.name if self.name else 'root', self.triple),
               'blue', attrs=['bold'])

        # Build all our libraries
        for l in self.libraries:
            l.build()
