#!/usr/bin/env python3

from reel import Reel

r = Reel()

r.add_toolchain('nuc7i7bnh', triple='x86_64-linux-musl', arch='x86_64')

r.build()
