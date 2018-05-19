#!/usr/bin/env python3

import os
import zipfile
from termcolor import cprint
from tqdm import tqdm

from ..util import indent


class ZipExtract:

    def __init__(self, **build_args):
        pass

    def extract(self, **state):

        # Get our archive and output location
        archive = state['archive']
        basename = os.path.basename(archive)
        dest = os.path.join(state['sources_dir'], basename[:basename.rindex('.zip')])

        # If our archive is newer than our folder extract
        if not os.path.exists(dest) or os.path.getmtime(archive) >= os.path.getmtime(dest):
            cprint(indent('Extracting {} to {}'.format(basename, dest), 8), 'green', attrs=['bold'])
            with zipfile.ZipFile(archive, 'r') as zf:

                # Find the leading directory prefix
                prefix = os.path.commonpath(zf.namelist())

                for f in tqdm(zf.namelist(), unit='files'):

                    # Remove the common prefix and extract
                    if f is not prefix:
                        dest_file = os.path.join(dest, os.path.relpath(f, prefix))
                        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                        with open(dest_file, 'wb') as f:
                            f.write(zf.read(f))

            # Touch the folder.
            os.utime(dest)

        else:
            cprint(indent('Archive {} already extracted... Skipping...'.format(basename), 8), 'yellow', attrs=['bold'])

        return {'source': dest}
