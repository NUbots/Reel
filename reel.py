#!/usr/bin/env python3

import os

from reel.patch import UpdateConfigSub
from reel import Reel

r = Reel()  #gnu_mirror='http://gnu.uberglobalmirror.com')

r.add_library(
    url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
    name='protobuf',
    configure_args={
        '--with-zlib': True,
        '--enable-static': True,
        '--enable-shared': True
    }
)

toolchains = [
    r.add_toolchain('nuc7i7bnh', triple='x86_64-linux-musl'),
    r.add_toolchain('jetsontx2', triple='aarch64-linux-musl')
]

for t in toolchains:

    t.add_library(
        UpdateConfigSub,
        name='libbacktrace',
        url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
        config_sub_file='config.sub',
        configure_args={'--enable-static': True,
                        '--enable-shared': True},
        install_targets=['install-strip']
    )

    t.add_library(
        name='zlib',
        url='http://www.zlib.net/zlib-1.2.11.tar.gz',
        configure_args={
            '--host': None,  # zlib configure doesn't understand host
            '--build': None,  # zlib configure doesn't understand build
            '--static': True,
            '--shared': True
        }
    )
    t.add_library(
        url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
        name='protobuf',
        env={
            'CC_FOR_BUILD': '{} -static'.format(t.parent_toolchain.env['CC']),
            'CXX_FOR_BUILD': '{} -static'.format(t.parent_toolchain.env['CXX'])
        },
        configure_args={
            '--with-zlib': True,
            '--with-protoc': os.path.join('{parent_prefix_dir}', 'bin', 'protoc'),
            '--enable-static': True,
            '--enable-shared': True,
            '--verbose': True
        }
    )

r.build()

# pkg-config
# linux-headers-generic
# nasm
# autopoint
# gettext
# python3
# protobuf

# zlib
# python3
# libasound2
# libusb
# protobuf
# zlib
# bzip2
# xml2
# nuclear
# openblas
# libsvm
# armadillo
# tcmalloc
# yaml-cpp
# fftw3
# fftw3f
# jpeg-turbo
# fmt
# portaudio
# eigen3
# boost (damn :'( )
# espeak
# fswatch
# catch
# ffi
# glib2
# aravis
# libpcre
# libmount
