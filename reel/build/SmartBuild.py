#!/usr/bin/env python3

import os

from .AutotoolsBuild import AutotoolsBuild


class SmartBuild:
    def __init__(self, **build_args):

        # Start without a downloader
        self.build_args = build_args
        self.build_tool = None

    def configure(self, **state):

        source = state['source']

        # First check to see if we have a configure script
        if os.path.isfile(os.path.join(source, 'configure')):
            self.build_tool = AutotoolsBuild(**self.build_args)

        # If we have a repo that has autogen but no configure yet
        elif os.path.isfile(os.path.join(source, 'autogen.sh')):
            # TODO
            pass

        # Then check for CMakeLists.txt
        elif os.path.isfile(os.path.join(source, 'CMakeLists.txt')):
            # TODO
            pass

        # Bjam
        # Bazel

        # Then check for a Makefile
        elif os.path.isfile(os.path.join(source, 'Makefile')):
            # TODO
            pass

        return self.build_tool.configure(**state)

    def build(self, **state):

        return self.build_tool.build(**state)

    def install(self, **state):

        return self.build_tool.install(**state)
