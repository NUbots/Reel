#!/usr/bin/env python3

import os
from termcolor import cprint
from collections import OrderedDict
from functools import partial

class Library:
    def __init__(self, name, toolchain, *phase_handlers, **kwargs):

        # The name of this library
        self.name = name

        # Our toolchain object
        self.toolchain = toolchain

        # Our phase handler instances
        self.handlers = []

        # Our phase functions
        self.phase = OrderedDict([
            ('pre_download',    None),
            ('download',        None),
            ('post_download',   None),
            ('pre_extract',     None),
            ('extract',         None),
            ('post_extract',    None),
            ('pre_configure',   None),
            ('configure',       None),
            ('post_configure',  None),
            ('pre_build',       None),
            ('build',           None),
            ('post_build',      None),
            ('pre_install',     None),
            ('install',         None),
            ('post_install',    None),
        ])

        # Get all our phase handlers and construct them
        # The last implementation of a phase is the one that gets used
        for ph in phase_handlers:
            handler = ph(**kwargs)

            # Bind in the functions provided
            for p in self.phase:
                if hasattr(handler, p):
                    self.phase[p] = getattr(handler, p)


    def build(self):

        state = {
            'prefix_dir': self.toolchain.prefix_dir,
            'working_dir': self.toolchain.working_dir,
            'archive_dir': self.toolchain.archive_dir,
            'sources_dir': self.toolchain.sources_dir,
            'build_dir': self.toolchain.build_dir,
            'logs_dir': self.toolchain.logs_dir,
        }

        for p, f in self.phase.items():
            if f is not None:
                cprint('{} {}'.format(p.capitalize(), self.name), 'green', attrs=['bold'])
                state.update(f(**state))

        # # Work out where our files go
        # # TODO these don't have extensions at the moment
        # archive_path = os.path.join(self.toolchain.archive_path, self.name)
        # src_path = os.path.join(self.toolchain.src_path, self.name)

        # # Download our archive
        # download(self.url, archive_path)
        # extract(archive_path, src_path)
