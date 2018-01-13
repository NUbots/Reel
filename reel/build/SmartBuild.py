#!/usr/bin/env python3

import os

from .AutotoolsBuild import AutotoolsBuild
from .BoostBuild import BoostBuild
from .CMakeBuild import CMakeBuild
from .MakeBuild import MakeBuild
from .PythonBuild import PythonBuild


class SmartBuild:

    def __init__(self, **build_args):

        # Start without a downloader
        self.build_args = build_args
        self.src_dir = build_args.get('src_dir', '.')
        self.use_tool = build_args.get('build_tool', None)
        self.build_tool = None

    def configure(self, **state):

        source = state['source']

        if self.use_tool:
            if self.use_tool == 'autotools':
                self.build_tool = AutotoolsBuild(**self.build_args)

            elif self.use_tool == 'cmake':
                self.build_tool = CMakeBuild(**self.build_args)

            elif self.use_tool == 'boost':
                self.build_tool = BoostBuild(**self.build_args)

            elif self.use_tool == 'make':
                self.build_tool = MakeBuild(**self.build_args)

            elif self.use_tool == 'python':
                self.build_tool = PythonBuild(**self.build_args)

        else:
            # First check to see if we have a configure script
            if os.path.isfile(os.path.join(source, self.src_dir, 'configure')) or os.path.isfile(os.path.join(
                    source, self.src_dir, 'autogen.sh')):
                self.build_tool = AutotoolsBuild(**self.build_args)

            # Then check for CMakeLists.txt
            elif os.path.isfile(os.path.join(source, self.src_dir, 'CMakeLists.txt')):
                self.build_tool = CMakeBuild(**self.build_args)

            # Then check for Jamroot
            elif os.path.isfile(os.path.join(source, self.src_dir, 'Jamroot')):
                self.build_tool = BoostBuild(**self.build_args)

            # Then check for setup.py
            elif os.path.isfile(os.path.join(source, self.src_dir, 'setup.py')):
                self.build_tool = PythonBuild(**self.build_args)

            # Bazel

            # Then check for a Makefile
            elif os.path.isfile(os.path.join(source, self.src_dir, 'Makefile')):
                self.build_tool = MakeBuild(**self.build_args)

        return self.build_tool.configure(**state)

    def build(self, **state):

        return self.build_tool.build(**state)

    def install(self, **state):

        return self.build_tool.install(**state)
