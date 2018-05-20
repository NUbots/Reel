#!/usr/bin/env python3

from .TarExtract import TarExtract
from .ZipExtract import ZipExtract


class SmartExtract:

    def __init__(self, **build_args):
        self.build_args = build_args

    def extract(self, **state):

        # If we have an archive
        if 'archive' in state:

            if state['archive'].endswith('.zip'):
                return ZipExtract(**self.build_args).extract(**state)
            elif state['archive'].endswith(('.tgz', '.tar.gz', '.txz', '.tar.xz', '.tbz ', '.tbz2 ', '.tar.bz2')):
                return TarExtract(**self.build_args).extract(**state)
            else:
                # This isn't a known archive format, its probably a single file library
                return {'source': state['archive']}

        else:
            raise Exception('No archive was found to extract')
