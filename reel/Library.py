#!/usr/bin/env python3

import os
from .download import download
from .extract import extract

class Library:
    def __init__(self, toolchain, name, url):
        self.toolchain = toolchain
        self.name = name
        self.url = url

    def build(self):

        # Work out where our files go
        # TODO these don't have extensions at the moment
        archive_path = os.path.join(self.toolchain.archive_path, self.name)
        src_path = os.path.join(self.toolchain.src_path, self.name)

        # Download our archive
        download(self.url, archive_path)
        extract(archive_path, src_path)
