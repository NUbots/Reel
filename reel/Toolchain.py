#!/usr/bin/env python3

import os

from .download import download
from .build import build
from .extract import extract
from .Library import Library

class Toolchain:
    def __init__(self, name):
        self.name = name
        self.libraries = []

        # Setup our directories
        # TODO change some of these directories based on what toolchain we are building
        self.toolchain_path = 'toolchain'
        self.working_path = os.path.join('toolchain', 'toolchain_build')
        self.archive_path = os.path.join(self.working_path, 'archive')
        self.src_path = os.path.join(self.working_path, 'src')
        self.build_path = os.path.join(self.working_path, 'build')
        self.logs_path = os.path.join(self.working_path, 'log')


    def add_library(self, name, url):
        self.libraries.append(Library(self, name, url))


    def build(self):

        # Make our directories if they do not already exist
        os.makedirs(self.toolchain_path, exist_ok=True)
        os.makedirs(self.working_path, exist_ok=True)
        os.makedirs(self.archive_path, exist_ok=True)
        os.makedirs(self.src_path, exist_ok=True)
        os.makedirs(self.build_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)

        # Download our source code
        download(url='https://ftpmirror.gnu.org/gnu/gcc/gcc-7.1.0/gcc-7.1.0.tar.bz2',
                 dest=os.path.join(self.archive_path, 'gcc.tar.bz2'))
        download(url='https://www.musl-libc.org/releases/musl-1.1.16.tar.gz',
                 dest=os.path.join(self.archive_path, 'musl.tar.gz'))
        download(url='https://ftpmirror.gnu.org/gnu/binutils/binutils-2.28.tar.bz2',
                 dest=os.path.join(self.archive_path, 'binutils.tar.bz2'))
        download(url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
                 dest=os.path.join(self.archive_path, 'libbacktrace.tar.gz'))

        # Uncompress the archives
        extract(path=os.path.join(self.archive_path, 'gcc.tar.bz2'),
                dest=os.path.join(self.src_path, 'gcc'))
        extract(path=os.path.join(self.archive_path, 'musl.tar.gz'),
                dest=os.path.join(self.src_path, 'musl'))
        extract(path=os.path.join(self.archive_path, 'binutils.tar.bz2'),
                dest=os.path.join(self.src_path, 'binutils'))
        extract(path=os.path.join(self.archive_path, 'libbacktrace.tar.gz'),
                dest=os.path.join(self.src_path, 'libbacktrace'))

        bootstrap_prefix = os.path.abspath(os.path.join(self.build_path, 'bootstrap_prefix'))

        # Bootstrap musl
        build(toolchain=self,
              src='musl',
              build='bootstrap_musl',
              args=['--prefix={}'.format(bootstrap_prefix),
                    '--target=x86_64',
                    '--disable-shared'],
              env={'CROSS_COMPILE': ' '})

        # Bootstrap binutils
        build(toolchain=self,
              src='binutils',
              build='bootstrap_binutils',
              args=['--prefix={}'.format(bootstrap_prefix),
                    '--target=amd64-linux-musl',
                    '--with-sysroot',
                    '--disable-nls',
                    '--disable-bootstrap',
                    '--disable-werror'])


        # TODO create bootstrap binutils and build boostrap binutils

        # TODO create bootstrap gcc and build bootstrap gcc

        # TODO build our gcc toolchain

        # Build libraries using this toolchain
        for l in self.libraries:
            l.build()
