#!/usr/bin/env python3

import os
import patch
from functools import partial
from termcolor import cprint

from .util import indent, get_status, update_status, is_sequence


class Patch:

    class PatchSet:

        def execute(self, phase, patch_uri, build_args, **state):

            # Build our environment variables
            env = dict(os.environ)

            # Merge in extra env
            if 'env' in build_args:
                env.update(build_args['env'])

            # We need the actual source path to actually apply a patch
            if 'source' in state:
                src_path = state['source']
                base_src = os.path.basename(src_path)
                status_path = os.path.join(state['patches_dir'], '{}.json'.format(base_src))
                logs_path = os.path.join(state['logs_dir'], base_src)

            else:
                raise Exception('Unable to apply a patch without a source directory')

            # Load the status file
            status = get_status(status_path)

            if phase not in status or not status[phase]:
                os.makedirs(logs_path, exist_ok=True)

                with open(os.path.join(logs_path, '{}_{}.log'.format(base_src, phase)), 'w') as logfile:
                    if is_sequence(patch_uri):
                        patch_uris = patch_uri
                    else:
                        patch_uris = [patch_uri]

                    errors = False
                    for patch_uri in patch_uris:
                        try:
                            if patch_uri.startswith(('http', 'ftp')):
                                cprint(
                                    indent('Applying patch from URL to "{}"'.format(base_src), 8),
                                    'white',
                                    attrs=['bold']
                                )
                                logfile.write('Applying patch from URL "{}" to "{}"\n'.format(patch_uri, base_src))
                                pset = patch.fromurl(patch_uri)
                            elif os.path.exists(patch_uri):
                                cprint(
                                    indent('Applying patch from local file to "{}"'.format(base_src), 8),
                                    'white',
                                    attrs=['bold']
                                )
                                logfile.write(
                                    'Applying patch from local file "{}" to "{}"\n'.format(patch_uri, base_src)
                                )
                                pset = patch.fromfile(patch_uri)
                            else:
                                cprint(
                                    indent('Applying patch from string to "{}"'.format(base_src), 8),
                                    'white',
                                    attrs=['bold']
                                )
                                logfile.write('Applying patch from string "{}" to "{}"\n'.format(patch_uri, base_src))

                                # Strings have to be bytes encoded
                                pset = patch.fromstring(patch_uri.encode('utf-8'))

                        except:
                            pset = False
                            pass

                        if not pset:
                            errors = True
                            cprint(indent('Failed to load patch "{}"'.format(patch_uri), 8), 'red', attrs=['bold'])

                        root_folder = build_args.get('patch_root', src_path)
                        patch.streamhandler = patch.logging.StreamHandler(stream=logfile)
                        patch.setdebug()
                        if pset and not pset.apply(root=root_folder):
                            errors = True
                            cprint(
                                indent('Failed to apply patch "{}" to "{}"'.format(patch_uri, base_src), 8),
                                'red',
                                attrs=['bold']
                            )

                    if errors:
                        raise Exception('{} step for {} failed to apply patches'.format(phase, base_src))

                    else:
                        status = update_status(status_path, {phase: True})

            else:
                cprint(
                    indent('{} step for {} complete... Skipping...'.format(phase, base_src), 8),
                    'yellow',
                    attrs=['bold']
                )

    def __init__(self, **commands):
        self.commands = commands

    def __call__(self, **build_args):

        v = Patch.PatchSet()

        for k in self.commands:
            setattr(v, k, partial(v.execute, k, self.commands[k], build_args))

        return v
