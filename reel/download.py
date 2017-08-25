#!/usr/bin/env python3

import os
import time
import requests
from dateutil import parser
from termcolor import cprint
from tqdm import tqdm

def download(url, dest):

    # TODO handle git urls (and maybe this doesn't handle FTP not sure)

    # If our file exists compare the last modified of our file vs the one on the server
    if os.path.exists(dest):

        # Get the headers
        h = requests.head(url, allow_redirects=True).headers

        # Check if we have a last modified value in our header
        if 'Last-Modified' in h:

            # Get when the local and remote files were last modified
            l_modified = os.path.getmtime(dest)
            r_modified = time.mktime(parser.parse(h['Last-Modified']).timetuple())

            # If we were modified after we don't need to download again
            if l_modified > r_modified:
                cprint(dest + ' not modified... Skipping...', 'green', attrs=['bold'])
                return

        # If there is an etag we can use we can check that hasn't changed
        elif 'Etag' in h:
            pass

    cprint('Downloading ' + dest, 'green', attrs=['bold'])

    # Do our get request
    r = requests.get(url, allow_redirects=True, stream=True)

    # Total size in bytes.
    total_size = int(r.headers.get('content-length', 0));

    # Get the file
    with open(dest, 'wb') as f:
        progress = tqdm(r.iter_content(32*1024), total=total_size, unit='B', unit_scale=True)
        for data in progress:
            f.write(data)
            progress.update(len(data))
