#!/usr/bin/env python3

import os
import platform

from .Toolchain import Toolchain
from .Shell import Shell
from .patch import UpdateConfigSub


class Reel:

    def add_build_tools(self, toolchain):

        toolchain.add_library(
            name='make',
            url='{}/make/make-4.2.tar.gz'.format(self.gnu_mirror),
            configure_args={
                '--without-guile': True,
                '--disable-nls': True
            }
        )

        toolchain.add_library(
            name='m4',
            url='{}/m4/m4-1.4.18.tar.xz'.format(self.gnu_mirror),
            configure_args={
                '--enable-threads': 'posix',
                '--enable-c++': True,
                '--enable-changeword': True,
                '--with-packager': '"Reel"',
                '--with-packager-version': '"0.1"',
                '--with-syscmd-shell': '/bin/bash'
            }
        )

        toolchain.add_library(
            UpdateConfigSub,
            name='autoconf',
            config_sub_file='build-aux/config.sub',
            url='{}/autoconf/autoconf-2.69.tar.xz'.format(self.gnu_mirror),
        )

        toolchain.add_library(
            name='automake',
            url='{}/automake/automake-1.15.1.tar.xz'.format(self.gnu_mirror),
        )

        toolchain.add_library(
            name='libtool',
            url='{}/libtool/libtool-2.4.6.tar.xz'.format(self.gnu_mirror),
            configure_args={
                '--with-sysroot': '"{prefix_dir}"',
                '--enable-ltdl-install': True
            }
        )

        toolchain.add_library(
            name='nasm',
            url='http://www.nasm.us/pub/nasm/releasebuilds/2.13.02/nasm-2.13.02.tar.xz',
            configure_args={
                '--target': '{target_triple}',
            }
        )

        toolchain.install_linux_headers()

        toolchain.add_library(
            name='util-linux',
            url='https://www.kernel.org/pub/linux/utils/util-linux/v2.31/util-linux-2.31.tar.xz',
            configure_args={
                '--disable-all-programs': True,
                '--enable-libblkid': True,
                '--enable-libmount': True,
                '--enable-libuuid': True,
                '--without-python': True,
                '--with-bashcompletiondir': os.path.join('{prefix_dir}', 'share', 'bash-completion', 'completions')
            }
        )

        toolchain.add_library(name='gettext', url='{}/gettext/gettext-0.19.8.1.tar.xz'.format(self.gnu_mirror))

        toolchain.add_library(
            url='http://ftp.pcre.org/pub/pcre/pcre-8.41.tar.bz2',
            name='pcre',
            configure_args={
                '--enable-utf': True,
                '--enable-unicode-properties': True
            }
        )

        toolchain.add_library(
            name='texinfo',
            url='{}/texinfo/texinfo-6.5.tar.xz'.format(self.gnu_mirror),
            configure_args={
                '--with-sysroot': '"{prefix_dir}"'
            }
        )

        toolchain.add_library(url='https://github.com/libffi/libffi/archive/v3.2.1.tar.gz', name='ffi')

        toolchain.add_library(url='http://www.mr511.de/software/libelf-0.8.13.tar.gz', name='libelf')

        toolchain.install_compression_libraries(zlib=True, bzip2=True, xz=True)

        toolchain.add_library(
            Shell(post_install='cp -v {build}/glib/glibconfig.h {prefix_dir}/include/glibconfig.h'),
            name='glib2',
            url='https://ftp.gnome.org/pub/gnome/sources/glib/2.52/glib-2.52.3.tar.xz',
            configure_args={
                '--with-threads': 'posix',
                '--with-pcre': 'system',
                '--disable-gtk-doc': True,
                '--disable-man': True
            }
        )

        toolchain.add_library(
            name='pkgconfig', url='https://pkg-config.freedesktop.org/releases/pkg-config-0.29.2.tar.gz'
        )

        toolchain.add_library(
            name='ncurses',
            url='{}/ncurses/ncurses-6.0.tar.gz'.format(self.gnu_mirror),
            env={'CPPFLAGS': '-P'},
            configure_args={
                '--with-sysroot': '"{prefix_dir}"',
                '--with-build-cc': '"$CC"',
                '--with-normal': True,
                '--with-debug': True,
                '--with-profile': True,
                '--with-termlib': True,
                '--with-ticlib': True,
                '--with-gpm': True,
                '--enable-sp-funcs': True,
                '--enable-const': True,
                '--enable-ext-colors': True,
                '--enable-ext-mouse': True,
                '--enable-ext-putwin': True,
                '--enable-no-padding': True,
                '--enable-sigwinch': True,
                '--enable-tcap-names': True
            }
        )

        # Building ninja is a little weird
        toolchain.add_library(
            Shell(
                configure=
                'mkdir -p {builds_dir}/$(basename {source}) && cp -rv {source}/* {builds_dir}/$(basename {source})'
            ),
            Shell(build='cd {builds_dir}/$(basename {source}) && ./configure.py --bootstrap'),
            Shell(install='cd {builds_dir}/$(basename {source}) && cp -v ninja {prefix_dir}/bin'),
            name='ninja',
            url='https://github.com/ninja-build/ninja/archive/v1.8.2.tar.gz'
        )

        toolchain.add_library(
            Shell(
                configure='base_dir=$(pwd)'
                ' && mkdir -p {builds_dir}/$(basename {source})'
                ' && cd {builds_dir}/$(basename {source})'
                ' && $base_dir/{source}/Configure'
                '    --prefix={prefix_dir} '
                '    --libdir=lib'
                '    --release'
                '    no-async'
                '    linux-{arch}'
            ),
            Shell(build='cd {builds_dir}/$(basename {source})'
                  ' && make'),
            Shell(install='cd {builds_dir}/$(basename {source})'
                  ' && make install'),
            name='openssl',
            url='https://www.openssl.org/source/openssl-1.1.0f.tar.gz',
            env={
                'CROSS_COMPILE': ' '
            }
        )

        toolchain.add_library(
            name='curl',
            url='https://curl.haxx.se/download/curl-7.57.0.tar.xz',
            configure_args={
                '--with-sysroot': '"{prefix_dir}"',
                '--with-ssl': '"{prefix_dir}"'
            }
        )

        # Bootstrapping cmake is a little weird too
        toolchain.add_library(
            Shell(
                configure='base_dir=$(pwd)'
                ' && mkdir -p {builds_dir}/$(basename {source})'
                ' && cd {builds_dir}/$(basename {source})'
                ' && $base_dir/{source}/bootstrap'
                '    --prefix={prefix_dir}'
                '    --no-qt-gui'
                '    --system-zlib'
                '    --system-curl'
                '    --parallel={cpu_count}'
            ),
            Shell(build='cd {builds_dir}/$(basename {source})'
                  ' && make'),
            Shell(install='cd {builds_dir}/$(basename {source})'
                  ' && make install'),
            name='cmake',
            url='https://cmake.org/files/v3.10/cmake-3.10.0.tar.gz'
        )

    def __init__(self, toolchain_level='FULL', gnu_mirror='https://ftpmirror.gnu.org/gnu'):
        self.toolchains = []
        self.libraries = []
        self.toolchain = None
        self.gnu_mirror = gnu_mirror

        # OSX can't handle musl based programs yet so downgrade
        if platform.system() == 'Darwin' and toolchain_level == 'FULL':
            toolchain_level = 'SYSTEM'

        # With a system root toolchain we use the system compiler and build the tools
        if toolchain_level is 'SYSTEM':

            # Just use the system toolchain
            self.toolchain = Toolchain(name='', gnu_mirror=self.gnu_mirror)
            self.toolchains.append(self.toolchain)

            # Add system tools
            self.add_build_tools(self.toolchain)

        # With a built root toolchain, we build and self host our compiler
        elif toolchain_level is 'FULL':

            # Declare our system toolchain
            system_toolchain = Toolchain(name='', gnu_mirror=self.gnu_mirror)

            # Make our bootstrap toolchain
            bootstrap_toolchain = Toolchain(
                name='bootstrap', gnu_mirror=self.gnu_mirror, static=True, parent_toolchain=system_toolchain
            )
            self.toolchains.append(bootstrap_toolchain)

            # Make our real toolchain
            self.toolchain = Toolchain(name='', gnu_mirror=self.gnu_mirror, parent_toolchain=bootstrap_toolchain)
            self.toolchains.append(self.toolchain)

            # The final toolchain gets all the tools
            self.add_build_tools(self.toolchain)

    def add_toolchain(self, name, triple=''):
        # Create a new toolchain and return it and build using our toolchain
        t = Toolchain(name, gnu_mirror=self.gnu_mirror, triple=triple, parent_toolchain=self.toolchain)
        self.toolchains.append(t)
        return t

    def add_library(self, *args, **kwargs):
        self.toolchain.add_library(*args, **kwargs)

    def install_compression_libraries(self, **kwargs):
        kwargs.get('toolchain', self.toolchain).install_compression_libraries(**kwargs)

    def install_X11(self, **kwargs):
        kwargs.get('toolchain', self.toolchain).install_X11(**kwargs)

    def install_tcltk(self, **kwargs):
        kwargs.get('toolchain', self.toolchain).install_tcltk(**kwargs)

    def install_linux_headers(self, **kwargs):
        kwargs.get('toolchain', self.toolchain).install_linux_headers(**kwargs)

    def build(self):
        # Build our toolchains
        for t in self.toolchains:
            t.build()
