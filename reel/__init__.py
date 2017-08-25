#!/usr/bin/env python3

from .Toolchain import Toolchain
from .Library import Library
from tqdm import tqdm
import requests
from dateutil import parser
import time
import tarfile
import os
from termcolor import cprint

def download_source(url, dest):

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

def extract_archive(path, dest):

    # If our archive is newer than our folder extract
    if not os.path.exists(dest) or os.path.getmtime(path) > os.path.getmtime(dest):
        cprint('Extracting ' + path + ' to ' + dest, 'green', attrs=['bold'])
        with tarfile.open(path, 'r') as tf:
            for f in tqdm(tf.getmembers()):
                tf.extract(f, dest)
    else:
        cprint('Archive ' + path + ' already extracted... Skipping...', 'green', attrs=['bold'])


class Reel:

    def __init__(self):
        self.toolchains = []

    def add_toolchain(self, name):
        t = Toolchain(name)

        self.toolchains.append(t)

        return t

    def build(self):

        # Setup our directories
        toolchain_path = 'toolchain'
        working_path = os.path.join('toolchain', 'toolchain_build')
        archive_path = os.path.join(working_path, 'archive')
        src_path = os.path.join(working_path, 'src')
        build_path = os.path.join(working_path, 'build')
        logs_path = os.path.join(working_path, 'log')

        # Make our directories if they do not already exist
        os.makedirs(toolchain_path, exist_ok=True)
        os.makedirs(working_path, exist_ok=True)
        os.makedirs(archive_path, exist_ok=True)
        os.makedirs(src_path, exist_ok=True)
        os.makedirs(build_path, exist_ok=True)
        os.makedirs(logs_path, exist_ok=True)

        # Download our source code
        download_source(url='https://ftpmirror.gnu.org/gnu/gcc/gcc-7.1.0/gcc-7.1.0.tar.bz2',
                        dest=os.path.join(archive_path, 'gcc.tar.bz2'))
        download_source(url='https://www.musl-libc.org/releases/musl-1.1.16.tar.gz',
                        dest=os.path.join(archive_path, 'musl.tar.gz'))
        download_source(url='https://ftpmirror.gnu.org/gnu/binutils/binutils-2.28.tar.bz2',
                        dest=os.path.join(archive_path, 'binutils.tar.bz2'))
        download_source(url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
                        dest=os.path.join(archive_path, 'libbacktrace.tar.gz'))

        # Uncompress the archives
        extract_archive(path=os.path.join(archive_path, 'gcc.tar.bz2'),
                        dest=os.path.join(src_path, 'gcc'))
        extract_archive(path=os.path.join(archive_path, 'musl.tar.gz'),
                        dest=os.path.join(src_path, 'musl'))
        extract_archive(path=os.path.join(archive_path, 'binutils.tar.bz2'),
                        dest=os.path.join(src_path, 'binutils'))
        extract_archive(path=os.path.join(archive_path, 'libbacktrace.tar.gz'),
                        dest=os.path.join(src_path, 'libbacktrace'))


