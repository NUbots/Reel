#!/usr/bin/env python3

import os
import tarfile
from termcolor import cprint
from tqdm import tqdm

class TarExtract:
    def __init__(self, **build_args):
        pass

    def extract(self, **state):

        # Get our archive and output location
        archive = state['archive']
        basename = os.path.basename(archive)
        dest = os.path.join(state['sources_dir'], basename[:basename.rindex('.t')])

        # If our archive is newer than our folder extract
        if not os.path.exists(dest) or os.path.getmtime(archive) > os.path.getmtime(dest):
            cprint('Extracting {} to {}'.format(basename, dest), 'green', attrs=['bold'])
            with tarfile.open(archive, 'r') as tf:

                # Find the leading directory prefix
                prefix = os.path.commonpath([n.name for n in tf.getmembers()])

                for f in tqdm(tf.getmembers(), unit='files'):

                    # Remove the common prefix and extract
                    if f.name is not prefix:
                        f.name = os.path.relpath(f.name, prefix)
                        tf.extract(f, dest)
        else:
            cprint('Archive {} already extracted... Skipping...'.format(basename), 'green', attrs=['bold'])

        return {'source': dest}
