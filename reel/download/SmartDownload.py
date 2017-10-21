#!/usr/bin/env python3

from .HTTPDownload import HTTPDownload

class SmartDownload:
    def __init__(self, **kwargs):

        # Start without a downloader
        self._downloader = None

        url = kwargs.get('url')

        # If we have a URL
        if url is not None:

            # If we have a http, https use our HTTP downloader
            if url.startswith('http://') or url.startswith('https://'):
                self._downloader = HTTPDownload(**kwargs)


    def download(self, **kwargs):
        return self._downloader.download(**kwargs)
