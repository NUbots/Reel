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

r.add_library(name='icu', src_dir='source', url='http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-src.tgz')

r.add_library(
    Shell(
        post_configure='cp {} {}'.format(os.path.join('{build}', 'bjam'), os.path.join('{prefix_dir}', 'bin', 'bjam'))
    ),
    name='bjam',
    url='https://dl.bintray.com/boostorg/release/1.64.0/source/boost_1_64_0.tar.gz',
    configure_args={'--with-python': 'python3',
                    '--with-icu': '{prefix_dir}'},
    build_targets=[],
    install_targets=[]
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

    t.add_library(
        name='nuclear',
        url='https://github.com/Fastcode/NUClear/archive/master.tar.gz',
        configure_args={
            '-DBUILD_TESTS': 'OFF',
        }
    )

    t.add_library(
        name='openblas',
        url='https://github.com/xianyi/OpenBLAS/archive/v0.2.19.tar.gz',
        build_tool='make',
        build_args={
            'CROSS': '1',
            'TARGET': 'HASWELL' if t.name == 'nuc7i7bnh' else 'ARMV8',
            'USE_THREAD': '1',
            'BINARY': '64',
            'NUM_THREADS': '2',
            'HOSTCC': t.parent_toolchain.env['CC']
        }
    )

    t.add_library(name='libsvm', url='https://github.com/Bidski/libsvm/archive/v322.tar.gz')

    t.add_library(
        name='armadillo',
        url='https://downloads.sourceforge.net/project/arma/armadillo-7.950.1.tar.xz',
        build_tool='cmake',
        configure_args={
            '-DLAPACK_LIBRARY': os.path.join('{prefix_dir}', 'lib', 'libopenblas.so'),
            '-DARPACK_LIBRARY': os.path.join('{prefix_dir}', 'lib', 'libopenblas.so')
        }
    )

    t.add_library(
        name='yaml-cpp',
        url='https://github.com/jbeder/yaml-cpp/archive/master.tar.gz',
        configure_args={
            '-DYAML_CPP_BUILD_CONTRIB': 'OFF',
            '-DYAML_CPP_BUILD_TOOLS': 'OFF'
        }
    )

    # Double precision FFTW3 library
    t.add_library(
        name='fftw3',
        url='http://www.fftw.org/fftw-3.3.7.tar.gz',
        configure_args={
            '--enable-openmp': True,
            '--enable-threads': True
        }
    )

    # Single precision FFTW3 library
    t.add_library(
        name='fftw3f',
        url='http://www.fftw.org/fftw-3.3.7.tar.gz',
        configure_args={
            '--enable-openmp': True,
            '--enable-threads': True,
            '--enable-float': True
        }
    )

    t.add_library(
        name='jpeg-turbo',
        url='http://downloads.sourceforge.net/project/libjpeg-turbo/1.5.1/libjpeg-turbo-1.5.1.tar.gz',
        configure_args={
            'CCASFLAGS': '-f elf64'
        }
    )

    t.add_library(name='fmt', url='https://github.com/fmtlib/fmt/archive/3.0.1.tar.gz')

    t.add_library(UpdateConfigSub, name='portaudio', url='http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz')

    t.add_library(
        name='eigen3',
        url='http://bitbucket.org/eigen/eigen/get/3.3.4.tar.bz2',
        configure_args={
            # Eigen doesn't know how to MinSizeRel.
            '-DCMAKE_BUILD_TYPE': 'RelWithDebInfo'
        }
    )

    t.add_library(
        name='icu',
        src_dir='source',
        url='http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-src.tgz',
        configure_args={
            # We need to specify the build directory as necessary cross-tools are not installed.
            '--with-cross-build': os.path.abspath(os.path.join('{parent_builds_dir}', 'icu4c-60_2-src')),
            '--disable-tests': True,
            '--disable-samples': True
        }
    )

    t.add_library(
        name='boost',
        url='https://dl.bintray.com/boostorg/release/1.64.0/source/boost_1_64_0.tar.gz',
        configure_args={'--with-python': 'python3',
                        '--with-icu': '{prefix_dir}'},
        use_bjam=os.path.join('{parent_prefix_dir}', 'bin', 'bjam'),
        env={'BOOST_BUILD_PATH': os.path.abspath('{source}')},
        build_args={
            'address-model': '64',
            'architecture': 'x86' if t.name == 'nuc7i7bnh' else 'arm',
            'link': 'static',
            'variant': 'release',
            'threading': 'multi',
            'threadapi': 'pthread',
            'abi': 'x32' if t.name == 'nuc7i7bnh' else 'aapcs',
            'binary-format': 'elf',
            'target-os': 'linux',
            'toolset': 'gcc',

            # Unable to cross compule boost.context for ARM (other modules depend on boost.context)
            '--without-context': True if t.name == 'jetsontx2' else False,
            '--without-coroutine': True if t.name == 'jetsontx2' else False,
            '--without-coroutine2': True if t.name == 'jetsontx2' else False,
            '--without-fiber': True if t.name == 'jetsontx2' else False
        },
        install_args={
            'address-model': '64',
            'architecture': 'x86' if t.name == 'nuc7i7bnh' else 'arm',
            'link': 'static',
            'variant': 'release',
            'threading': 'multi',
            'threadapi': 'pthread',
            'abi': 'x32' if t.name == 'nuc7i7bnh' else 'aapcs',
            'binary-format': 'elf',
            'target-os': 'linux',
            'toolset': 'gcc',

            # Unable to cross compule boost.context for ARM (other modules depend on boost.context)
            '--without-context': True if t.name == 'jetsontx2' else False,
            '--without-coroutine': True if t.name == 'jetsontx2' else False,
            '--without-coroutine2': True if t.name == 'jetsontx2' else False,
            '--without-fiber': True if t.name == 'jetsontx2' else False
        }
    )

    t.add_library(
        Shell(
            pre_configure='cp {} {}'.format(
                os.path.abspath(os.path.join('{source}', 'src', 'portaudio19.h')),
                os.path.abspath(os.path.join('{source}', 'src', 'portaudio.h'))
            )
        ),
        name='espeak',
        src_dir='src',
        url='https://github.com/Bidski/espeak/archive/master.tar.gz',
        env={'AUDIO': 'PORTAUDIO'},
        build_args={'DATADIR': os.path.join('{prefix_dir}', 'share', 'espeak-data')},
        install_args={
            'DATADIR': os.path.join('{prefix_dir}', 'share', 'espeak-data'),
            'SRC_DIR': os.path.abspath(os.path.join('{source}', 'src'))
        }
    )

    t.add_library(
        name='fswatch',
        url='https://github.com/emcrisostomo/fswatch/releases/download/1.9.3/fswatch-1.9.3.tar.gz',
        src_dir='fswatch-1.9.3'
    )

r.build()

# libasound2
# libusb
# tcmalloc
# espeak
# fswatch
# catch
# aravis
