#!/usr/bin/env python3

from reel import Reel

r = Reel(gnu_mirror='http://gnu.uberglobalmirror.com')

r.add_toolchain('nuc7i7bnh', triple='x86_64-linux-musl')
r.add_toolchain('jetsontx2', triple='aarch64-linux-musl')

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
#protobuf
#zlib
#bzip2
#xml2
#nuclear
#openblas
#libsvm
#armadillo
#tcmalloc
#yaml-cpp
#fftw3
#fftw3f
#jpeg-turbo
#fmt
#portaudio
#eigen3
#boost (damn :'( )
#espeak
#fswatch
#catch
#ffi
#glib2
#aravis
#libpcre
#libmount
