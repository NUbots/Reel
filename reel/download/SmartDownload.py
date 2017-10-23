#!/usr/bin/env python3

from .HTTPDownload import HTTPDownload

class SmartDownload:
    def __init__(self, **build_args):

        # Start without a downloader
        self._downloader = None

        url = build_args.get('url')

        # If we have a URL
        if url is not None:

            # If we have a http, https use our HTTP downloader
            if url.startswith('http://') or url.startswith('https://'):
                self._downloader = HTTPDownload(**build_args)


    def download(self, **state):
        return self._downloader.download(**state)
