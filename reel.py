#!/usr/bin/env python3

from reel import Reel

r = Reel()

t = r.add_toolchain(name='nuc7i7bnh')

t.add_library(url='https://github.com/google/protobuf/releases/download/v3.3.0/protobuf-cpp-3.3.0.tar.gz')

r.build()
