#!/usr/bin/env python3

from termcolor import cprint
from collections import OrderedDict

from .util import indent


class Library:
    def __init__(self, toolchain, *phase_handlers, **kwargs):

        # Our toolchain object
        self.toolchain = toolchain

        # Our name
        self.name = kwargs.get('name')

        # Our phase handler instances
        self.handlers = []

        # Our phase functions
        self.phase = OrderedDict([
            ('pre_download', None),
            ('download', None),
            ('post_download', None),
            ('pre_extract', None),
            ('extract', None),
            ('post_extract', None),
            ('pre_configure', None),
            ('configure', None),
            ('post_configure', None),
            ('pre_build', None),
            ('build', None),
            ('post_build', None),
            ('pre_install', None),
            ('install', None),
            ('post_install', None),
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

        cprint(
            'Building library {0} of {1}'.format(
                self.name, self.toolchain.state['toolchain_name']),
            'cyan',
            attrs=['bold'])

        state = self.toolchain.state.copy()

        for p, f in self.phase.items():
            if f is not None:
                cprint(
                    indent('Running phase {} for {}'.format(p, self.name)),
                    'magenta',
                    attrs=['bold'])
                new_state = f(**state)
                if new_state is not None:
                    state.update(new_state)
