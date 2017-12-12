#!/usr/bin/env python3

import os
import tarfile
from termcolor import cprint
from tqdm import tqdm

from ..util import indent


class TarExtract:

    def __init__(self, **build_args):
        pass

    def extract(self, **state):

        # Get our archive and output location
        archive = state['archive']
        basename = os.path.basename(archive)
        dest = os.path.join(state['sources_dir'], basename[:basename.rindex('.t')])

        # If our archive is newer than our folder extract
        if not os.path.exists(dest) or os.path.getmtime(archive) >= os.path.getmtime(dest):
            cprint(indent('Extracting {} to {}'.format(basename, dest), 8), 'green', attrs=['bold'])
            with tarfile.open(archive, 'r') as tf:

                # Find the leading directory prefix
                prefix = os.path.commonpath([n.name for n in tf.getmembers()])

                for f in tqdm(tf.getmembers(), unit='files'):

                    # Remove the common prefix and extract
                    if f.name is not prefix:
                        f.name = os.path.relpath(f.name, prefix)
                        tf.extract(f, dest)

            # Touch the folder.
            os.utime(dest)

        else:
            cprint(indent('Archive {} already extracted... Skipping...'.format(basename), 8), 'yellow', attrs=['bold'])

        return {'source': dest}
