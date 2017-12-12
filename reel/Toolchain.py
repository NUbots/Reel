#!/usr/bin/env python3

import os
import subprocess
from termcolor import cprint
import multiprocessing

from .download import SmartDownload
from .extract import SmartExtract
from .build import SmartBuild
from .Shell import Shell

from .Library import Library


class Toolchain:

    def __init__(
            self,
            name,
            gnu_mirror,
            triple='',
            c_flags=None,
            cxx_flags=None,
            fc_flags=None,
            static=False,
            parent_toolchain=None
    ):

        self.name = name
        self.parent_toolchain = parent_toolchain

        # If we don't have a triple, work out the systems one
        if not triple:
            self.triple = subprocess.check_output(['cc', '-dumpmachine']).decode('utf-8').strip()

            # Non system toolchains are musl based
            if parent_toolchain is not None:
                self.triple = self.triple.replace('gnu', 'musl')

        # Otherwise use the one provided
        else:
            self.triple = triple

        # Our arch is the first part of the triple
        self.arch = self.triple.split('-')[0]

        if c_flags is None:
            c_flags = []

        if cxx_flags is None:
            cxx_flags = []

        if fc_flags is None:
            fc_flags = []

        # Make sure we are always generating position independent code.
        if '-fPIC' not in c_flags:
            c_flags.append('-fPIC')
            cxx_flags.append('-fPIC')
            fc_flags.append('-fPIC')

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
        self.status_dir = os.path.join(self.working_dir, 'status')

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
            'status_dir': self.status_dir,
            'cpu_count': multiprocessing.cpu_count(),
        }

        # Embed our parents state into our state.
        if self.parent_toolchain is not None:
            self.state.update({'parent_{}'.format(k): v for (k, v) in self.parent_toolchain.state.items()})

        # If this is the system toolchain don't build anything but update our env
        if parent_toolchain is None:
            self.env = dict(os.environ.copy())

            # Update our path to include where we build binaries too
            self.env['PATH'] = '{}{}{}'.format(
                os.path.join(self.state['prefix_dir'], 'bin'), os.pathsep, self.env['PATH']
            )
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
                'PATH':
                    '{}{}{}'.format(
                        os.path.join(self.state['prefix_dir'], 'bin'), os.pathsep, self.parent_toolchain.env['PATH']
                    ),

                # Overwrite the compiler and compiler flags
                'CC': '{}-gcc'.format(self.triple),
                'CXX': '{}-g++'.format(self.triple),
                'FC': '{}-gfortran'.format(self.triple),
                'AR': '{}-ar'.format(self.triple),
                'RANLIB': '{}-ranlib'.format(self.triple),
                'NM': '{}-nm'.format(self.triple),
                'CFLAGS': ' '.join(c_flags),
                'CXXFLAGS': ' '.join(cxx_flags),
                'FCFLAGS': ' '.join(fc_flags),
                'LD_LIBRARY_PATH': os.path.abspath(os.path.join(self.prefix_dir, 'lib')),

                # Let all makes know they should treat this as a cross compilation
                'CROSS_COMPILE': '{}-'.format(self.triple),
            })

            # Build Binutils so we can link, ar, ranlib etc
            self.add_tool(
                name='binutils',
                url='{}/binutils/binutils-2.29.tar.xz'.format(gnu_mirror),
                configure_args={
                    '--host': self.parent_toolchain.triple,
                    '--build': self.parent_toolchain.triple,
                    '--target': '{target_triple}',
                    '--with-lib-path': os.path.join('{prefix_dir}', 'lib'),
                    '--with-sysroot': '"{prefix_dir}"',
                    '--disable-nls': True,
                    '--disable-bootstrap': True,
                    '--disable-werror': True,
                    '--enable-static': True,
                    '{}'.format('--enable-shared' if not static else '--disable-shared'): True
                },
                install_targets=['install-strip']
            )

            # We use this gcc build a few times, so make sure args are the same
            gcc_args = {
                'url': '{}/gcc/gcc-7.2.0/gcc-7.2.0.tar.xz'.format(gnu_mirror),
                'env': {
                    'CFLAGS_FOR_TARGET': self.env['CFLAGS'],
                    'CXXFLAGS_FOR_TARGET': self.env['CXXFLAGS'],
                    'FCFLAGS_FOR_TARGET': self.env['FCFLAGS'],
                    'LD_LIBRARY_PATH': os.path.join(self.prefix_dir, 'lib'),
                },
                'configure_args': {
                    '--host': self.parent_toolchain.triple,
                    '--build': self.parent_toolchain.triple,
                    '--target': '{target_triple}',
                    '--enable-languages': 'c,c++,fortran',
                    '--with-sysroot': '"{prefix_dir}"',
                    '--disable-nls': True,
                    '--disable-multilib': True,
                    '--disable-bootstrap': True,
                    '--disable-werror': True,
                    '{}'.format('--enable-shared' if not static else '--disable-shared'): True
                }
            }

            # Build gcc so we can build basic c programs (like musl)
            self.add_tool(
                Shell(post_extract='cd {source} && ./contrib/download_prerequisites'),
                Shell(
                    pre_configure='case $(uname -m) in'
                    '  x86_64)'
                    '    sed -e "/m64=/s/lib64/lib/" -i {source}/gcc/config/i386/t-linux64'
                    '  ;;'
                    'esac'
                ),
                name='gcc7',
                build_targets=['all-gcc'],
                install_targets=['install-strip-gcc'],
                **gcc_args
            )

            # Build our static musl (our c standard library)
            self.add_library(
                name='musl',
                url='https://www.musl-libc.org/releases/musl-1.1.18.tar.gz',
                configure_args={
                    '--target': '{target_triple}',
                    '--syslibdir': os.path.join('{prefix_dir}', 'lib'),
                    '--disable-shared': True,
                    '--enable-static': True
                }
            )

            # Build libgcc (our low level api)
            self.add_tool(
                Shell(
                    post_install='{prefix_dir}/bin/{target_triple}-gcc -dumpspecs'
                    ' | sed "s@/lib/ld-@{prefix_dir}/lib/ld-@g"'
                    ' > $(dirname $({prefix_dir}/bin/{target_triple}-gcc -print-libgcc-file-name))/specs'
                ),
                name='libgcc',
                build_targets=['all-target-libgcc'],
                install_targets=['install-strip-target-libgcc'],
                **gcc_args
            )

            # If we're not building a pure static toolchain, make shared libc
            if not static:
                self.add_library(
                    name='musl_shared',
                    build_postfix='_shared',
                    url='https://www.musl-libc.org/releases/musl-1.1.18.tar.gz',
                    configure_args={
                        '--target': '{target_triple}',
                        '--syslibdir': os.path.join('{prefix_dir}', 'lib'),
                        '--enable-shared': True,
                        '--disable-static': True
                    }
                )

            # Build the other gnu libraries
            self.add_tool(
                Shell(
                    pre_build='echo "{build}/gcc/"'
                    ' && {build}/gcc/xgcc -dumpspecs'
                    ' | sed "s@/lib/ld-@{prefix_dir}/lib/ld-@g"'
                    ' > {build}/gcc/specs'
                ),
                name='gnulibs',
                build_targets=[
                    'all-target-libstdc++-v3', 'all-target-libquadmath', 'all-target-libgfortran', 'all-target-libgomp'
                ],
                install_targets=[
                    'install-strip-target-libstdc++-v3', 'install-strip-target-libquadmath',
                    'install-strip-target-libgfortran', 'install-strip-target-libgomp'
                ],
                **gcc_args
            )

            # Libbacktrace is super useful
            self.add_library(
                name='libbacktrace',
                url='https://github.com/NUbots/libbacktrace/archive/master.tar.gz',
                configure_args={
                    '--enable-static': True,
                    '{}'.format('--enable-shared' if not static else '--disable-shared'): True
                },
                install_targets=['install-strip']
            )

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
            os.makedirs(os.path.join(self.state['prefix_dir'], d), exist_ok=True)

        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(self.builds_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.status_dir, exist_ok=True)

        cprint(
            'Building toolchain {0} with architecture {1}'.format(self.name if self.name else 'root', self.triple),
            'red',
            attrs=['bold']
        )

        # Build all our libraries
        for l in self.libraries:
            l.build()
