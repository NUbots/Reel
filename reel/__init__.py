#!/usr/bin/env python3

import platform
from .Toolchain import Toolchain
from .Shell import Shell


class Reel:
    def add_build_tools(self, toolchain):
        toolchain.add_library(
            name='make',
            url='{}/make/make-4.2.tar.gz'.format(self.gnu_mirror),
            configure_args=[
                '--host={arch}', '--build={arch}', '--without-guile',
                '--disable-nls'
            ])

        toolchain.add_library(
            name='m4',
            url='{}/m4/m4-1.4.18.tar.xz'.format(self.gnu_mirror),
            configure_args=[
                '--host={arch}', '--build={arch}', '--enable-threads=posix',
                '--enable-c++', '--enable-changeword',
                '--with-packager="Reel"', '--with-packager-version="0.1"',
                '--with-syscmd-shell="/bin/bash"'
            ])

        toolchain.add_library(
            name='autoconf',
            url='{}/autoconf/autoconf-2.69.tar.xz'.format(self.gnu_mirror),
            configure_args=['--host={arch}', '--build={arch}'])

        toolchain.add_library(
            name='automake',
            url='{}/automake/automake-1.15.1.tar.xz'.format(self.gnu_mirror),
            configure_args=['--host={arch}', '--build={arch}'])

        toolchain.add_library(
            name='libtool',
            url='{}/libtool/libtool-2.4.6.tar.xz'.format(self.gnu_mirror),
            configure_args=[
                '--host={arch}', '--build={arch}', '--enable-static',
                '--enable-shared', '--with-sysroot="{prefix_dir}"'
            ])

        toolchain.add_library(
            name='ncurses',
            url='{}/ncurses/ncurses-6.0.tar.gz'.format(self.gnu_mirror),
            env={'CPPFLAGS': '-P'},
            configure_args=[
                '--host={arch}', '--build={arch}', '--enable-static',
                '--enable-shared', '--with-sysroot="{prefix_dir}"',
                '--with-build-cc="$CC"', '--with-normal', '--with-debug',
                '--with-profile', '--with-termlib', '--with-ticlib',
                '--with-gpm', '--enable-sp-funcs', '--enable-const',
                '--enable-ext-colors', '--enable-ext-mouse',
                '--enable-ext-putwin', '--enable-no-padding',
                '--enable-sigwinch', '--enable-tcap-names'
            ])

        # Building ninja is a little weird
        toolchain.add_library(
            Shell(
                configure=
                'mkdir -p {builds_dir}/$(basename {source}) && cp -r {source}/* {builds_dir}/$(basename {source})'
            ),
            Shell(
                build=
                'cd {builds_dir}/$(basename {source}) && ./configure.py --bootstrap'
            ),
            Shell(
                install=
                'cd {builds_dir}/$(basename {source}) && cp ninja {prefix_dir}/bin'
            ),
            name='ninja',
            url='https://github.com/ninja-build/ninja/archive/v1.8.2.tar.gz')

        toolchain.add_library(
            name='zlib',
            url='http://www.zlib.net/zlib-1.2.11.tar.gz',
            configure_args=['--static', '--shared'])

        toolchain.add_library(
            Shell(configure='base_dir=$(pwd)'
                  ' && mkdir -p {builds_dir}/$(basename {source})'
                  ' && cd {builds_dir}/$(basename {source})'
                  ' && CROSS_COMPILE=" " '
                  '    $base_dir/{source}/config'
                  '    --prefix={prefix_dir} '
                  '    --libdir=lib'
                  '    --release no-async'),
            Shell(build='cd {builds_dir}/$(basename {source})'
                  ' && make'),
            Shell(install='cd {builds_dir}/$(basename {source})'
                  ' && make install'),
            name='openssl',
            url='https://www.openssl.org/source/openssl-1.1.0f.tar.gz')

        toolchain.add_library(
            name='curl',
            url='https://curl.haxx.se/download/curl-7.57.0.tar.xz',
            configure_args=[
                '--host={arch}', '--build={arch}', '--enable-static',
                '--enable-shared', '--with-sysroot="{prefix_dir}"',
                '--with-ssl="{prefix_dir}"'
            ])

        # Bootstrapping cmake is a little weird too
        toolchain.add_library(
            Shell(configure='base_dir=$(pwd)'
                  ' && mkdir -p {builds_dir}/$(basename {source})'
                  ' && cd {builds_dir}/$(basename {source})'
                  ' && $base_dir/{source}/bootstrap'
                  '    --prefix={prefix_dir}'
                  '    --no-qt-gui'
                  '    --system-curl'
                  '    --parallel={cpu_count}'),
            Shell(build='cd {builds_dir}/$(basename {source})'
                  ' && make'),
            Shell(install='cd {builds_dir}/$(basename {source})'
                  ' && make install'),
            name='cmake',
            url='https://cmake.org/files/v3.10/cmake-3.10.0.tar.gz')

    def __init__(self,
                 toolchain_level='FULL',
                 gnu_mirror='https://ftpmirror.gnu.org/gnu'):
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
                name='bootstrap',
                gnu_mirror=self.gnu_mirror,
                static=True,
                parent_toolchain=system_toolchain)
            self.toolchains.append(bootstrap_toolchain)

            # Make our real toolchain
            self.toolchain = Toolchain(
                name='',
                gnu_mirror=self.gnu_mirror,
                parent_toolchain=bootstrap_toolchain)
            self.toolchains.append(self.toolchain)

            # The final toolchain gets all the tools
            self.add_build_tools(self.toolchain)

    def add_toolchain(self, name, triple=''):
        # Create a new toolchain and return it and build using our toolchain
        t = Toolchain(
            name,
            gnu_mirror=self.gnu_mirror,
            triple=triple,
            parent_toolchain=self.toolchain)
        self.toolchains.append(t)
        return t

    def build(self):
        # Build our toolchains
        for t in self.toolchains:
            t.build()
