#!/usr/bin/env python3

import os
import sys
import argparse
import shutil
import glob
import re

from subprocess import Popen, check_output, PIPE, run
from termcolor import cprint
from tqdm import tqdm

from reel import Python
from reel import Reel
from reel import Shell
from reel.patch import UpdateConfigSub
from reel.util import dedent

r = Reel()

r.add_library(
    name='gperf',
    url='https://ftpmirror.gnu.org/gnu/gperf/gperf-3.1.tar.gz',
)

r.add_library(
    name='readline',
    url='https://ftpmirror.gnu.org/gnu/readline/readline-7.0.tar.gz',
)

r.add_library(
    name='expat',
    url='https://github.com/libexpat/libexpat/releases/download/R_2_2_5/expat-2.2.5.tar.bz2',
    configure_args={
        '--without-docbook': True
    }
)

r.add_library(name='png', url='https://downloads.sourceforge.net/project/libpng/libpng16/1.6.34/libpng-1.6.34.tar.xz')

r.add_library(
    name='jpeg-turbo',
    url='http://downloads.sourceforge.net/project/libjpeg-turbo/1.5.3/libjpeg-turbo-1.5.3.tar.gz',
    configure_args={'CCASFLAGS': '-f elf64'}
)

r.add_library(
    name='protobuf',
    url='https://github.com/google/protobuf/releases/download/v3.5.1/protobuf-cpp-3.5.1.tar.gz',
    configure_args={
        '--with-zlib': True
    }
)

r.add_library(name='icu', src_dir='source', url='http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-src.tgz')

r.add_library(
    name='intltool',
    url='http://launchpad.net/intltool/trunk/0.51.0/+download/intltool-0.51.0.tar.gz',
    # intltool-update has some regex that is incompatible with Perl 5.26
    # https://bugs.launchpad.net/intltool/+bug/1696658
    phases=[
        Shell(
            post_extract='cd {source} && '
            'wget https://raw.githubusercontent.com/Alexpux/MSYS2-packages/master/intltool/perl-5.22-compatibility.patch -O patch'
            ' && patch -Np1 --dry-run -i patch'
            ' ; if [ $? -eq 0 ]; then patch -Np1 -i patch; else exit 0; fi'
        ),
        Shell(
            pre_configure=
            'echo "This library depends on the Perl module \'XML::Parser\', please make sure it is installed."'
        )
    ]
)

r.add_library(
    name='gettext',
    url='https://ftpmirror.gnu.org/gnu/gettext/gettext-0.19.8.1.tar.xz',
    configure_args={
        '--with-sysroot': '"{prefix_dir}"',
        '--disable-java': True,
        '--disable-csharp': True,
        '--enable-relocatable': True
    }
)

# Trent: If you cant do the headers and util-linux then try this https://sourceforge.net/projects/libuuid/
#        fontconfig (in X11) requires libuuid, I assume this library is the same as the util-linux one
r.install_linux_headers()

r.add_library(
    name='util-linux',
    url='https://www.kernel.org/pub/linux/utils/util-linux/v2.31/util-linux-2.31.tar.xz',
    configure_args={
        '--disable-all-programs': True,
        '--enable-libblkid': True,
        '--enable-libmount': True,
        '--enable-libuuid': True,
        '--without-python': True,
        '--with-bashcompletiondir': os.path.join('{prefix_dir}', 'share', 'bash-completion', 'completions')
    }
)

r.install_X11()
r.install_tcltk()

r.add_library(
    name='mpdec',
    url='http://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.4.2.tar.gz',
    phases=[UpdateConfigSub],
    in_source_build=True,
    build_targets=['default']
)

r.add_library(
    name='openblas',
    # Unable to build version 0.2.20
    # https://github.com/xianyi/OpenBLAS/issues/1252
    url='https://github.com/xianyi/OpenBLAS/archive/v0.2.19.tar.gz',
    build_tool='make',
    build_args={
        'DYNAMIC_ARCH': '1',
        'USE_THREAD': '1',
        'TARGET': 'ATOM',
        'BINARY': '64',
        'NUM_THREADS': '2',
    },
    install_args={'DYNAMIC_ARCH': '1'}
)

r.add_library(
    name='python',
    url='https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tar.xz',
    env={
        # Configure needs some help finding the curses headers
        'CPPFLAGS':
            '{} -I{} -I{}'.format(
                r.toolchain.env.get('CPPFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                os.path.join('{prefix_dir}', 'include', 'ncurses')
            ),
        'CFLAGS':
            '{} -I{} -I{}'.format(
                r.toolchain.env.get('CFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                os.path.join('{prefix_dir}', 'include', 'ncurses')
            ),
        'CXXFLAGS':
            '{} -I{} -I{}'.format(
                r.toolchain.env.get('CXXFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                os.path.join('{prefix_dir}', 'include', 'ncurses')
            ),
        'LDFLAGS': '{} -L{}'.format(r.toolchain.env.get('LDFLAGS', ''), os.path.join('{prefix_dir}', 'lib')),
        'LD_LIBRARY_PATH': os.pathsep.join([os.path.join('{prefix_dir}', 'lib'),
                                            os.path.join('{prefix_dir}', 'lib64')]),

        # For installing matplotlib
        'MPLBASEDIRLIST': '{prefix_dir}'
    },
    in_source_build=True,
    configure_args={
        '--enable-ipv6': True,
        '--with-system-ffi': True,
        '--with-system-expat': True,
        '--with-system-libmpdec': True,
        '--with-threads': True
    },
    phases=[
        Shell(
            post_install='pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/pip --upgrade pip'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/numpy numpy'
            ' && LDFLAGS="$LDFLAGS -shared" pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/scipy scipy'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/matplotlib matplotlib'
            ' && pip3 --cache-dir {prefix_dir}/temp install --global-option="build_ext" --global-option="--disable-platform-guessing" --build {prefix_dir}/temp/pillow pillow'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/scikit-image scikit-image'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/pyyaml pyyaml'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/yapf yapf'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/xxhash xxhash'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/protobuf protobuf==3.5.1'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/termcolor termcolor'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/stringcase stringcase'
            ' && pip3 --cache-dir {prefix_dir}/temp install --build {prefix_dir}/temp/pillow pillow'
        )
    ]
)

r.add_library(
    name='bjam',
    url='https://dl.bintray.com/boostorg/release/1.66.0/source/boost_1_66_0.tar.bz2',
    phases=[
        Shell(
            post_configure='cp -v {} {}'.
            format(os.path.join('{build}', 'bjam'), os.path.join('{prefix_dir}', 'bin', 'bjam'))
        )
    ],
    configure_args={
        '--with-python': os.path.join('{parent_prefix_dir}', 'bin', 'python3'),
        '--with-icu': '{prefix_dir}'
    },
    build_targets=[],
    install_targets=[]
)

nuc7i7bnh_flags = [
    '-march=broadwell', '-mtune=broadwell', '-mmmx', '-mno-3dnow', '-msse', '-msse2', '-msse3', '-mssse3', '-mno-sse4a',
    '-mcx16', '-msahf', '-mmovbe', '-maes', '-mno-sha', '-mpclmul', '-mpopcnt', '-mabm', '-mno-lwp', '-mfma',
    '-mno-fma4', '-mno-xop', '-mbmi', '-mbmi2', '-mno-tbm', '-mavx', '-mavx2', '-msse4.2', '-msse4.1', '-mlzcnt',
    '-mno-rtm', '-mno-hle', '-mrdrnd', '-mf16c', '-mfsgsbase', '-mrdseed', '-mprfchw', '-madx', '-mfxsr', '-mxsave',
    '-mxsaveopt', '-mno-avx512f', '-mno-avx512er', '-mno-avx512cd', '-mno-avx512pf', '-mno-prefetchwt1', '-mclflushopt',
    '-mxsavec', '-mxsaves', '-mno-avx512dq', '-mno-avx512bw', '-mno-avx512vl', '-mno-avx512ifma', '-mno-avx512vbmi',
    '-mno-clwb', '-mno-mwaitx', '--param l1-cache-size=32', '--param l1-cache-line-size=64',
    '--param l2-cache-size=4096'
]

jetsontx2_flags = [
    '-mabi=lp64', '-march=armv8-a+crypto+simd+fp+crc', '-mtune=cortex-a57', '-mabi=lp64', '-mlittle-endian',
    '-mcmodel=small', '-mfix-cortex-a53-835769', '-mfix-cortex-a53-843419', '-mmusl', '-momit-leaf-frame-pointer',
    '-mpc-relative-literal-loads', '-msign-return-address=none', '-mtls-dialect=desc'
]

toolchains = [
    r.add_toolchain(
        'nuc7i7bnh',
        triple='x86_64-linux-musl',
        abi='64',
        c_flags=nuc7i7bnh_flags,
        cxx_flags=nuc7i7bnh_flags,
        fc_flags=nuc7i7bnh_flags
    ),
    r.add_toolchain(
        'jetsontx2',
        triple='aarch64-linux-musl',
        abi='64',
        c_flags=jetsontx2_flags,
        cxx_flags=jetsontx2_flags,
        fc_flags=jetsontx2_flags
    )
]

for t in toolchains:
    t.add_library(
        name='libbacktrace',
        url='https://github.com/ianlancetaylor/libbacktrace/archive/master.tar.gz',
        phases=[UpdateConfigSub],
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
            '--enable-libuuid': True,
            '--without-python': True,
            '--with-bashcompletiondir': os.path.join('{prefix_dir}', 'share', 'bash-completion', 'completions')
        }
    )

    t.install_compression_libraries(zlib=True, bzip2=True, xz=True)

    t.add_library(
        name='protobuf',
        url='https://github.com/google/protobuf/releases/download/v3.5.1/protobuf-cpp-3.5.1.tar.gz',
        env={'CC_FOR_BUILD': t.parent_toolchain.env['CC'],
             'CXX_FOR_BUILD': t.parent_toolchain.env['CXX']},
        configure_args={
            '--with-zlib': True,
            '--with-protoc': os.path.join('{parent_prefix_dir}', 'bin', 'protoc')
        }
    )

    t.add_library(
        name='expat',
        url='https://github.com/libexpat/libexpat/releases/download/R_2_2_5/expat-2.2.5.tar.bz2',
        configure_args={
            '--without-docbook': True
        }
    )

    t.add_library(name='ffi', url='https://github.com/libffi/libffi/archive/v3.2.1.tar.gz')

    t.add_library(
        name='png',
        url='https://downloads.sourceforge.net/project/libpng/libpng16/1.6.34/libpng-1.6.34.tar.xz',
    )

    t.add_library(
        name='libelf',
        url='http://www.mr511.de/software/libelf-0.8.13.tar.gz',
        phases=[UpdateConfigSub],

        # Need to force the results of some configure checks
        env={
            'ac_cv_sizeof_long': '8',
            'ac_cv_sizeof_long_long': '8',
            'libelf_cv_int64': 'long'
        }
    )

    t.add_library(
        name='pcre',
        url='http://ftp.pcre.org/pub/pcre/pcre-8.41.tar.bz2',
        configure_args={
            '--enable-utf': True,
            '--enable-unicode-properties': True
        }
    )

    t.add_library(
        name='glib2',
        url='https://ftp.gnome.org/pub/gnome/sources/glib/2.56/glib-2.56.0.tar.xz',
        phases=[Shell(post_install='cp -v {build}/glib/glibconfig.h {prefix_dir}/include/glibconfig.h')],
        configure_args={
            'glib_cv_stack_grows': 'no',
            'glib_cv_uscore': 'no',
            '--with-threads': 'posix',
            '--with-pcre': 'system',
            '--disable-gtk-doc': True,
            '--disable-man': True
        }
    )

    t.install_X11()
    t.install_tcltk()

    t.add_library(
        name='mpdec',
        url='http://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.4.2.tar.gz',
        phases=[UpdateConfigSub],
        in_source_build=True,
        build_targets=['default']
    )

    t.add_library(
        name='ncurses',
        url='https://ftpmirror.gnu.org/gnu/ncurses/ncurses-6.1.tar.gz',
        env={
            'CPPFLAGS': '-P',
            'TIC_PATH': os.path.join('{parent_prefix_dir}', 'bin', 'tic')
        },
        configure_args={
            # We need the parents compiler for building here.
            '--with-build-cc': r.toolchain.env['CC'],
            '--with-pkg-config': True,
            '--enable-pc-files': True,
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
            '--enable-tcap-names': True,
            '--without-manpages': True,
            '--without-tests': True
        }
    )

    t.add_library(
        name='readline',
        url='https://ftpmirror.gnu.org/gnu/readline/readline-7.0.tar.gz',
    )

    t.add_library(
        name='openssl',
        url='https://www.openssl.org/source/openssl-1.1.0g.tar.gz',
        phases=[
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
                  ' && make install')
        ],
        env={
            'CROSS_COMPILE': ' '
        }
    )

    t.add_library(
        name='python',
        url='https://www.python.org/ftp/python/3.6.4/Python-3.6.4.tar.xz',
        env={
            # Configure cant run all tests
            'ac_cv_file__dev_ptmx': 'no',
            'ac_cv_file__dev_ptc': 'no',

            # Configure needs some help finding the curses headers
            'CPPFLAGS':
                '{} -I{} -I{}'.format(
                    t.env.get('CPPFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                    os.path.join('{prefix_dir}', 'include', 'ncurses')
                ),
            'CFLAGS':
                '{} -I{} -I{}'.format(
                    t.env.get('CFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                    os.path.join('{prefix_dir}', 'include', 'ncurses')
                ),
            'CXXFLAGS':
                '{} -I{} -I{}'.format(
                    t.env.get('CXXFLAGS', ''), os.path.join('{prefix_dir}', 'include'),
                    os.path.join('{prefix_dir}', 'include', 'ncurses')
                ),
            'LDFLAGS': '{} -L{}'.format(t.env.get('LDFLAGS', ''), os.path.join('{prefix_dir}', 'lib')),

            # We need to be able to find the systems python to perform cross-compilation
            '_PYTHON_PROJECT_BASE': '{}'.format(os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.4'))),
            '_PYTHON_HOST_PLATFORM': 'linux-{arch}',
            'PYTHONPATH':
                os.pathsep.join([
                    os.path.abspath(os.path.join(t.state['builds_dir'], 'Python-3.6.4')),
                    os.path.abspath(os.path.join(t.state['sources_dir'], 'Python-3.6.4'))
                ]),
            'PYTHON_FOR_BUILD': os.path.join('{parent_prefix_dir}', 'bin', 'python3')
        },
        in_source_build=True,
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
        url='http://xmlsoft.org/sources/libxml2-2.9.8.tar.gz',
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
        # Unable to build version 0.2.20
        # https://github.com/xianyi/OpenBLAS/issues/1252
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
        url='https://downloads.sourceforge.net/project/arma/armadillo-8.400.0.tar.xz',
        build_tool='cmake',
        configure_args={
            '-DLAPACK_LIBRARY': os.path.join('{prefix_dir}', 'lib', 'libopenblas.so'),
            '-DARPACK_LIBRARY': os.path.join('{prefix_dir}', 'lib', 'libopenblas.so'),
            '-DDETECT_HDF5': 'OFF'
        }
    )

    t.add_library(
        name='yaml-cpp',
        url='https://github.com/jbeder/yaml-cpp/archive/yaml-cpp-0.6.2.tar.gz',
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
        build_postfix='_single',
        configure_args={
            '--enable-openmp': True,
            '--enable-threads': True,
            '--enable-float': True
        }
    )

    t.add_library(
        name='jpeg-turbo',
        url='http://downloads.sourceforge.net/project/libjpeg-turbo/1.5.3/libjpeg-turbo-1.5.3.tar.gz',
        configure_args={
            'CCASFLAGS': '-f elf64'
        }
    )

    t.add_library(name='fmt', url='https://github.com/fmtlib/fmt/archive/4.1.0.tar.gz')

    t.add_library(
        name='portaudio', url='http://www.portaudio.com/archives/pa_stable_v19_20140130.tgz', phases=[UpdateConfigSub]
    )

    t.add_library(
        name='eigen3',
        url='http://bitbucket.org/eigen/eigen/get/3.3.4.tar.bz2',
        configure_args={
            # Eigen doesn't know how to MinSizeRel
            '-DCMAKE_BUILD_TYPE': 'RelWithDebInfo'
        }
    )

    t.add_library(
        name='icu',
        url='http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-src.tgz',
        src_dir='source',
        configure_args={
            # We need to specify the build directory as necessary cross-tools are not installed
            '--with-cross-build': os.path.abspath(os.path.join('{parent_builds_dir}', 'icu4c-60_2-src')),
            '--disable-tests': True,
            '--disable-samples': True
        }
    )

    boost_args = {
        'address-model': t.abi,
        'architecture': 'x86' if t.arch == 'x86_64' else 'arm',
        'link': 'static',
        'variant': 'release',
        'threading': 'multi',
        'threadapi': 'pthread',
        'abi': 'x32' if t.arch == 'x86_64' else 'aapcs',
        'binary-format': 'elf',
        'target-os': 'linux',
        'toolset': 'gcc',

        # Unable to cross compule boost.context for ARM (other modules depend on boost.context)
        '--without-context': True if t.arch == 'aarch64' else None,
        '--without-coroutine': True if t.arch == 'aarch64' else None,
        '--without-fiber': True if t.arch == 'aarch64' else None
    }

    t.add_library(
        name='boost',
        url='https://dl.bintray.com/boostorg/release/1.66.0/source/boost_1_66_0.tar.gz',
        configure_args={'--with-python': 'python3',
                        '--with-icu': '{prefix_dir}'},
        use_bjam=os.path.join('{parent_prefix_dir}', 'bin', 'bjam'),
        env={'BOOST_BUILD_PATH': os.path.abspath('{source}')},
        build_args=boost_args,
        install_args=boost_args
    )

    t.add_library(
        name='espeak',
        url='https://github.com/Bidski/espeak/archive/master.tar.gz',
        phases=[
            Shell(
                pre_configure='cp -v {} {}'.format(
                    os.path.abspath(os.path.join('{source}', 'src', 'portaudio19.h')),
                    os.path.abspath(os.path.join('{source}', 'src', 'portaudio.h'))
                )
            )
        ],
        src_dir='src',
        env={'AUDIO': 'PORTAUDIO'},
        build_args={'DATADIR': os.path.join('{prefix_dir}', 'share', 'espeak-data')},
        install_args={
            'DATADIR': os.path.join('{prefix_dir}', 'share', 'espeak-data'),
            'SRC_DIR': os.path.abspath(os.path.join('{source}', 'src'))
        }
    )

    t.add_library(name='fswatch', url='https://github.com/emcrisostomo/fswatch/archive/1.11.2.tar.gz')

    t.add_library(name='libuv', url='https://github.com/libuv/libuv/archive/v1.19.2.tar.gz')

    t.add_library(name='udev', url='https://dev.gentoo.org/~blueness/eudev/eudev-3.2.5.tar.gz')

    t.add_library(
        name='libusb',
        url='https://github.com/libusb/libusb/releases/download/v1.0.21/libusb-1.0.21.tar.bz2',
        configure_args={
            '--disable-examples-build': True,
            '--disable-tests-build': True
        }
    )

    t.add_library(
        name='aravis',
        url='http://ftp.gnome.org/pub/GNOME/sources/aravis/0.5/aravis-0.5.11.tar.xz',
        phases=[
            Shell(
                post_install='cp -v {} {}'.format(
                    os.path.join('{build}', 'src', 'arvconfig.h'),
                    os.path.join('{prefix_dir}', 'include', 'arvconfig.h')
                )
            )
        ],
        configure_args={
            '--disable-viewer': True,
            '--disable-gst-plugin': True,
            '--disable-gst-0.10-plugin': True,
            '--disable-gtk-doc': True,
            '--disable-gtk-doc-html': True,
            '--disable-gtk-doc-pdf': True,
            '--enable-usb': True,
            '--disable-zlib-pc': True,
            '--disable-nls': True
        }
    )

    t.add_library(
        name='pybind11',
        url='https://github.com/pybind/pybind11/archive/v2.2.2.tar.gz',
        configure_args={
            '-DPYBIND11_TEST': 'OFF',
            '-DPYBIND11_PYTHON_VERSION': '3',

            # Prevent cmake from trying to execute python to find its libraries.
            '-DPYTHON_EXECUTABLE': os.path.join('{prefix_dir}', 'bin', 'python3'),
            '-DPYTHON_LIBRARY': os.path.join('{prefix_dir}', 'lib', 'libpython3.6m.so'),
            '-DPYTHONLIBS_FOUND': 'ON',
            '-DPYTHON_MODULE_EXTENSION': '.cpython-36m-{}-linux-gnu.so'.format(t.arch)
        }
    )

r.build()

# libasound2    Dont know if we actually need this

# tcmalloc      Needs patching for musl
# catch

# command => '/usr/bin/pip3 install pyparsing &&
#             /usr/bin/pip3 install pydotplus &&
#             /usr/bin/pip3 install pygments &&
#             /usr/bin/pip3 install termcolor &&
#             /usr/bin/pip3 install protobuf &&
#             /usr/bin/pip3 install xxhash &&
#             /usr/bin/pip3 install wheel &&
#             /usr/bin/pip3 install numpy &&
#             /usr/bin/pip3 install tensorflow &&
#             /usr/bin/pip3 install mako &&
#             /usr/bin/pip3 install scikit-image &&
#             /usr/bin/pip3 install PyYAML',

# Mesa
# http://www.linuxfromscratch.org/blfs/view/svn/x/mesa.html
# 'pybeaker'     => {'url'         => 'https://files.pythonhosted.org/packages/source/B/Beaker/Beaker-1.9.0.tar.gz',
#                    'args'        => { 'native'   => [ ' --optimize=1',  ],
#                                       'nuc7i7bnh' => [ ' --optimize=1', ], },
#                    'method'      => 'python', },
# 'pymarkupsafe' => {'url'         => 'https://files.pythonhosted.org/packages/source/M/MarkupSafe/MarkupSafe-1.0.tar.gz',
#                    'args'        => { 'native'   => [ ' --optimize=1',  ],
#                                       'nuc7i7bnh' => [ ' --optimize=1', ], },
#                    'method'      => 'python', },
# 'pymako'       => {'url'         => 'https://files.pythonhosted.org/packages/source/M/Mako/Mako-1.0.4.tar.gz',
#                    'args'        => { 'native'   => [ ' --optimize=1',  ],
#                                       'nuc7i7bnh' => [ ' --optimize=1', ], },
#                    'require'     => [ Installer['pybeaker'], Installer['pymarkupsafe'], ],
#                    'method'      => 'python', },
# 'drm'          => {'url'         => 'https://dri.freedesktop.org/libdrm/libdrm-2.4.85.tar.bz2',
#                    'args'        => { 'native'   => [ '--enable-udev', ],
#                                       'nuc7i7bnh' => [ '--enable-udev', ], },
#                    'creates'     => 'lib/libdrm.so',
#                    'require'     => [ Installer['xorg-libs'], ],
#                    'method'      => 'autotools', },
# 'mesa'         => {'url'         => 'https://mesa.freedesktop.org/archive/mesa-17.2.3.tar.xz',
#                    'args'        => { 'native'   => [ '--enable-texture-float', '--enable-osmesa', '--enable-xa', '--enable-glx-tls', '--with-platforms="drm,x11"', '--enable-gles1', '--enable-gles2', '--enable-shared-glapi', '--enable-egl', '--with-dri-drivers="i965,i915"', '--with-gallium-drivers="swrast,svga"', '--with-vulkan-drivers=intel', '--enable-gbm', ],
#                                       'nuc7i7bnh' => [ '--enable-texture-float', '--enable-osmesa', '--enable-xa', '--enable-glx-tls', '--with-platforms="drm,x11"', '--enable-gles1', '--enable-gles2', '--enable-shared-glapi', '--enable-egl', '--with-dri-drivers="i965,i915"', '--with-gallium-drivers="swrast,svga"', '--with-vulkan-drivers=intel', '--enable-gbm', ], },
#                    'creates'     => 'lib/libEGL.so',
#                    'require'     => [ Installer['xorg-libs'], Installer['drm'], ], #Installer['pymako'], ],
#                    'method'      => 'autotools', },
# 'glm'          => {'url'         => 'https://github.com/g-truc/glm/archive/0.9.8.5.tar.gz',
#                    'args'        => { 'native'   => [ '-DGLM_TEST_ENABLE_CXX_14=ON', '-DGLM_TEST_ENABLE_LANG_EXTENSIONS=ON', '-DGLM_TEST_ENABLE_FAST_MATH=ON',  ],
#                                       'nuc7i7bnh' => [ '-DGLM_TEST_ENABLE_CXX_14=ON', '-DGLM_TEST_ENABLE_LANG_EXTENSIONS=ON', '-DGLM_TEST_ENABLE_FAST_MATH=ON',  ], },
#                    'creates'     => 'include/glm/glm.hpp',
#                    'method'      => 'cmake', },

# # Caffe OpenCL
# 'gflags'       => {'url'         => 'https://github.com/gflags/gflags/archive/v2.2.1.tar.gz',
#                    'args'        => { 'native'   => [ '-DBUILD_TESTING=OFF', ],
#                                       'nuc7i7bnh' => [ '-DBUILD_TESTING=OFF', ], },
#                    'creates'     => 'lib/libgflags.a',
#                    'method'      => 'cmake', },
# 'gtest'        => {'url'         => 'https://github.com/google/googletest/archive/release-1.8.0.tar.gz',
#                    'creates'     => 'lib/libgtest.a',
#                    'method'      => 'cmake', },
# 'snappy'       => {'url'         => 'https://github.com/google/snappy/archive/1.1.7.tar.gz',
#                    'args'        => { 'native'   => [ '-DSNAPPY_BUILD_TESTS=OFF', ],
#                                       'nuc7i7bnh' => [ '-DSNAPPY_BUILD_TESTS=OFF', ], },
#                    'require'     => [ Installer['gtest'], Installer['gflags'], ],
#                    'creates'     => 'lib/libsnappy.a',
#                    'method'      => 'cmake', },
# 'leveldb'      => {'url'         => '',
#                    'creates'     => 'lib/leveldb.a',
#                    'prebuild'    => 'wget -N https://github.com/google/leveldb/archive/v1.20.tar.gz &&
#                                      tar -xf v1.20.tar.gz &&
#                                      cd leveldb-1.20 &&
#                                      make -j$(nproc) &&
#                                      cp out-static/lib* out-shared/lib* PREFIX/lib/ &&
#                                      cp -r include/* PREFIX/include/',
#                    'creates'     => 'lib/libleveldb.a',
#                    'require'     => [ Installer['snappy'], ],
#                    'method'      => 'custom', },
# 'lmdb'         => {'url'         => 'https://github.com/LMDB/lmdb/archive/LMDB_0.9.21.tar.gz',
#                    'creates'     => 'lib/liblmdb.so',
#                    'args'        => { 'native'   => [ 'prefix=PREFIX', ],
#                                       'nuc7i7bnh' => [ 'prefix=PREFIX', ], },
#                    'src_dir'     => 'libraries/liblmdb',
#                    'method'      => 'make', },
# 'hdf5'         => {'url'         => 'https://support.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.10.1.tar.gz',
#                    'args'        => { 'native'   => [ '-DHDF5_BUILD_CPP_LIB=ON', '-DHDF5_ENABLE_Z_LIB_SUPPORT=ON', ],
#                                       'nuc7i7bnh' => [ '-DHDF5_BUILD_CPP_LIB=ON', '-DHDF5_ENABLE_Z_LIB_SUPPORT=ON', ], },
#                    'creates'     => 'lib/libhdf5.so',
#                    'method'      => 'cmake', },
# 'glog'         => {'url'         => 'https://github.com/google/glog/archive/v0.3.5.tar.gz',
#                    'args'        => { 'native'   => [ '-DBUILD_TESTING=OFF', ],
#                                       'nuc7i7bnh' => [ '-DBUILD_TESTING=OFF', ], },
#                    'require'     => [ Installer['gflags'], ],
#                    'creates'     => 'lib/libglog.a',
#                    'method'      => 'cmake', },
# 'opencv'       => {'url'         => 'https://github.com/opencv/opencv/archive/3.3.1.tar.gz',
#                    'args'        => { 'native'   => [ '-DOPENCV_ENABLE_NONFREE=ON', '-DWITH_CUDA=OFF', '-DWITH_CUFFT=OFF', '-DWITH_CUBLAS=OFF', '-DWITH_NVCUVID=OFF', '-DWITH_EIGEN=ON', '-DWITH_ARAVIS=ON', '-DWITH_TBB=ON', '-DWITH_OPENMP=ON', '-DWITH_OPENCL=ON', '-DBUILD_opencv_apps=OFFF', '-DBUILD_opencv_js=OFF', '-DBUILD_opencv_python3=ON', '-DBUILD_DOCS=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_PERF_TESTS=OFF', '-DBUILD_TESTS=OFF', '-DBUILD_WITH_DEBUG_INFO=OFF', '-DBUILD_ZLIB=OFF', '-DBUILD_TIFF=ON', '-DBUILD_JASPER=ON', '-DBUILD_JPEG=ON', '-DBUILD_PNG=ON', '-DBUILD_TBB=ON', ],
#                                       'nuc7i7bnh' => [ '-DOPENCV_ENABLE_NONFREE=ON', '-DWITH_CUDA=OFF', '-DWITH_CUFFT=OFF', '-DWITH_CUBLAS=OFF', '-DWITH_NVCUVID=OFF', '-DWITH_EIGEN=ON', '-DWITH_ARAVIS=ON', '-DWITH_TBB=ON', '-DWITH_OPENMP=ON', '-DWITH_OPENCL=ON', '-DBUILD_opencv_apps=OFFF', '-DBUILD_opencv_js=OFF', '-DBUILD_opencv_python3=ON', '-DBUILD_DOCS=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_PERF_TESTS=OFF', '-DBUILD_TESTS=OFF', '-DBUILD_WITH_DEBUG_INFO=OFF', '-DBUILD_ZLIB=OFF', '-DBUILD_TIFF=ON', '-DBUILD_JASPER=ON', '-DBUILD_JPEG=ON', '-DBUILD_PNG=ON', '-DBUILD_TBB=ON', ], },
#                    'require'     => [ Installer['aravis'], Installer['eigen3'], ],
#                    'creates'     => 'lib/libopencv_core.so',
#                    'method'      => 'cmake', },
# 'viennacl'     => {'url'         => 'https://github.com/viennacl/viennacl-dev/archive/release-1.7.1.tar.gz',
#                    'args'        => { 'native'   => [ '-DBUILD_EXAMPLES=OFF', '-DBUILD_TESTING=OFF', '-DOPENCL_LIBRARY=PREFIX/opt/intel/opencl/libOpenCL.so', ],
#                                       'nuc7i7bnh' => [ '-DBUILD_EXAMPLES=OFF', '-DBUILD_TESTING=OFF', '-DOPENCL_LIBRARY=PREFIX/opt/intel/opencl/libOpenCL.so', ], },
#                    'creates'     => 'include/viennacl/version.hpp',
#                    'method'      => 'cmake', },
# 'clfft'        => {'url'         => 'https://github.com/clMathLibraries/clFFT/archive/v2.12.2.tar.gz',
#                    'args'        => { 'native'   => [ '-DBUILD_CLIENT=OFF', '-DBUILD_TEST=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_CALLBACK_CLIENT=OFF', '-DSUFFIX_LIB=""', ],
#                                       'nuc7i7bnh' => [ '-DBUILD_CLIENT=OFF', '-DBUILD_TEST=OFF', '-DBUILD_EXAMPLES=OFF', '-DBUILD_CALLBACK_CLIENT=OFF', '-DSUFFIX_LIB=""', ], },
#                    'creates'     => 'lib/libclFFT.so',
#                    'src_dir'     => 'src',
#                    'require'     => [ Installer['viennacl'], Installer['fftw3f'], Installer['fftw3'], Installer['boost'], ],
#                    'method'      => 'cmake', },
# 'isaac'        => {'url'         => 'https://github.com/intel/isaac/archive/master.tar.gz',
#                    'creates'     => 'lib/libisaac.so',
#                    'require'     => [ Installer['viennacl'], ],
#                    'method'      => 'cmake', },
# 'libdnn'       => {'url'         => 'https://github.com/naibaf7/libdnn/archive/master.tar.gz',
#                    'args'        => { 'native'   => [ '-DUSE_CUDA=OFF', '-DUSE_OPENCL=ON', '-DUSE_INDEX_64=OFF', ],
#                                       'nuc7i7bnh' => [ '-DUSE_CUDA=OFF', '-DUSE_OPENCL=ON', '-DUSE_INDEX_64=OFF', ], },
#                    'creates'     => 'lib/libgreentea_libdnn.so',
#                    'require'     => [ Installer['viennacl'], ],
#                    'method'      => 'cmake', },
# 'caffe'        => {'url'         => 'https://github.com/01org/caffe/archive/inference-optimize.tar.gz',
#                    'prebuild'    => 'export ISAAC_HOME=PREFIX',
#                    'args'        => { 'native'   => [ '-DUSE_GREENTEA=ON', '-DUSE_CUDA=OFF', '-DUSE_INTEL_SPATIAL=ON', '-DBUILD_docs=OFF', '-DUSE_ISAAC=ON', '-DViennaCL_INCLUDE_DIR=PREFIX/include', '-DBLAS=Open', '-DOPENCL_LIBRARIES=PREFIX/opt/intel/opencl/libOpenCL.so', '-DOPENCL_INCLUDE_DIRS=PREFIX/opt/intel/opencl/include', '-Dpython_version=3', '-DUSE_OPENMP=ON', '-DUSE_INDEX_64=OFF', '-DUSE_FFT=OFF', '-DBUILD_examples=OFF', '-DBUILD_tools=OFF', ],
#                                       'nuc7i7bnh' => [ '-DUSE_GREENTEA=ON', '-DUSE_CUDA=OFF', '-DUSE_INTEL_SPATIAL=ON', '-DBUILD_docs=OFF', '-DUSE_ISAAC=ON', '-DViennaCL_INCLUDE_DIR=PREFIX/include', '-DBLAS=Open', '-DOPENCL_LIBRARIES=PREFIX/opt/intel/opencl/libOpenCL.so', '-DOPENCL_INCLUDE_DIRS=PREFIX/opt/intel/opencl/include', '-Dpython_version=3', '-DUSE_OPENMP=ON', '-DUSE_INDEX_64=OFF', '-DUSE_FFT=OFF', '-DBUILD_examples=OFF', '-DBUILD_tools=OFF', ], },
#                    'require'     => [ Installer['isaac'], Installer['boost'], Installer['hdf5'], Installer['leveldb'], Installer['lmdb'], Installer['glog'], Installer['gflags'], Installer['clfft'], Installer['libdnn'], Installer['opencv'], ],
#                    'creates'     => 'lib/libcaffe.so',
#                    'method'      => 'cmake', },
# 'tensorflow'   => {'url'         => 'https://github.com/tensorflow/tensorflow/archive/master.tar.gz',
#                    'prebuild'    => "patch -Np1 -i PREFIX/src/tensorflow.patch &&
#                                      cp PREFIX/src/tensorflow_eigen3.patch PREFIX/src/tensorflow/third_party/eigen3/remove_unsupported_devices.patch &&
#                                      /usr/bin/python3 tensorflow/tools/git/gen_git_source.py --configure .  &&
#                                      echo \"export PYTHON_BIN_PATH=/usr/bin/python3\" > tools/python_bin_path.sh &&
#                                      export BAZELRC=PREFIX/src/tensorflow.bazelrc",
#                    'postbuild'   => "./bazel-bin/tensorflow/tools/pip_package/build_pip_package PREFIX/tmp/tensorflow_pkg &&
#                                      /usr/bin/pip3 install --target PREFIX/lib/python3.5/site-packages PREFIX/tmp/tensorflow_pkg/tensorflow-1.4.0-cp35-cp35m-linux_x86_64.whl &&
#                                      cp PREFIX/lib/python3.5/site-packages/tensorflow/libtensorflow_framework.so PREFIX/lib/ &&
#                                      cp -r PREFIX/lib/python3.5/site-packages/tensorflow/include/tensorflow PREFIX/include/",
#                    'args'        => { 'native'   => [ '-c opt', '--config=sycl', '//tensorflow/tools/pip_package:build_pip_package', '--verbose_failures', ],
#                                       'nuc7i7bnh' => [ '-c opt', '--config=sycl', '//tensorflow/tools/pip_package:build_pip_package', '--verbose_failures', ], },
#                    'require'     => [ Installer['protobuf'], ],
#                    'creates'     => 'lib/libtensorflow_framework.so',
#                    'method'      => 'bazel', },
