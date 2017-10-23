#!/usr/bin/env python3

import tarfile
from .TarExtract import TarExtract

class SmartExtract:
    def __init__(self, **build_args):
        self.build_args = build_args

    def extract(self, **state):

        # If we have an archive
        if 'archive' in state:
            archive = state['archive']

            # For now assume tar file
            return TarExtract(**self.build_args).extract(**state)

