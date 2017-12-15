#!/usr/bin/env python3

import os

from .AutotoolsBuild import AutotoolsBuild
from .MakeBuild import MakeBuild


class SmartBuild:

    def __init__(self, **build_args):

        # Start without a downloader
        self.build_args = build_args
        self.src_dir = build_args.get('src_dir', '.')
        self.build_tool = None

    def configure(self, **state):

        source = state['source']

        # First check to see if we have a configure script
        if os.path.isfile(os.path.join(source, self.src_dir, 'configure')) or os.path.isfile(os.path.join(
                source, self.src_dir, 'autogen.sh')):
            self.build_tool = AutotoolsBuild(**self.build_args)

        # Then check for CMakeLists.txt
        elif os.path.isfile(os.path.join(source, self.src_dir, 'CMakeLists.txt')):
            # TODO
            pass

        # Bjam
        # Bazel

        # Then check for a Makefile
        elif os.path.isfile(os.path.join(source, self.src_dir, 'Makefile')):
            self.build_tool = MakeBuild(**self.build_args)

        return self.build_tool.configure(**state)

    def build(self, **state):

        return self.build_tool.build(**state)

    def install(self, **state):

        return self.build_tool.install(**state)
