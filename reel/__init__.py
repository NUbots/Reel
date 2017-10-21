#!/usr/bin/env python3

from .Toolchain import Toolchain

class Reel:

    def __init__(self):
        # This is our main toolchain build for the current system
        self.toolchain = Toolchain(name='')

        self.toolchains = []
        self.libraries = []

        # By default we need some libraries to build things
        # Add them to our system libraries
        # self.toolchain.add_library(name='make',
        #                            url='https://ftpmirror.gnu.org/gnu/make/make-4.2.tar.gz')
        # self.toolchain.add_library(name='m4',
        #                            url='https://ftpmirror.gnu.org/gnu/m4/m4-1.4.18.tar.xz')
        # self.toolchain.add_library(name='autoconf',
        #                            url='https://ftpmirror.gnu.org/gnu/autoconf/autoconf-2.69.tar.xz')
        # self.toolchain.add_library(name='automake',
        #                            url='https://ftpmirror.gnu.org/gnu/automake/automake-1.15.1.tar.xz')
        # self.toolchain.add_library(name='libtool',
        #                            url='https://ftpmirror.gnu.org/gnu/libtool/libtool-2.4.6.tar.xz')
        # self.toolchain.add_library(name='ncurses',
        #                            url='https://ftpmirror.gnu.org/gnu/ncurses/ncurses-6.0.tar.gz')
        # self.toolchain.add_library(name='openssl',
        #                            url='https://www.openssl.org/source/openssl-1.1.0f.tar.gz')
        # self.toolchain.add_library(name='cmake',
        #                            url='https://cmake.org/files/v3.8/cmake-3.8.2.tar.gz')
        # self.toolchain.add_library(name='ninja',
        #                            url='https://github.com/ninja-build/ninja/archive/v1.7.2.tar.gz')

    def add_toolchain(self, name):
        # Create a new toolchain and return it
        t = Toolchain(name)
        self.toolchains.append(t)
        return t

    def build(self):
        # Build our main toolchain
        self.toolchain.build()

        # Build our other toolchains
        for t in self.toolchains:
            t.build()

