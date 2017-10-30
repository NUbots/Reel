#!/usr/bin/env python3

import platform
from .Toolchain import Toolchain

class Reel:

    def add_build_tools(self, toolchain):

        toolchain.add_library(name='make',
                              url='https://ftpmirror.gnu.org/gnu/make/make-4.2.tar.gz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"',
                                              '--without-guile',
                                              '--disable-nls'])

        toolchain.add_library(name='m4',
                              url='https://ftpmirror.gnu.org/gnu/m4/m4-1.4.18.tar.xz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"',
                                              '--enable-threads=posix',
                                              '--enable-c++',
                                              '--enable-changeword',
                                              '--with-packager="Reel"',
                                              '--with-packager-version="0.1"',
                                              '--with-syscmd-shell="/bin/bash"'])

        toolchain.add_library(name='autoconf',
                              url='https://ftpmirror.gnu.org/gnu/autoconf/autoconf-2.69.tar.xz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"'])

        toolchain.add_library(name='automake',
                              url='https://ftpmirror.gnu.org/gnu/automake/automake-1.15.1.tar.xz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"'])


        toolchain.add_library(name='libtool',
                              url='https://ftpmirror.gnu.org/gnu/libtool/libtool-2.4.6.tar.xz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"',
                                              '--enable-static',
                                              '--with-sysroot="{prefix_dir}"'])



        toolchain.add_library(name='ncurses',
                              url='https://ftpmirror.gnu.org/gnu/ncurses/ncurses-6.0.tar.gz',
                              configure_args=['--target="{arch}"',
                                              '--host="{arch}"',
                                              '--enable-static',
                                              '--with-sysroot="{prefix_dir}"',
                                              '--with-build-cc="{CC}"',
                                              '--with-normal',
                                              '--with-debug',
                                              '--with-profile',
                                              '--with-termlib',
                                              '--with-ticlib',
                                              '--with-gpm',
                                              '--enable-sp-funcs',
                                              '--enable-const',
                                              '--enable-ext-colors',
                                              '--enable-ext-mouse',
                                              '--enable-ext-putwin',
                                              '--enable-no-padding',
                                              '--enable-sigwinch',
                                              '--enable-tcap-names'])


        # toolchain.add_library(url='https://cmake.org/files/v3.10/cmake-3.10.0-rc3.tar.gz')
        # CFLAGS="$CFLAGS -isystem {prefix_dir}/include/ncurses" \
        # CXXFLAGS="$CXXFLAGS -isystem {prefix_dir}/include/ncurses" \
        # "${SOURCE}/${CMAKE}/bootstrap" \
        #     --parallel="$(nproc)" \
        #     --no-qt-gui


        # toolchain.add_library(url='https://github.com/ninja-build/ninja/archive/v1.8.2.tar.gz')

    def __init__(self, toolchain_level='FULL'):

        self.toolchains = []
        self.libraries = []
        self.toolchain = None

        # OSX can't handle musl based programs yet so downgrade
        if platform.system() is 'Darwin' and toolchain_level is 'FULL':
            toolchain_level = 'HOSTED'

        # With a system root toolchain we use the system compiler and build the tools
        if toolchain_level is 'SYSTEM':

            # Just use the system toolchain
            self.toolchain = Toolchain(name='', system=True)
            self.toolchains.append(self.toolchain)

            # Add system tools
            self.add_build_tools(toolchain)

        # We build our own compiler but just using the system toolchain
        elif toolchain_level is 'HOSTED':

            # Just use the system toolchain
            self.toolchain = Toolchain(name='')
            self.toolchains.append(self.toolchain)

            # Add system tools
            self.add_build_tools(toolchain)


        # With a built root toolchain, we build and self host our compiler
        elif toolchain_level is 'FULL':

            # Make our bootstrap toolchain
            bootstrap_toolchain = Toolchain(name='bootstrap')
            self.toolchains.append(bootstrap_toolchain)

            # Make our real toolchain
            self.toolchain = Toolchain(name='full', build_toolchain=bootstrap_toolchain)
            self.toolchains.append(self.toolchain)

            self.add_build_tools(self.toolchain)

    def add_toolchain(self, name):
        # Create a new toolchain and return it and build using our toolchain
        t = Toolchain(name, build_with=self.toolchain)
        self.toolchains.append(t)
        return t

    def build(self):
        # Build our toolchains
        for t in self.toolchains:
            t.build()

