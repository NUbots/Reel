#!/usr/bin/env python3

import os
import re
import sys
import subprocess
from termcolor import cprint
import multiprocessing

from .build import SmartBuild
from .download import SmartDownload
from .extract import SmartExtract
from .Library import Library
from .patch import UpdateConfigSub
from .Patch import Patch
from .Shell import Shell
from .Python import Python
from .util import dedent


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
            parent_toolchain=None,
            abi='64'
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

        # Are we building for a 32-bit or a 64-bit ABI?
        self.abi = abi

        self.c_flags = c_flags.copy() if c_flags is not None else []
        self.cxx_flags = cxx_flags.copy() if cxx_flags is not None else []
        self.fc_flags = fc_flags.copy() if fc_flags is not None else []

        # Global directories
        self.toolchain_dir = 'toolchain'
        self.setup_dir = os.path.join(self.toolchain_dir, 'setup')
        self.archives_dir = os.path.join(self.setup_dir, 'archive')
        self.sources_dir = os.path.join(self.setup_dir, 'src')
        self.patches_dir = os.path.join(self.setup_dir, 'patches')

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
            'patches_dir': self.patches_dir,
            'prefix_dir': os.path.abspath(self.prefix_dir),
            'working_dir': self.working_dir,
            'builds_dir': self.builds_dir,
            'logs_dir': self.logs_dir,
            'status_dir': self.status_dir,
            'cpu_count': multiprocessing.cpu_count(),
            'c_flags': self.c_flags.copy(),
            'cxx_flags': self.cxx_flags.copy(),
            'fc_flags': self.fc_flags.copy()
        }

        # Make sure we are always generating position independent code
        if '-fPIC' not in self.c_flags:
            self.c_flags.append('-fPIC')
            self.cxx_flags.append('-fPIC')
            self.fc_flags.append('-fPIC')

        # If we are doing a static build, add -static to our flags
        if static and '-static' not in self.c_flags:
            self.c_flags.insert(0, '-static')
            self.cxx_flags.insert(0, '-static')
            self.fc_flags.insert(0, '-static')

        # Embed our parents state into our state
        if self.parent_toolchain is not None:
            self.state.update({'parent_{}'.format(k): v for (k, v) in self.parent_toolchain.state.items()})
        # Otherwise pretend that we are our own parent
        else:
            self.state.update({'parent_{}'.format(k): v for (k, v) in self.state.items()})

        # If this is the system toolchain don't build anything but update our env
        if parent_toolchain is None:
            self.env = dict(os.environ.copy())

            # System toolchains need environment too
            self.env.update({
                # Update our path to include where we build binaries too
                'PATH': os.pathsep.join([os.path.join(self.state['prefix_dir'], 'bin'), self.env['PATH']]),
                'CFLAGS': ' '.join(self.c_flags),
                'CXXFLAGS': ' '.join(self.cxx_flags),
                'FCFLAGS': ' '.join(self.fc_flags),
                'CPATH': os.path.join('{prefix_dir}', 'include'),
                'LIBRARY_PATH': os.path.join(self.state['prefix_dir'], 'lib'),
                'LD_LIBRARY_PATH': os.path.join(self.state['prefix_dir'], 'lib'),
                'CROSS_COMPILE': '',
                'PKG_CONFIG_PATH':
                    os.pathsep.join([
                        os.path.join('{prefix_dir}', 'lib', 'pkgconfig'),
                        os.path.join('{prefix_dir}', 'share', 'pkgconfig')
                    ]),
            })

            # If our environment doesn't already have a CC or CXX use cc and c++
            if 'CC' not in self.env:
                self.env['CC'] = 'cc'
            if 'CXX' not in self.env:
                self.env['CXX'] = 'c++'

        # Otherwise we need to build our compiler
        else:
            # Take our environment from our parent toolchain and update it
            self.env = self.parent_toolchain.env.copy()

            self.env.update({
                # Extend the path
                'PATH':
                    os.pathsep.join([
                        os.path.join(self.state['prefix_dir'], 'bin'),
                        os.path.join(self.state['prefix_dir'], self.triple, 'bin'), self.env['PATH']
                    ]),

                # Overwrite the compiler and compiler flags
                'CC': '{}-gcc'.format(self.triple),
                'CPP': '{}-gcc -E'.format(self.triple),
                'CXX': '{}-g++'.format(self.triple),
                'CXXCPP': '{}-g++ -E'.format(self.triple),
                'FC': '{}-gfortran'.format(self.triple),
                'AR': '{}-ar'.format(self.triple),
                'RANLIB': '{}-ranlib'.format(self.triple),
                'NM': '{}-nm'.format(self.triple),
                'CFLAGS': ' '.join(self.c_flags),
                'CXXFLAGS': ' '.join(self.cxx_flags),
                'FCFLAGS': ' '.join(self.fc_flags),
                'LD_LIBRARY_PATH': '',
                'PKG_CONFIG_PATH':
                    os.pathsep.join([
                        os.path.join(self.state['prefix_dir'], 'lib', 'pkgconfig'),
                        os.path.join(self.state['prefix_dir'], 'share', 'pkgconfig')
                    ]),

                # Let all makes know they should treat this as a cross compilation
                'CROSS_COMPILE': '{}-'.format(self.triple),
            })

            # Build Binutils so we can link, ar, ranlib etc
            self.add_tool(
                name='binutils',
                url='{}/binutils/binutils-2.30.tar.xz'.format(gnu_mirror),
                configure_args={
                    '--host': self.parent_toolchain.triple,
                    '--build': self.parent_toolchain.triple,
                    '--target': '{target_triple}',
                    '--with-lib-path': os.pathsep.join([os.path.join('=', 'usr', 'lib'),
                                                        os.path.join('=', 'usr', 'lib64'),
                                                        os.path.join('=', 'usr', '{target_triple}', 'lib'),
                                                        os.path.join('=', 'usr', '{target_triple}', 'lib64')]),
                    '--with-sysroot': '"{prefix_dir}"',
                    '--disable-nls': True,
                    '--disable-bootstrap': True,
                    '--disable-werror': True,
                    '--enable-static': True,
                    '{}'.format('--enable-shared' if not static else '--disable-shared'): True,
                    '--enable-64-bit-bfd': True,
                    '--enable-plugins': True,
                },
                install_targets=['install-strip']
            )

            # We use this gcc build a few times, so make sure args are the same
            gcc_args = {
                'url': '{}/gcc/gcc-8.1.0/gcc-8.1.0.tar.xz'.format(gnu_mirror),
                'env': {
                    'CFLAGS_FOR_TARGET': self.env['CFLAGS'],
                    'CXXFLAGS_FOR_TARGET': self.env['CXXFLAGS'],
                    'FCFLAGS_FOR_TARGET': self.env['FCFLAGS'],
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
                    '--enable-libquadmath': True,
                    '--enable-libquadmath-support': True,
                    '{}'.format('--enable-shared' if not static else '--disable-shared'): True
                }
            }

            # Build gcc so we can build basic c programs (like musl)
            # gcc x86 has a "bug"
            # error: declaration of 'int posix_memalign(void**, size_t, size_t) throw ()' has a different exception specifier
            # Only x86 + musl produces this error, apparently glibc actually has the exception specifier, but musl doesn't
            # https://github.com/android-ndk/ndk/issues/91
            gcc_patch = dedent(
                """\
            --- a/gcc/config/i386/pmm_malloc.h
            +++ b/gcc/config/i386/pmm_malloc.h
            @@ -31,8 +31,12 @@
             #ifndef __cplusplus
             extern int posix_memalign (void **, size_t, size_t);
             #else
            +#ifdef __GLIBC__
             extern "C" int posix_memalign (void **, size_t, size_t) throw ();
            -#endif
            +#else
            +extern "C" int posix_memalign (void **, size_t, size_t);
            +#endif  // __GLIBC__
            +#endif  // __cplusplus

             static __inline void *
             _mm_malloc (size_t __size, size_t __alignment)
             {{
               void * __ptr;
            """
            )
            self.add_tool(
                name='gcc',
                phases=[Python(post_extract=gcc_post_extract),
                        Patch(pre_configure=gcc_patch)],
                build_targets=['all-gcc'],
                install_targets=['install-strip-gcc'],
                **gcc_args
            )

            # Build our static musl (our c standard library)
            self.add_library(
                name='musl',
                url='https://www.musl-libc.org/releases/musl-1.1.19.tar.gz',
                configure_args={
                    '--target': '{target_triple}',
                    '--syslibdir': os.path.join('{prefix_dir}', 'lib'),
                    '--disable-shared': True,
                    '--enable-static': True
                }
            )

            # Build libgcc (our low level api)
            self.add_tool(
                name='libgcc',
                phases=[Python(post_install=gcc_post_install)],
                build_targets=['all-target-libgcc'],
                install_targets=['install-strip-target-libgcc'],
                **gcc_args
            )

            # If we're not building a pure static toolchain, make shared libc
            if not static:
                self.add_library(
                    name='musl_shared',
                    url='https://www.musl-libc.org/releases/musl-1.1.19.tar.gz',
                    build_postfix='_shared',
                    phases=[Python(post_install=musl_post_install)],
                    configure_args={
                        '--target': '{target_triple}',
                        '--syslibdir': os.path.join('{prefix_dir}', 'lib'),
                        '--enable-shared': True,
                        '--disable-static': True
                    }
                )

            # Build the other gnu libraries
            self.add_tool(
                name='gnulibs',
                phases=[Python(pre_build=gnulibs_pre_build, pre_install=generate_toolchain_files)],
                build_targets=[
                    'all-target-libstdc++-v3', 'all-target-libquadmath', 'all-target-libgfortran', 'all-target-libgomp'
                ],
                install_targets=[
                    'install-strip-target-libstdc++-v3', 'install-strip-target-libquadmath',
                    'install-strip-target-libgfortran', 'install-strip-target-libgomp'
                ],
                **gcc_args
            )

    # Build a tool we can run (Use our state but parents env)
    def add_tool(self, phases=None, **kwargs):

        # Update our own env with one if it's provided
        env = self.parent_toolchain.env.copy()
        if 'env' in kwargs:
            env.update(kwargs['env'])
        kwargs['env'] = env

        default_phases = [SmartDownload, SmartExtract, SmartBuild]

        if phases is not None:
            default_phases.extend(phases)

        self.libraries.append(Library(self, default_phases, **kwargs))

    # Build a library using our toolchain
    def add_library(self, phases=None, **kwargs):

        # Update our own env with one if it's provided
        env = self.env.copy()
        if 'env' in kwargs:
            env.update(kwargs['env'])
        kwargs['env'] = env

        default_phases = [SmartDownload, SmartExtract, SmartBuild]

        if phases is not None:
            default_phases.extend(phases)

        self.libraries.append(Library(self, default_phases, **kwargs))

    def install_compression_libraries(self, **kwargs):

        if kwargs.get('xz', False):
            self.add_library(name='xz', url='https://tukaani.org/xz/xz-5.2.3.tar.xz')

        if kwargs.get('bzip2', False):
            self.add_library(name='bzip2', url='https://github.com/Bidski/bzip2/archive/master.tar.gz')

        if kwargs.get('zlib', False):
            self.add_library(
                name='zlib',
                url='http://www.zlib.net/zlib-1.2.11.tar.gz',
                configure_args={
                    # zlib has a special configure which doesn't understand the usual options
                    '--host': None,
                    '--build': None,
                    '--enable-static': None,
                    '--enable-shared': None,

                    # Enable static and shared build for zlib
                    '--static': True,
                    '--shared': True
                }
            )

    def install_X11(self, **kwargs):

        self.add_library(
            name='freetype',
            url='https://downloads.sourceforge.net/freetype/freetype-2.9.tar.bz2',
            phases=[
                Shell(
                    post_extract='cd {source}'
                    ' && sed -ri "s:.*(AUX_MODULES.*valid):\\1:" modules.cfg '
                    ' && sed -ri "s:.*(#.*SUBPIXEL_RENDERING) .*:\\1:" include/freetype/config/ftoption.h'
                )
            ],
            configure_args={
                '--with-harfbuzz': 'no',
                '--with-zlib': 'yes',
                '--with-bzip2': 'yes',
                '--with-png': 'yes'
            }
        )

        self.add_library(
            name='fontconfig',
            url='https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.13.0.tar.bz2',
            phases=[Shell(post_extract='cd {source} && rm -f src/fcobjshash.h')],
            configure_args={
                '--disable-docs': True
            }
        )

        self.add_library(url='https://www.x.org/pub/individual/util/util-macros-1.19.2.tar.bz2', name='util-macros')

        self.add_library(name='xcb-proto', url='https://xcb.freedesktop.org/dist/xcb-proto-1.13.tar.bz2')

        # yapf: disable
        xorg_protos = [
            ('applewmproto',             '1.4.2'),
            ('bigreqsproto',             '1.1.2'),
            ('compositeproto',           '0.4.2'),
            ('damageproto',              '1.2.1'),
            ('dmxproto',                 '2.3.1'),
            ('dri2proto',                '2.8'),
            ('dri3proto',                '1.0'),
            ('fixesproto',               '5.0'),
            ('fontsproto',               '2.1.3'),
            ('glproto',                  '1.4.17'),
            ('inputproto',               '2.3.2'),
            ('kbproto',                  '1.0.7'),
            ('presentproto',             '1.1'),
            ('randrproto',               '1.5.0'),
            ('recordproto',              '1.14.2'),
            ('renderproto',              '0.11.1'),
            ('resourceproto',            '1.2.0'),
            ('scrnsaverproto',           '1.2.2'),
            ('trapproto',                '3.4.3'),
            ('videoproto',               '2.3.3'),
            ('windowswmproto',           '1.0.4'),
            ('xcmiscproto',              '1.2.2'),
            ('xextproto',                '7.3.0'),
            ('xf86bigfontproto',         '1.2.0'),
            ('xf86dgaproto',             '2.1'),
            ('xf86driproto',             '2.1.1'),
            ('xf86miscproto',            '0.9.3'),
            ('xf86vidmodeproto',         '2.3.1'),
            ('xineramaproto',            '1.2.1'),
            ('xproto',                   '7.0.31'),
            ('xproxymanagementprotocol', '1.0.3')
        ]
        # yapf: enable

        for proto in xorg_protos:
            self.add_library(
                name='xorg-protocol-header-{}'.format(proto[0]),
                url='https://www.x.org/pub/individual/proto/{}-{}.tar.bz2'.format(*proto),
                phases=[UpdateConfigSub]
            )

        self.add_library(name='Xdmcp', url='https://www.x.org/pub/individual/lib/libXdmcp-1.1.2.tar.bz2')

        self.add_library(name='Xau', url='https://www.x.org/pub/individual/lib/libXau-1.0.8.tar.bz2')

        self.add_library(
            name='xcb',
            url='https://xcb.freedesktop.org/dist/libxcb-1.13.tar.bz2',
            phases=[
                Shell(
                    post_extract='cd {source}'
                    # Fixes incompatibilities between python2 and python3 (whitespace inconsistencies)
                    # https://bugs.freedesktop.org/show_bug.cgi?id=95490
                    ' && wget http://www.linuxfromscratch.org/patches/blfs/7.10/libxcb-1.12-python3-1.patch -O - | patch -Np1 || true'
                    # pthread-stubs is useless on linux
                    ' && sed -i "s/pthread-stubs//" configure'
                )
            ],
            configure_args={
                '--enable-xinput': True,
                '--without-doxygen': True
            }
        )

        # yapf: disable
        xorg_libs = [
            ('xtrans',        '1.3.5'),
            ('libX11',        '1.6.5'),
            ('libXext',       '1.3.3'),
            ('libFS',         '1.0.7'),
            ('libICE',        '1.0.9'),
            ('libSM',         '1.2.2'),
            ('libXScrnSaver', '1.2.2'),
            ('libXt',         '1.1.5'),
            ('libXmu',        '1.1.2'),
            ('libXpm',        '3.5.12'),
            ('libXaw',        '1.0.13'),
            ('libXfixes',     '5.0.3'),
            ('libXcomposite', '0.4.4'),
            ('libXrender',    '0.9.10'),
            ('libXcursor',    '1.1.15'),
            ('libXdamage',    '1.1.4'),
            ('libfontenc',    '1.1.3'),
            ('libXfont2',     '2.0.3'),
            ('libXft',        '2.3.2'),
            ('libXi',         '1.7.9'),
            ('libXinerama',   '1.1.3'),
            ('libXrandr',     '1.5.1'),
            ('libXres',       '1.2.0'),
            ('libXtst',       '1.2.3'),
            ('libXv',         '1.0.11'),
            ('libXvMC',       '1.0.10'),
            ('libXxf86dga',   '1.1.4'),
            ('libXxf86vm',    '1.1.4'),
            ('libdmx',        '1.1.3'),
            ('libpciaccess',  '0.14'),
            ('libxkbfile',    '1.0.9'),
            ('libxshmfence',  '1.3')
        ]
        # yapf: enable

        for lib in xorg_libs:
            self.add_library(
                name='xorg-lib-{}'.format(lib[0]),
                url='https://www.x.org/pub/individual/lib/{}-{}.tar.bz2'.format(*lib),
                phases=[UpdateConfigSub],
                env={'CC_FOR_BUILD': '{}-gcc'.format('{parent_target_triple}'),
                     'CFLAGS_FOR_BUILD': ''},
                configure_args={
                    # musl returns a valid pointer for a 0 byte allocation
                    '--enable-malloc0returnsnull': 'no'
                }
            )

    def install_tcltk(self, version='8.6.8', **kwargs):

        if kwargs.get('install_X11', False):
            self.install_X11()

        # Apparently configure gets confused when we are cross compiling
        # https://groups.google.com/forum/#!topic/comp.lang.tcl/P56Gge5_3Z8
        # It looks like musl have fixed some bugs in strtod, so lets assume that it is not "buggy"
        env = {'ac_cv_func_strtod': 'yes', 'tcl_cv_strtod_unbroken': 'yes', 'tcl_cv_strtod_buggy': 'no'}

        # Tcl/Tk configures don't understand --enable-static
        self.add_library(
            name='tcl',
            url='https://prdownloads.sourceforge.net/tcl/tcl{}-src.tar.gz'.format(version),
            src_dir='unix',
            configure_args={'--enable-threads': True,
                            '--enable-static': None},
            env=env
        )

        m64 = '--enable-64bit' if self.arch == 'x86_64' else '--disable-64bit'

        self.add_library(
            name='tk',
            url='https://prdownloads.sourceforge.net/tcl/tk{}-src.tar.gz'.format(version),
            src_dir='unix',
            configure_args={
                '--with-tcl': os.path.join('..', 'tcl{}-src'.format(version)),
                m64: True,
                '--x-includes': os.path.join('{prefix_dir}', 'include'),
                '--x-libraries': os.path.join('{prefix_dir}', 'lib'),
                '--enable-static': None
            },
            install_targets=['install', 'install-private-headers'],
            env=env
        )

    def install_linux_headers(self, **kwargs):

        # Linux kernel doesn't know what aarch64, it knows arm64 though
        args = {
            'ARCH': self.arch if self.arch != 'aarch64' else 'arm64',
            'INSTALL_HDR_PATH': os.path.join('{prefix_dir}', 'temp')
        }

        self.add_library(
            name='linux-headers',
            url='https://git.kernel.org/torvalds/t/linux-4.16-rc5.tar.gz',
            phases=[
                Shell(pre_install='mkdir -p {}'.format('{prefix_dir}', 'temp')),
                Shell(
                    post_install=
                    'find {dest} \( -name .install -o -name ..install.cmd \) -delete && cp -rv {} {} && rm -rf {dest}'.
                    format(
                        os.path.join('{prefix_dir}', 'temp', 'include', '*'),
                        os.path.join('{prefix_dir}', 'include'),
                        dest=os.path.join('{prefix_dir}', 'temp', 'include')
                    )
                )
            ],
            build_targets=[],
            install_args=args,
            install_targets=['headers_install']
        )

    def build(self):

        # Make our directories if they do not already exist
        os.makedirs(self.prefix_dir, exist_ok=True)

        if os.path.exists(os.path.join(self.state['prefix_dir'], 'usr')):
            if not os.path.islink(os.path.join(self.state['prefix_dir'], 'usr')):
                os.path.unlink(os.path.join(self.state['prefix_dir'], 'usr'))
                os.symlink(self.state['prefix_dir'], os.path.join(self.state['prefix_dir'], 'usr'))

        else:
            os.symlink(self.state['prefix_dir'], os.path.join(self.state['prefix_dir'], 'usr'))

        for d in ['bin', 'include', 'lib', 'etc']:
            os.makedirs(os.path.join(self.state['prefix_dir'], d), exist_ok=True)

        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(self.patches_dir, exist_ok=True)
        os.makedirs(self.builds_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.status_dir, exist_ok=True)

        # A nice big banner to make it visible
        info = [
            'Toolchain:    {}'.format(self.state['toolchain_name']), 'Architecture: {}'.format(self.triple),
            'Directory:    {}'.format(self.state['prefix_dir'])
        ]
        max_string = max(len(l) for l in info)
        max_len = max(76, max_string)

        cprint('')
        cprint('#' * (max_len + 4), 'red', attrs=['bold'])
        for i in info:
            cprint('# {} #'.format(i.ljust(max_string).center(max_len)), 'red', attrs=['bold'])
        cprint('#' * (max_len + 4), 'red', attrs=['bold'])
        cprint('')

        # Build all our libraries
        for l in self.libraries:
            l.build()


def generate_toolchain_files(env, log_file, **state):
    gcc_template = dedent(
        """\
        *c_opts:
        {c_compile_options}

        *cxx_opts:
        {cxx_compile_options}

        *cc1_options:
        + %(c_opts)

        *cc1plus_options:
        + %(cxx_opts)
        """
    )

    cmake_template = dedent(
        """\
        # Set default system parameters
        SET(CMAKE_SYSTEM_NAME Linux)
        SET(CMAKE_SYSTEM_PROCESSOR {arch})
        SET(TRIPLE "{triple}" CACHE STRING "Compiler triple of the build system" FORCE)
        SET(CMAKE_C_COMPILER ${{TRIPLE}}-gcc)
        SET(CMAKE_CXX_COMPILER ${{TRIPLE}}-g++)
        SET(CMAKE_Fortran_COMPILER ${{TRIPLE}}-gfortran)

        SET(CMAKE_FIND_ROOT_PATH "${{TOOLCHAIN_ROOT}}"
                                 "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}"
                                 "${{TOOLCHAIN_ROOT}}/.."
        )
        SET(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM BOTH)
        SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
        SET(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
        SET(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

        # C system search directories
        SET(CMAKE_C_IMPLICIT_INCLUDE_DIRECTORIES "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}/include"
                                                 "${{TOOLCHAIN_ROOT}}/usr/include"
                                                 "${{TOOLCHAIN_ROOT}}/lib/gcc/${{TRIPLE}}/7.3.0/include"
        )

        # CXX system search directories
        SET(CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}/include/c++/7.3.0"
                                                   "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}/include/c++/7.3.0/${{TRIPLE}}"
                                                   "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}/include/c++/7.3.0/backward"
                                                   "${{TOOLCHAIN_ROOT}}/${{TRIPLE}}/include"
                                                   "${{TOOLCHAIN_ROOT}}/usr/include"
                                                   "${{TOOLCHAIN_ROOT}}/lib/gcc/${{TRIPLE}}/7.3.0/include"
        )


        INCLUDE_DIRECTORIES(SYSTEM "${{TOOLCHAIN_ROOT}}/include")
        INCLUDE_DIRECTORIES(SYSTEM "${{TOOLCHAIN_ROOT}}/include/python3.6m")

        SET(PLATFORM "{platform}" CACHE STRING "The platform to build for." FORCE)

        # Prevent cmake from trying to execute python to find its libraries.
        SET(PYTHON_EXECUTABLE {python_exec} CACHE STRING "" FORCE)
        SET(PYTHON_LIBRARY {python_lib} CACHE STRING "" FORCE)
        SET(PYTHONLIBS_FOUND ON CACHE BOOLEAN "" FORCE)
        SET(PYTHON_MODULE_EXTENSION ".cpython-36m-{arch}-linux-gnu.so" CACHE STRING "" FORCE)

        SET(Protobuf_PROTOC_EXECUTABLE {protoc_exec} CACHE STRING "The Google Protocol Buffers Compiler" FORCE)
        SET(Protobuf_PROTOC_LIBRARY_DEBUG {protoc_lib} CACHE STRING "Path to a library" FORCE)
        SET(Protobuf_PROTOC_LIBRARY_RELEASE {protoc_lib} CACHE STRING "Path to a library" FORCE)
        """
    )

    # Get the march and mtune flags from c_flags + cxx_flags + fc_flags
    march = ''
    mtune = ''
    for flag in state['c_flags'] + state['cxx_flags'] + state['fc_flags']:
        if flag.startswith('-march='):
            march = flag[1:]
            log_file.write('Found architecture parameter: {}\n'.format(march))
        if flag.startswith('-mtune='):
            mtune = flag[1:]
            log_file.write('Found tuning parameter: {}\n'.format(mtune))

    # Find the location of the GCC specs file
    libgcc = subprocess.check_output(
        '{} {}'.format(
            os.path.join(state['prefix_dir'], 'bin', '{}-gcc'.format(state['target_triple'])),
            '-print-libgcc-file-name'
        ),
        shell=True,
        env=env
    ).decode('utf-8')

    if march != '' and mtune != '':
        arch = '%<march=* -{0} %>{0}'.format(march)
        tune = '%{{!mtune=*:%>{0}}} %{{{0}:%>{0}}}'.format(mtune)
        compile_options = '{} {} '.format(arch, tune)
    else:
        compile_options = ''

    # Form our output file names
    specs_file = os.path.join(os.path.dirname(libgcc), 'specs')
    cmake_toolchain_file = os.path.join(state['prefix_dir'], '{}.cmake'.format(state['toolchain_name']))

    log_file.write('Using gcc specs: {}\n'.format(specs_file))

    # Write out the new GCC specs
    with open(specs_file, 'a') as specs:
        specs.write(
            gcc_template.format(
                c_compile_options='{}{}'.format(
                    compile_options, ' '.join([
                        flag for flag in state['c_flags']
                        if flag != '-{}'.format(march) and flag != '-{}'.format(mtune)
                    ])
                ),
                cxx_compile_options='{}{}'.format(
                    compile_options, ' '.join([
                        flag for flag in state['cxx_flags']
                        if flag != '-{}'.format(march) and flag != '-{}'.format(mtune)
                    ])
                )
            )
        )

    log_file.write('Successfully wrote new specs file to "{}"\n'.format(specs_file))

    # Write out the CMake toolchain file
    with open(cmake_toolchain_file, 'w') as f:
        f.write(
            cmake_template.format(
                platform=state['toolchain_name'],
                arch=state['arch'],
                cc='{}-gcc'.format(state['target_triple']),
                cxx='{}-g++'.format(state['target_triple']),
                triple=state['target_triple'],
                parent_triple=state['parent_target_triple'],
                python_exec=os.path.join(
                    '${TOOLCHAIN_ROOT}', '..' if state['toolchain_name'] != 'root' else '', 'bin', 'python3'
                ),
                python_lib=os.path.join('${TOOLCHAIN_ROOT}', 'lib', 'libpython3.6m.so'),
                protoc_exec=os.path.join(
                    '${TOOLCHAIN_ROOT}', '..' if state['toolchain_name'] != 'root' else '', 'bin', 'protoc'
                ),
                protoc_lib=os.path.join(
                    '${TOOLCHAIN_ROOT}', '..' if state['toolchain_name'] != 'root' else '', 'lib', 'libprotoc.so'
                )
            )
        )

    log_file.write('Successfully wrote cmake toolchain file to "{}"\n'.format(cmake_toolchain_file))
    log_file.write('\n\nCompleted with no errors\n')


def gcc_post_extract(env, log_file, **state):
    process = subprocess.Popen(
        args='cd {source} && ./contrib/download_prerequisites'.format(**state),
        shell=True,
        env={k: v.format(**state)
             for (k, v) in env.items()},
        stdout=log_file,
        stderr=log_file
    )

    if process.wait() != 0:
        raise Exception('Failed to download GCC prerequisites')


def gcc_post_install(env, log_file, **state):
    # Get the default GCC specs file
    specs = subprocess.check_output(
        '{} -dumpspecs'.format(
            os.path.join(state['prefix_dir'], 'bin', '{}-gcc'.format(state['target_triple']))
        ),
        shell=True,
        env=env
    ).decode('utf-8')

    # Set the path to our dynamic loader
    specs = re.sub('/lib/ld-', '{prefix_dir}/lib/ld-'.format(**state), specs)

    # Find the location of GCC specs file (via the libgcc location)
    libgcc = subprocess.check_output(
        '{} -print-libgcc-file-name'.format(
            os.path.join(state['prefix_dir'], 'bin', '{}-gcc'.format(state['target_triple']))
        ),
        shell=True,
        env=env
    ).decode('utf-8')

    # Write out the modified specs file
    with open(os.path.join(os.path.dirname(libgcc), 'specs'), 'w') as f:
        f.write(specs)

def musl_post_install(env, log_file, **state):
    with open(os.path.join(state['prefix_dir'], 'etc', 'ld-musl-{}.path'.format(state['arch'])), 'w') as f:
        f.write(os.pathsep.join(['{prefix_dir}/lib',
                                 '{prefix_dir}/lib64',
                                 '{prefix_dir}/{target_triple}/lib',
                                 '{prefix_dir}/{target_triple}/lib64']).format(**state))


def gnulibs_pre_build(env, log_file, **state):
    # Get the default GCC specs file
    specs = subprocess.check_output('{} -dumpspecs'.format(os.path.join(state['build'], 'gcc', 'xgcc')),
        shell=True,
        env=env
    ).decode('utf-8')

    # Set the path to our dynamic loader
    specs = re.sub('/lib/ld-', '{prefix_dir}/lib/ld-'.format(**state), specs)

    # Find the location of GCC specs file (via the libgcc location)
    libgcc = subprocess.check_output(
        '{} -print-libgcc-file-name'.format(
            os.path.join(state['prefix_dir'], 'bin', '{}-gcc'.format(state['target_triple']))
        ),
        shell=True,
        env=env
    ).decode('utf-8')

    # Write out the modified specs file
    with open(os.path.join(state['build'], 'gcc', 'specs'), 'w') as f:
        f.write(specs)
