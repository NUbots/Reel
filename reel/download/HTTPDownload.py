#!/usr/bin/env python3

import os
import time
import requests
import rfc6266
from urllib.parse import urlsplit
from dateutil import parser
from termcolor import cprint
from tqdm import tqdm

from ..util import indent, get_status, update_status


class HTTPDownload:

    def __init__(self, **build_args):
        self.url = build_args['url']
        pass

    def download(self, **state):

        # Load the status file.
        split = urlsplit(self.url)
        url_status_file = '{}.json'.format(os.path.join(state['archives_dir'], 'status', split.netloc, split.path[1:]))
        url_status = get_status(url_status_file)

        # Get the headers for the URL
        if 'downloaded' not in url_status or not url_status['downloaded']:
            req = requests.get(self.url, allow_redirects=True, stream=True)
            headers = req.headers

            # Extract a filename
            filename = rfc6266.parse_requests_response(req).filename_unsafe

            # Work out our output path
            output_file = os.path.join(state['archives_dir'], filename)

            status_file = os.path.join(state['status_dir'], '{}.json'.format(filename))

            # Load the status file.
            status = get_status(status_file)

            # If our file exists compare the last modified of our file vs the one on the server
            if os.path.exists(output_file):

                # Check if we have a last modified value in our header
                if 'Last-Modified' in headers:

                    # Get when the local and remote files were last modified
                    l_modified = os.path.getmtime(output_file)
                    r_modified = time.mktime(parser.parse(headers['Last-Modified']).timetuple())

                    # If we were modified after we don't need to download again
                    if l_modified > r_modified:
                        cprint(
                            indent('URL {} not modified... Skipping...'.format(filename), 8), 'yellow', attrs=['bold']
                        )

                        url_status = update_status(url_status_file, {'downloaded': True, 'archive': output_file})
                        return {'archive': output_file}

                # If there is an etag we can use we can check that hasn't changed
                elif 'Etag' in headers:
                    if 'download_etag' not in status or status['download_etag'] != headers['Etag']:
                        status = update_status(status_file, {'download_etag': headers['Etag']})
                    else:
                        cprint(
                            indent('URL {} not modified... Skipping...'.format(filename), 8), 'yellow', attrs=['bold']
                        )

                        url_status = update_status(url_status_file, {'downloaded': True, 'archive': output_file})
                        return {'archive': output_file}

            cprint(indent('Downloading {}'.format(filename), 8), 'green', attrs=['bold'])

            # Total size in bytes.
            total_size = int(headers.get('content-length', 0))

            # Get the file
            with open(output_file, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True) as progress:
                    for data in req.iter_content(32 * 1024):
                        f.write(data)
                        progress.update(len(data))

            url_status = update_status(url_status_file, {'downloaded': True, 'archive': output_file})

            # Return our updates to state
            return {'archive': output_file}

        else:
            cprint(
                indent('URL {} not modified... Skipping...'.format(os.path.basename(url_status['archive'])), 8),
                'yellow',
                attrs=['bold']
            )
            return {'archive': url_status['archive']}
