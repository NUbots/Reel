#!/usr/bin/env python3

import os
import subprocess
from termcolor import cprint
import multiprocessing

from .download import SmartDownload
from .extract import SmartExtract
from .build import SmartBuild
from .patch import UpdateConfigSub
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

        if c_flags is None:
            c_flags = []

        if cxx_flags is None:
            cxx_flags = []

        if fc_flags is None:
            fc_flags = []

        # Make sure we are always generating position independent code
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

        # Embed our parents state into our state
        if self.parent_toolchain is not None:
            self.state.update({'parent_{}'.format(k): v for (k, v) in self.parent_toolchain.state.items()})
        # Otherwise pretend that we are our own parent
        else:
            self.state.update({'parent_{}'.format(k): v for (k, v) in self.state.items()})

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
                'LD_LIBRARY_PATH': '',
                'PKG_CONFIG_PATH':
                    '{}{}{}'.format(
                        os.path.join(self.state['prefix_dir'], 'lib', 'pkgconfig'), os.pathsep,
                        os.path.join(self.state['prefix_dir'], 'share', 'pkgconfig')
                    ),

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
                    Shell(
                        post_install='echo "{prefix_dir}/lib:{prefix_dir}/lib64" > {prefix_dir}/etc/ld-musl-{arch}.path'
                    ),
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
            Shell(
                post_extract='cd {source}'
                ' && sed -ri "s:.*(AUX_MODULES.*valid):\\1:" modules.cfg '
                ' && sed -ri "s:.*(#.*SUBPIXEL_RENDERING) .*:\\1:" include/freetype/config/ftoption.h'
            ),
            url='https://downloads.sourceforge.net/freetype/freetype-2.8.1.tar.bz2',
            name='freetype',
            configure_args={
                '--with-harfbuzz': 'no',
                '--with-zlib': 'yes',
                '--with-bzip2': 'yes',
                '--with-png': 'yes'
            }
        )

        self.add_library(
            Shell(post_extract='cd {source} && rm -f src/fcobjshash.h'),
            url='https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.12.6.tar.bz2',
            name='fontconfig',
            configure_args={
                '--disable-docs': True
            }
        )

        self.add_library(url='https://www.x.org/pub/individual/util/util-macros-1.19.1.tar.bz2', name='util-macros')

        self.add_library(
            Shell(
                post_extract='cd {source}'
                ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/xcb-proto-1.12-schema-1.patch -O - | patch -Np1 || true'
                ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/xcb-proto-1.12-python3-1.patch -O - | patch -Np1 || true'
            ),
            url='https://xcb.freedesktop.org/dist/xcb-proto-1.12.tar.bz2',
            name='xcb-proto'
        )

        # yapf: disable
        xorg_protos = [
            ('bigreqsproto', '1.1.2'),
            ('compositeproto', '0.4.2'),
            ('damageproto', '1.2.1'),
            ('dmxproto', '2.3.1'),
            ('dri2proto', '2.8'),
            ('dri3proto', '1.0'),
            ('fixesproto', '5.0'),
            ('fontsproto', '2.1.3'),
            ('glproto', '1.4.17'),
            ('inputproto', '2.3.2'),
            ('kbproto', '1.0.7'),
            ('presentproto', '1.1'),
            ('randrproto', '1.5.0'),
            ('recordproto', '1.14.2'),
            ('renderproto', '0.11.1'),
            ('resourceproto', '1.2.0'),
            ('scrnsaverproto', '1.2.2'),
            ('videoproto', '2.3.3'),
            ('xcmiscproto', '1.2.2'),
            ('xextproto', '7.3.0'),
            ('xf86bigfontproto', '1.2.0'),
            ('xf86dgaproto', '2.1'),
            ('xf86driproto', '2.1.1'),
            ('xf86vidmodeproto', '2.3.1'),
            ('xineramaproto', '1.2.1'),
            ('xproto', '7.0.31')
        ]
        # yapf: enable

        for proto in xorg_protos:
            self.add_library(
                UpdateConfigSub,
                url='https://www.x.org/pub/individual/proto/{}-{}.tar.bz2'.format(*proto),
                name='xorg-protocol-header-{}'.format(proto[0])
            )

        self.add_library(url='https://www.x.org/pub/individual/lib/libXdmcp-1.1.2.tar.bz2', name='Xdmcp')

        self.add_library(url='https://www.x.org/pub/individual/lib/libXau-1.0.8.tar.bz2', name='Xau')

        self.add_library(
            Shell(
                post_extract='cd {source}'
                # Fixes incompatibilities between python2 and python3 (whitespace inconsistencies)
                # https://bugs.freedesktop.org/show_bug.cgi?id=95490
                ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/libxcb-1.12-python3-1.patch -O - | patch -Np1 || true'
                # pthread-stubs is useless on linux
                ' && sed -i "s/pthread-stubs//" configure'
            ),
            url='https://xcb.freedesktop.org/dist/libxcb-1.12.tar.bz2',
            name='xcb',
            configure_args={
                '--enable-xinput': True,
                '--without-doxygen': True
            }
        )

        # yapf: disable
        xorg_libs = [
            ('xtrans', '1.3.5'),
            ('libX11', '1.6.5'),
            ('libXext', '1.3.3'),
            ('libFS', '1.0.7'),
            ('libICE', '1.0.9'),
            ('libSM', '1.2.2'),
            ('libXScrnSaver', '1.2.2'),
            ('libXt', '1.1.5'),
            ('libXmu', '1.1.2'),
            ('libXpm', '3.5.12'),
            ('libXaw', '1.0.13'),
            ('libXfixes', '5.0.3'),
            ('libXcomposite', '0.4.4'),
            ('libXrender', '0.9.10'),
            ('libXcursor', '1.1.14'),
            ('libXdamage', '1.1.4'),
            ('libfontenc', '1.1.3'),
            ('libXfont2', '2.0.2'),
            ('libXft', '2.3.2'),
            ('libXi', '1.7.9'),
            ('libXinerama', '1.1.3'),
            ('libXrandr', '1.5.1'),
            ('libXres', '1.2.0'),
            ('libXtst', '1.2.3'),
            ('libXv', '1.0.11'),
            ('libXvMC', '1.0.10'),
            ('libXxf86dga', '1.1.4'),
            ('libXxf86vm', '1.1.4'),
            ('libdmx', '1.1.3'),
            ('libpciaccess', '0.14'),
            ('libxkbfile', '1.0.9'),
            ('libxshmfence', '1.2')
        ]
        # yapf: enable

        for lib in xorg_libs:
            self.add_library(
                UpdateConfigSub,
                url='https://www.x.org/pub/individual/lib/{}-{}.tar.bz2'.format(*lib),
                name='xorg-lib-{}'.format(lib[0]),
                configure_args={
                    # musl returns a valid pointer for a 0 byte allocation
                    '--enable-malloc0returnsnull': 'no'
                }
            )

    def install_tcltk(self, **kwargs):

        if kwargs.get('install_X11', False):
            self.install_X11()

        # Apparently configure gets confused when we are cross compiling
        # https://groups.google.com/forum/#!topic/comp.lang.tcl/P56Gge5_3Z8
        # It looks like musl have fixed some bugs in strtod, so lets assume that it is not "buggy"
        env = {'ac_cv_func_strtod': 'yes', 'tcl_cv_strtod_unbroken': 'yes', 'tcl_cv_strtod_buggy': 'no'}

        # Tcl/Tk configures don't understand --enable-static
        self.add_library(
            url='https://prdownloads.sourceforge.net/tcl/tcl8.6.7-src.tar.gz',
            name='tcl',
            src_dir='unix',
            configure_args={'--enable-threads': True,
                            '--enable-static': None},
            env=env
        )

        m64 = '--enable-64bit' if self.arch == 'x86_64' else '--disable-64bit'

        self.add_library(
            url='https://prdownloads.sourceforge.net/tcl/tk8.6.7-src.tar.gz',
            name='tk',
            src_dir='unix',
            configure_args={
                '--with-tcl': os.path.join('..', 'tcl8.6.7-src'),
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
            Shell(pre_build='mkdir -p {}'.format('{prefix_dir}', 'temp')),
            Shell(
                post_build=
                'find {dest} \( -name .install -o -name ..install.cmd \) -delete && cp -rv {} {} && rm -rf {dest}'.
                format(
                    os.path.join('{prefix_dir}', 'temp', 'include', '*'),
                    os.path.join('{prefix_dir}', 'include'),
                    dest=os.path.join('{prefix_dir}', 'temp', 'include')
                )
            ),
            name='linux-headers',
            url='https://git.kernel.org/torvalds/t/linux-4.15-rc3.tar.gz',
            build_args=args,
            build_targets=['mrproper', 'headers_check'],
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
