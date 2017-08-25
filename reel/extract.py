#!/usr/bin/env python3

import os
import tarfile
from termcolor import cprint
from tqdm import tqdm

def extract(path, dest):

    # If our archive is newer than our folder extract
    if not os.path.exists(dest) or os.path.getmtime(path) > os.path.getmtime(dest):
        cprint('Extracting {} to {}'.format(path, dest), 'green', attrs=['bold'])
        with tarfile.open(path, 'r') as tf:

            # Find the leading directory prefix
            prefix = os.path.commonpath([n.name for n in tf.getmembers()])

            for f in tqdm(tf.getmembers(), unit='files'):

                # Remove the common prefix and extract
                if f.name is not prefix:
                    f.name = os.path.relpath(f.name, prefix)
                    tf.extract(f, dest)
    else:
        cprint('Archive {} already extracted... Skipping...'.format(path), 'green', attrs=['bold'])
