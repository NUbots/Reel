#!/usr/bin/env python3

import os
import tarfile
from termcolor import cprint
from tqdm import tqdm

def extract(path, dest):

    # If our archive is newer than our folder extract
    if not os.path.exists(dest) or os.path.getmtime(path) > os.path.getmtime(dest):
        cprint('Extracting ' + path + ' to ' + dest, 'green', attrs=['bold'])
        with tarfile.open(path, 'r') as tf:
            for f in tqdm(tf.getmembers(), unit='files'):
                tf.extract(f, dest)
    else:
        cprint('Archive ' + path + ' already extracted... Skipping...', 'green', attrs=['bold'])
