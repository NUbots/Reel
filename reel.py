#!/usr/bin/env python3

import os

from reel.patch import UpdateConfigSub
from reel import Shell
from reel import Reel

r = Reel()  #gnu_mirror='http://gnu.uberglobalmirror.com')

r.add_library(
    name='gperf',
    url='https://ftpmirror.gnu.org/gnu/gperf/gperf-3.1.tar.gz',
)

r.add_library(
    name='readline',
    url='https://ftpmirror.gnu.org/gnu/readline/readline-7.0.tar.gz',
)

r.add_library(
    url='https://github.com/libexpat/libexpat/releases/download/R_2_2_5/expat-2.2.5.tar.bz2',
    name='expat',
    configure_args={
        '--without-docbook': True
    }
)

r.add_library(url='https://downloads.sourceforge.net/project/libpng/libpng16/1.6.34/libpng-1.6.34.tar.xz', name='png')

r.install_X11()
r.install_tcltk()

r.add_library(
    UpdateConfigSub,
    url='http://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.4.2.tar.gz',
    name='mpdec',
    in_source_build=True,
    build_targets=['default']
)

r.add_library(
    url='https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz',
    name='python',
    env={
        # Configure needs some help finding the curses headers.
        'CPPFLAGS': '{} -I{}/include/ncurses'.format(r.toolchain.env.get('CPPFLAGS', ''), '{prefix_dir}'),
        'CFLAGS': '{} -I{}/include/ncurses'.format(r.toolchain.env.get('CFLAGS', ''), '{prefix_dir}'),
        'CXXFLAGS': '{} -I{}/include/ncurses'.format(r.toolchain.env.get('CXXFLAGS', ''), '{prefix_dir}'),
        'LDFLAGS': '{} -L{}/lib'.format(r.toolchain.env.get('LDFLAGS', ''), '{prefix_dir}')
    },
    configure_args={
        '--enable-ipv6': True,
        '--with-system-ffi': True,
        '--with-system-expat': True,
        '--with-system-libmpdec': True,
        '--with-threads': True
    }
)

r.add_library(
    url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
    name='protobuf',
    configure_args={
        '--with-zlib': True
    }
)

toolchains = [
    r.add_toolchain('nuc7i7bnh', triple='x86_64-linux-musl'),
    r.add_toolchain('jetsontx2', triple='aarch64-linux-musl')
]

for t in toolchains:
    t.add_library(
        UpdateConfigSub,
        name='libbacktrace',
        url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
        install_targets=['install-strip']
    )

    t.install_linux_headers()

    t.add_library(
        name='util-linux',
        url='https://www.kernel.org/pub/linux/utils/util-linux/v2.31/util-linux-2.31.tar.xz',
        configure_args={
            '--disable-all-programs': True,
            '--enable-libblkid': True,
            '--enable-libmount': True,
            '--without-python': True
        }
    )

    t.install_compression_libraries(zlib=True, bzip2=True, xz=True)

    t.add_library(
        url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
        name='protobuf',
        env={'CC_FOR_BUILD': t.parent_toolchain.env['CC'],
             'CXX_FOR_BUILD': t.parent_toolchain.env['CXX']},
        configure_args={
            '--with-zlib': True,
            '--with-protoc': os.path.join('{parent_prefix_dir}', 'bin', 'protoc')
        }
    )

    t.add_library(
        url='https://github.com/libexpat/libexpat/releases/download/R_2_2_5/expat-2.2.5.tar.bz2',
        name='expat',
        configure_args={
            '--without-docbook': True
        }
    )

    t.add_library(
        url='https://github.com/libffi/libffi/archive/v3.2.1.tar.gz',
        name='ffi',
    )

    t.add_library(
        url='https://downloads.sourceforge.net/project/libpng/libpng16/1.6.34/libpng-1.6.34.tar.xz',
        name='png',
    )

    t.install_X11()
    t.install_tcltk()

    t.add_library(
        UpdateConfigSub,
        url='http://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.4.2.tar.gz',
        name='mpdec',
        in_source_build=True,
        build_targets=['default']
    )

    t.add_library(
        name='ncurses',
        url='https://ftpmirror.gnu.org/gnu/ncurses/ncurses-6.0.tar.gz',
        env={'CPPFLAGS': '-P'},
        configure_args={
            '--with-build-cc': r.toolchain.env['CC'],
            '--with-normal': True,
            '--with-debug': True,
            '--with-profile': True,
            '--with-termlib': True,
            '--with-ticlib': True,
            '--with-gpm': True,
            '--enable-sp-funcs': True,
            '--enable-const': True,
            '--enable-ext-colors': True,
            '--enable-ext-mouse': True,
            '--enable-ext-putwin': True,
            '--enable-no-padding': True,
            '--enable-sigwinch': True,
            '--enable-tcap-names': True
        }
    )

    t.add_library(
        name='readline',
        url='https://ftpmirror.gnu.org/gnu/readline/readline-7.0.tar.gz',
    )

    t.add_library(
        Shell(
            configure='base_dir=$(pwd)'
            ' && mkdir -p {builds_dir}/$(basename {source})'
            ' && cd {builds_dir}/$(basename {source})'
            ' && $base_dir/{source}/Configure'
            '    --prefix={prefix_dir} '
            '    --libdir=lib'
            '    --release'
            '    no-async'
            '    linux-{arch}'
        ),
        Shell(build='cd {builds_dir}/$(basename {source})'
              ' && make'),
        Shell(install='cd {builds_dir}/$(basename {source})'
              ' && make install'),
        name='openssl',
        url='https://www.openssl.org/source/openssl-1.1.0f.tar.gz',
        env={
            'CROSS_COMPILE': ' '
        }
    )

    PYTHON_PROJECT_BASE = '_PYTHON_PROJECT_BASE={}'.format(
        os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.3'))
    )
    PYTHON_HOST_PLATFORM = '_PYTHON_HOST_PLATFORM=linux-{arch}'
    PYTHONPATH = 'PYTHONPATH={}{}{}'.format(
        os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.3')), os.pathsep,
        os.path.abspath(os.path.join(t.state['sources_dir'], 'Python-3.6.3'))
    )
    t.add_library(
        url='https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz',
        name='python',
        env={
            # Configure cant run all tests.
            'ac_cv_file__dev_ptmx': 'no',
            'ac_cv_file__dev_ptc': 'no',

            # Configure needs some help finding the curses headers.
            'CPPFLAGS': '{} -I{}/include/ncurses'.format(t.env.get('CPPFLAGS', ''), '{prefix_dir}'),
            'CFLAGS': '{} -I{}/include/ncurses'.format(t.env.get('CFLAGS', ''), '{prefix_dir}'),
            'CXXFLAGS': '{} -I{}/include/ncurses'.format(t.env.get('CXXFLAGS', ''), '{prefix_dir}'),

            # We need to be able to find the systems python to perform cross-compilation.
            '_PYTHON_PROJECT_BASE': '{}'.format(os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.3'))),
            '_PYTHON_HOST_PLATFORM': 'linux-{arch}',
            'PYTHONPATH':
                '{}{}{}'.format(
                    os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.3')), os.pathsep,
                    os.path.abspath(os.path.join(t.state['sources_dir'], 'Python-3.6.3'))
                ),
            'PYTHON_FOR_BUILD': os.path.join(t.state['parent_prefix_dir'], 'bin', 'python3.6')
        },
        configure_args={
            '--enable-ipv6': True,
            '--with-system-ffi': True,
            '--with-system-expat': True,
            '--with-system-libmpdec': True,
            '--with-threads': True
        }
    )

    t.add_library(
        name='xml2',
        url='http://xmlsoft.org/sources/libxml2-2.9.3.tar.gz',
        env={
            'PYTHONPATH': os.path.abspath(os.path.join('{prefix_dir}', 'lib', 'python3.6', 'site-packages')),
        },
        configure_args={
            '--with-zlib': '{prefix_dir}',
            '--with-python': '{prefix_dir}',
            '--with-python-install-dir':
                os.path.abspath(os.path.join('{prefix_dir}', 'lib', 'python3.6', 'site-packages')),
        }
    )

r.build()

# python3

# libasound2
# libusb
# xml2
# nuclear
# openblas
# libsvm
# armadillo
# tcmalloc
# yaml-cpp
# fftw3
# fftw3f
# jpeg-turbo
# fmt
# portaudio
# eigen3
# boost (damn :'( )
# espeak
# fswatch
# catch
# aravis
