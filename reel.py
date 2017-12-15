#!/usr/bin/env python3

import os

from reel.patch import UpdateConfigSub
from reel import Shell
from reel import Reel

r = Reel()  #gnu_mirror='http://gnu.uberglobalmirror.com')

r.add_library(
    url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
    name='protobuf',
    configure_args={
        '--with-zlib': True,
        '--enable-static': True,
        '--enable-shared': True
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
        configure_args={'--enable-static': True,
                        '--enable-shared': True},
        install_targets=['install-strip']
    )

    t.add_library(
        Shell(pre_build='mkdir -p {}'.format('{prefix_dir}', 'temp')),
        Shell(
            post_build='find {dest} \( -name .install -o -name ..install.cmd \) -delete && cp -r {} {} && rm -rf {dest}'.
            format(
                os.path.join('{prefix_dir}', 'temp', 'include', '*'),
                os.path.join('{prefix_dir}', 'include'),
                dest=os.path.join('{prefix_dir}', 'temp', 'include')
            )
        ),
        name='linux-headers',
        url='https://git.kernel.org/torvalds/t/linux-4.15-rc3.tar.gz',
        build_args=[
            # Linux kernel doesn't know what aarch64, it knows arm64 though.
            'ARCH={}'.format(t.arch if t.arch != 'aarch64' else 'arm64'),
            'INSTALL_HDR_PATH={}'.format(os.path.join('{prefix_dir}', 'temp'))
        ],
        build_targets=['mrproper', 'headers_check', 'headers_install'],
        install_targets=[]
    )

    t.add_library(
        name='util-linux',
        url='https://www.kernel.org/pub/linux/utils/util-linux/v2.31/util-linux-2.31.tar.xz',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--disable-all-programs': True,
            '--enable-libblkid': True,
            '--enable-libmount': True,
            '--without-python': True
        }
    )

    t.add_library(
        name='zlib',
        url='http://www.zlib.net/zlib-1.2.11.tar.gz',
        configure_args={
            '--host': None,  # zlib configure doesn't understand host
            '--build': None,  # zlib configure doesn't understand build
            '--static': True,
            '--shared': True
        }
    )

    t.add_library(
        name='bzip2',
        url='https://github.com/Bidski/bzip2/archive/v1.0.6.1.tar.gz',
    )

    t.add_library(
        url='https://github.com/google/protobuf/releases/download/v3.5.0/protobuf-cpp-3.5.0.tar.gz',
        name='protobuf',
        env={'CC_FOR_BUILD': t.parent_toolchain.env['CC'],
             'CXX_FOR_BUILD': t.parent_toolchain.env['CXX']},
        configure_args={
            '--with-zlib': True,
            '--with-protoc': os.path.join('{parent_prefix_dir}', 'bin', 'protoc'),
            '--enable-static': True,
            '--enable-shared': True,
        }
    )

    t.add_library(
        url='https://github.com/libexpat/libexpat/releases/download/R_2_2_5/expat-2.2.5.tar.bz2',
        name='expat',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--without-docbook': True
        }
    )

    t.add_library(
        url='https://github.com/libffi/libffi/archive/v3.2.1.tar.gz',
        name='ffi',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        url='https://downloads.sourceforge.net/project/libpng/libpng16/1.6.34/libpng-1.6.34.tar.xz',
        name='png',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        Shell(
            post_extract='cd {source}'
            ' && sed -ri "s:.*(AUX_MODULES.*valid):\\1:" modules.cfg '
            ' && sed -ri "s:.*(#.*SUBPIXEL_RENDERING) .*:\\1:" include/freetype/config/ftoption.h'
        ),
        url='https://downloads.sourceforge.net/freetype/freetype-2.8.1.tar.bz2',
        name='freetype',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--with-harfbuzz': 'no',
            '--with-zlib': 'yes',
            '--with-bzip2': 'yes',
            '--with-png': 'yes'
        }
    )

    t.add_library(
        name='gperf',
        url='https://ftpmirror.gnu.org/gnu/gperf/gperf-3.1.tar.gz',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        Shell(post_extract='cd {source} && rm -f src/fcobjshash.h'),
        url='https://www.freedesktop.org/software/fontconfig/release/fontconfig-2.12.6.tar.bz2',
        name='fontconfig',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--disable-docs': True
        }
    )

    t.add_library(
        url='https://www.x.org/pub/individual/util/util-macros-1.19.1.tar.bz2',
        name='util-macros',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        Shell(
            post_extract='cd {source}'
            ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/xcb-proto-1.12-schema-1.patch -O - | patch -Np1'
            ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/xcb-proto-1.12-python3-1.patch -O - | patch -Np1'
        ),
        url='https://xcb.freedesktop.org/dist/xcb-proto-1.12.tar.bz2',
        name='xcb-proto',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    # yapf: disable
    xorg_protos = [
        ('bigreqsproto', '1.1.2'),
        ('compositeproto', '0.4.2'),
        ('damageproto', '1.2.1'),
        ('dmxproto', '2.3.1'),
        ('dri2proto', '2.8'),
        ('dri3proto', '1.0'),
        ('fixesproto', '5.0'),
        ('fontsproto', '2.1.3'),
        ('glproto', '1.4.17'),
        ('inputproto', '2.3.2'),
        ('kbproto', '1.0.7'),
        ('presentproto', '1.1'),
        ('randrproto', '1.5.0'),
        ('recordproto', '1.14.2'),
        ('renderproto', '0.11.1'),
        ('resourceproto', '1.2.0'),
        ('scrnsaverproto', '1.2.2'),
        ('videoproto', '2.3.3'),
        ('xcmiscproto', '1.2.2'),
        ('xextproto', '7.3.0'),
        ('xf86bigfontproto', '1.2.0'),
        ('xf86dgaproto', '2.1'),
        ('xf86driproto', '2.1.1'),
        ('xf86vidmodeproto', '2.3.1'),
        ('xineramaproto', '1.2.1'),
        ('xproto', '7.0.31')
    ]
    # yapf: enable

    for proto in xorg_protos:
        t.add_library(
            UpdateConfigSub,
            url='https://www.x.org/pub/individual/proto/{}-{}.tar.bz2'.format(*proto),
            name='xorg-protocol-header-{}'.format(proto[0]),
            configure_args={
                '--enable-static': True,
                '--enable-shared': True
            }
        )

    t.add_library(
        url='https://www.x.org/pub/individual/lib/libXdmcp-1.1.2.tar.bz2',
        name='Xdmcp',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        url='https://www.x.org/pub/individual/lib/libXau-1.0.8.tar.bz2',
        name='Xau',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True
        }
    )

    t.add_library(
        Shell(
            post_extract='cd {source}'
            # Fixes incompatibilities between python2 and python3 (whitespace inconsistencies)
            # https://bugs.freedesktop.org/show_bug.cgi?id=95490
            ' && wget http://www.linuxfromscratch.org/patches/blfs/svn/libxcb-1.12-python3-1.patch -O - | patch -Np1'
            # pthread-stubs is useless on linux
            ' && sed -i "s/pthread-stubs//" configure'
        ),
        url='https://xcb.freedesktop.org/dist/libxcb-1.12.tar.bz2',
        name='xcb',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--enable-xinput': True,
            '--without-doxygen': True
        }
    )

    # yapf: disable
    xorg_libs = [
        ('xtrans', '1.3.5'),
        ('libX11', '1.6.5'),
        ('libXext', '1.3.3'),
        ('libFS', '1.0.7'),
        ('libICE', '1.0.9'),
        ('libSM', '1.2.2'),
        ('libXScrnSaver', '1.2.2'),
        ('libXt', '1.1.5'),
        ('libXmu', '1.1.2'),
        ('libXpm', '3.5.12'),
        ('libXaw', '1.0.13'),
        ('libXfixes', '5.0.3'),
        ('libXcomposite', '0.4.4'),
        ('libXrender', '0.9.10'),
        ('libXcursor', '1.1.14'),
        ('libXdamage', '1.1.4'),
        ('libfontenc', '1.1.3'),
        ('libXfont2', '2.0.2'),
        ('libXft', '2.3.2'),
        ('libXi', '1.7.9'),
        ('libXinerama', '1.1.3'),
        ('libXrandr', '1.5.1'),
        ('libXres', '1.2.0'),
        ('libXtst', '1.2.3'),
        ('libXv', '1.0.11'),
        ('libXvMC', '1.0.10'),
        ('libXxf86dga', '1.1.4'),
        ('libXxf86vm', '1.1.4'),
        ('libdmx', '1.1.3'),
        ('libpciaccess', '0.14'),
        ('libxkbfile', '1.0.9'),
        ('libxshmfence', '1.2')
    ]
    # yapf: enable

    for lib in xorg_libs:
        t.add_library(
            UpdateConfigSub,
            url='https://www.x.org/pub/individual/lib/{}-{}.tar.bz2'.format(*lib),
            name='xorg-lib-{}'.format(lib[0]),
            configure_args={
                '--enable-static': True,
                '--enable-shared': True,
                # musl returns a valid pointer for a 0 byte allocation
                '--enable-malloc0returnsnull': 'no'
            }
        )

    t.add_library(
        url='https://prdownloads.sourceforge.net/tcl/tcl8.6.7-src.tar.gz',
        name='tcl',
        src_dir='unix',
        # Apparently configure gets confused when we are cross compiling
        # https://groups.google.com/forum/#!topic/comp.lang.tcl/P56Gge5_3Z8
        env={'ac_cv_func_strtod': 'yes',
             'tcl_cv_strtod_buggy': '1'},
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--enable-threads': True
        }
    )

    t.add_library(
        #Shell(post_instal='')
        url='https://prdownloads.sourceforge.net/tcl/tk8.6.7-src.tar.gz',
        name='tk',
        src_dir='unix',
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--with-tcl': os.path.join('..', 'tcl8.6.7-src'),
            '--enable-64bit' if t.arch == 'x86_64' else '--disable-64bit': True,
            '--x-includes': os.path.join('{prefix_dir}', 'include'),
            '--x-libraries': os.path.join('{prefix_dir}', 'lib')
        },
        install_targets=['install', 'install-private-headers']
    )

    t.add_library(
        UpdateConfigSub,
        url='http://www.bytereef.org/software/mpdecimal/releases/mpdecimal-2.4.2.tar.gz',
        name='mpdec',
        in_source_build=True,
        configure_args={'--enable-static': True,
                        '--enable-shared': True},
        build_targets=['default']
    )

    t.add_library(
        name='ncurses',
        url='https://ftpmirror.gnu.org/gnu/ncurses/ncurses-6.0.tar.gz',
        env={'CPPFLAGS': '-P'},
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
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
        Shell(
            configure='base_dir=$(pwd)'
            ' && mkdir -p {builds_dir}/$(basename {source})'
            ' && cd {builds_dir}/$(basename {source})'
            ' && $base_dir/{source}/config'
            '    --prefix={prefix_dir} '
            '    --libdir=lib'
            '    --release no-async'
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

    t.add_library(
        url='https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tar.xz',
        name='python',
        # Configure cant run all tests.
        env={
            'ac_cv_file__dev_ptmx': 'no',
            'ac_cv_file__dev_ptc': 'no',
            # Configure needs some help finding the curses headers.
            'CPPFLAGS': '-I{prefix_dir}/include/ncurses',
            'CFLAGS': '-I{prefix_dir}/include/ncurses',
            'CXXFLAGS': '-I{prefix_dir}/include/ncurses'
        },
        configure_args={
            '--enable-static': True,
            '--enable-shared': True,
            '--enable-ipv6': True,
            '--with-system-ffi': True,
            '--with-system-expat': True,
            '--with-system-libmpdec': True,
            '--with-threads': True
        }
    )

r.build()

# pkg-config

# autopoint
# gettext
# libpcre
# libmount

# ffi
# glib2

# linux-headers-generic
# nasm
# python3
# protobuf

# zlib
# python3
# libasound2
# libusb
# protobuf
# zlib
# bzip2
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
