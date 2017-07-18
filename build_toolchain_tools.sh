#!/bin/bash

# Error on failure
set -e

## Set our environment variables
PREFIX="$(pwd)/toolchain"
GENERATE="${PREFIX}/generate"
SOURCE="${GENERATE}/src"
TAR="${GENERATE}/tar"
BUILD="${GENERATE}/build"
BUILD_LOGS="${GENERATE}/build_logs"

ARCH=x86_64
TARGET=amd64-linux-musl

# Set package versions
CMAKE_VER="3.8.2"
CMAKE="cmake-3.8.2"
AUTOCONF_VER="2.69"
AUTOCONF="autoconf-${AUTOCONF_VER}"
AUTOMAKE_VER="1.15.1"
AUTOMAKE="automake-${AUTOMAKE_VER}"
LIBTOOL_VER="2.4.6"
LIBTOOL="libtool-${LIBTOOL_VER}"
M4_VER="1.4.18"
M4_PKG="m4-${M4_VER}"
MAKE_VER="4.2"
MAKE_PKG="make-${MAKE_VER}"
NCURSES_VER="6.0"
NCURSES="ncurses-${NCURSES_VER}"
OPENSSL_VER="1.1.0f"
OPENSSL="openssl-${OPENSSL_VER}"

## Download our source packages
cd "${TAR}"
wget -N "https://ftpmirror.gnu.org/gnu/make/${MAKE_PKG}.tar.gz"
wget -N "https://ftpmirror.gnu.org/gnu/m4/${M4_PKG}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/autoconf/${AUTOCONF}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/automake/${AUTOMAKE}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/libtool/${LIBTOOL}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/ncurses/${NCURSES}.tar.gz"
wget -N "https://www.openssl.org/source/${OPENSSL}.tar.gz"
wget -N "https://cmake.org/files/v3.8/${CMAKE}.tar.gz"

## Extract source packages
echo "Extracting make ..."
if [ ! -d "${SOURCE}/${MAKE_PKG}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${MAKE_PKG}.tar.gz"
fi

echo "Extracting m4 ..."
if [ ! -d "${SOURCE}/${M4_PKG}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${M4_PKG}.tar.xz"
fi

echo "Extracting autoconf ..."
if [ ! -d "${SOURCE}/${AUTOCONF}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${AUTOCONF}.tar.xz"
fi

echo "Extracting automake ..."
if [ ! -d "${SOURCE}/${AUTOMAKE}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${AUTOMAKE}.tar.xz"
fi

echo "Extracting libtool ..."
if [ ! -d "${SOURCE}/${LIBTOOL}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${LIBTOOL}.tar.xz"
fi

echo "Extracting ncurses ..."
if [ ! -d "${SOURCE}/${NCURSES}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${NCURSES}.tar.xz"
fi

echo "Extracting openssl ..."
if [ ! -d "${SOURCE}/${OPENSSL}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${OPENSSL}.tar.gz"
fi

echo "Extracting cmake ..."
if [ ! -d "${SOURCE}/${CMAKE}" ]
then
    cd "${SOURCE}"
    tar xf "${TAR}/${CMAKE}.tar.xz"
fi

## Update our path to use the new compilers
export PATH="${PREFIX}/bin:${PREFIX}/${TARGET}/bin:$PATH"
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export CFLAGS="$CFLAGS -static --sysroot=${PREFIX}"
export CXXFLAGS="$CXXFLAGS -static --sysroot=${PREFIX}"
export FC="$TARGET-gfortran"
export FCFLAGS="$FCFLAGS -static --sysroot=${PREFIX}"
export LDFLAGS="-Wl,--no-export-dynamic -Wl,--no-dynamic-linker -Wl,-static"
export M4="${PREFIX}/bin/m4"

## Build make
if [ ! -e "${BUILD}/phase3_make_complete" ]
then
    export MAKE="${BUILD}/build-make/make"

    echo "Phase 3: Building make ...."
    cd "${BUILD}"
    mkdir -p build-make
    cd build-make
    CROSS_COMPILE=" " "${SOURCE}/${MAKE_PKG}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --without-guile \
        --disable-nls &> "${BUILD_LOGS}/phase3_make_configure.log"
    sh "build.sh" &> "${BUILD_LOGS}/phase3_make_build.log"
    "${BUILD}/build-make/make" install-strip &> "${BUILD_LOGS}/phase3_make_install.log"
    touch "${BUILD}/phase3_make_complete"
else
    echo "Phase 3: make already built, skipping...."
fi

export MAKE="${PREFIX}/bin/make"

## Build m4
if [ ! -e "${BUILD}/phase3_m4_complete" ]
then
    echo "Phase 3: Building m4 ...."
    cd "${BUILD}"
    mkdir -p build-m4
    cd build-m4
    CROSS_COMPILE=" " "${SOURCE}/${M4_PKG}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-threads=posix \
        --enable-c++ \
        --enable-changeword \
        --with-packager="NUbots" \
        --with-packager-version="0.1" \
        --with-syscmd-shell="/bin/bash" &> "${BUILD_LOGS}/phase3_m4_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_m4_make.log"
    "${MAKE}" install-strip &> "${BUILD_LOGS}/phase3_m4_install.log"
    touch "${BUILD}/phase3_m4_complete"
else
    echo "Phase 3: m4 already built, skipping...."
fi

## Build autoconf
if [ ! -e "${BUILD}/phase3_autoconf_complete" ]
then
    echo "Phase 3: Building autoconf ...."
    cd "${BUILD}"
    mkdir -p build-autoconf
    cd build-autoconf
    CROSS_COMPILE=" " "${SOURCE}/${AUTOCONF}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${BUILD_LOGS}/phase3_autoconf_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_autoconf_make.log"
    "${MAKE}" install-strip &> "${BUILD_LOGS}/phase3_autoconf_install.log"
    touch "${BUILD}/phase3_autoconf_complete"
else
    echo "Phase 3: autoconf already built, skipping...."
fi

## Build automake
if [ ! -e "${BUILD}/phase3_automake_complete" ]
then
    echo "Phase 3: Building automake ...."
    cd "${BUILD}"
    mkdir -p build-automake
    cd build-automake
    CROSS_COMPILE=" " "${SOURCE}/${AUTOMAKE}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${BUILD_LOGS}/phase3_automake_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_automake_make.log"
    "${MAKE}" install-strip &> "${BUILD_LOGS}/phase3_automake_install.log"
    touch "${BUILD}/phase3_automake_complete"
else
    echo "Phase 3: automake already built, skipping...."
fi

## Build libtool
if [ ! -e "${BUILD}/phase3_libtool_complete" ]
then
    echo "Phase 3: Building libtool ...."
    cd "${BUILD}"
    mkdir -p build-libtool
    cd build-libtool
    CROSS_COMPILE=" " "${SOURCE}/${LIBTOOL}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-static \
        --with-sysroot="${PREFIX}" &> "${BUILD_LOGS}/phase3_libtool_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_libtool_make.log"
    "${MAKE}" install-strip &> "${BUILD_LOGS}/phase3_libtool_install.log"
    touch "${BUILD}/phase3_libtool_complete"
else
    echo "Phase 3: libtool already built, skipping...."
fi

## Build ncurses
if [ ! -e "${BUILD}/phase3_ncurses_complete" ]
then
    echo "Phase 3: Building ncurses ...."
    cd "${BUILD}"
    mkdir -p build-ncurses
    cd build-ncurses
    CROSS_COMPILE=" " "${SOURCE}/${NCURSES}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-static \
        --with-sysroot="${PREFIX}" \
        --with-build-cc="/usr/bin/gcc" \
        --with-normal \
        --with-debug \
        --with-profile \
        --with-termlib \
        --with-ticlib \
        --with-gpm \
        --enable-sp-funcs \
        --enable-const \
        --enable-ext-colors \
        --enable-ext-mouse \
        --enable-ext-putwin \
        --enable-no-padding \
        --enable-sigwinch \
        --enable-tcap-names &> "${BUILD_LOGS}/phase3_ncurses_configure.log"
    cd progs
    "${MAKE}" sources &> "${BUILD_LOGS}/phase3_ncurses_make_progs.log"
    #"${MAKE}" install &> "${BUILD_LOGS}/phase3_ncurses_install_progs.log"
    cd ..
    "${MAKE}" sources -j$(nproc) &> "${BUILD_LOGS}/phase3_ncurses_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_ncurses_install.log"
    touch "${BUILD}/phase3_ncurses_complete"
else
    echo "Phase 3: ncurses already built, skipping...."
fi

## Build openssl
if [ ! -e "${BUILD}/phase3_openssl_complete" ]
then
    echo "Phase 3: Building openssl ...."
    cd "${BUILD}"
    mkdir -p build-openssl
    cd build-openssl
    CROSS_COMPILE=" " "${SOURCE}/${OPENSSL}/config" \
        --prefix="${PREFIX}" \
        --release \
        no-async \
        no-shared &> "${BUILD_LOGS}/phase3_openssl_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_openssl_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_openssl_install.log"
    touch "${BUILD}/phase3_openssl_complete"
else
    echo "Phase 3: openssl already built, skipping...."
fi

## Build cmake
if [ ! -e "${BUILD}/phase3_cmake_complete" ]
then
    echo "Phase 3: Building cmake ...."
    cd "${BUILD}"
    mkdir -p build-cmake
    cd build-cmake
    CROSS_COMPILE=" " \
    CFLAGS="$CFLAGS -isystem ${PREFIX}/include/ncurses" \
    CXXFLAGS="$CXXFLAGS -isystem ${PREFIX}/include/ncurses" \
    "${SOURCE}/${CMAKE}/bootstrap" \
        --prefix="${PREFIX}" \
        --parallel="$(nproc)" \
        --no-qt-gui &> "${BUILD_LOGS}/phase3_cmake_bootstrap.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_cmake_make.log"
    "${MAKE}" install-strip &> "${BUILD_LOGS}/phase3_cmake_install.log"
    touch "${BUILD}/phase3_cmake_complete"
else
    echo "Phase 3: cmake already built, skipping...."
fi

echo "Phase 3 tools built successfully."
