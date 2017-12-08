#!/usr/bin/env python3

import os
import time
import requests
import rfc6266
from dateutil import parser
from termcolor import cprint
from tqdm import tqdm

from ..util import indent, get_status, update_status


class HTTPDownload:
    def __init__(self, **kwargs):
        self.url = kwargs['url']
        pass

    def download(self, **kwargs):

        # Get the headers for the URL
        head = requests.head(self.url, allow_redirects=True)
        headers = head.headers

        # Extract a filename
        filename = rfc6266.parse_requests_response(head).filename_unsafe

        # Work out our output path
        output_file = os.path.join(kwargs['archives_dir'], filename)

        status_file = os.path.join(kwargs['status_dir'],
                                   '{}.json'.format(filename))

        # Load the status file.
        status = get_status(status_file)

        # If our file exists compare the last modified of our file vs the one on the server
        if os.path.exists(output_file):

            # Check if we have a last modified value in our header
            if 'Last-Modified' in headers:

                # Get when the local and remote files were last modified
                l_modified = os.path.getmtime(output_file)
                r_modified = time.mktime(
                    parser.parse(headers['Last-Modified']).timetuple())

                # If we were modified after we don't need to download again
                if l_modified > r_modified:
                    cprint(
                        indent('URL {} not modified... Skipping...'.format(
                            filename), 8),
                        'yellow',
                        attrs=['bold'])
                    return {'archive': output_file}

            # If there is an etag we can use we can check that hasn't changed
            elif 'Etag' in headers:
                if 'download_etag' not in status or status['download_etag'] != headers['Etag']:
                    status = update_status(status_file, {
                        'download_etag': headers['Etag']
                    })
                else:
                    cprint(
                        indent('URL {} not modified... Skipping...'.format(
                            filename), 8),
                        'yellow',
                        attrs=['bold'])
                    return {'archive': output_file}

        cprint(
            indent('Downloading {}'.format(filename), 8),
            'green',
            attrs=['bold'])

        # Do our get request
        r = requests.get(self.url, allow_redirects=True, stream=True)

        # Total size in bytes.
        total_size = int(r.headers.get('content-length', 0))

        # Get the file
        with open(output_file, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as progress:
                for data in r.iter_content(32 * 1024):
                    f.write(data)
                    progress.update(len(data))

        # Return our updates to state
        return {'archive': output_file}
