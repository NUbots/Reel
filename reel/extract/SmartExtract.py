#!/usr/bin/env python3

import tarfile
from .TarExtract import TarExtract

class SmartExtract:
    def __init__(self, **kwargs):
        self.build_args = kwargs

    def extract(self, **kwargs):

        # If we have an archive
        if 'archive' in kwargs:
            archive = kwargs['archive']

            # For now assume tar file
            return TarExtract(**self.build_args).extract(**kwargs)

