#!/bin/bash

# Error on failure
set -e

## Set our environment variables
PREFIX="$(pwd)/toolchain"
SOURCE="${PREFIX}/src"
TAR="${SOURCE}/tar"
BUILD="${SOURCE}/build"

ARCH=x86_64
TARGET=amd64-linux-musl

# Set package versions
M4_VER="1.4.18"
M4="m4-${M4_VER}"
AUTOCONF_VER="2.69"
AUTOCONF="autoconf-${AUTOCONF_VER}"
AUTOMAKE_VER="1.15.1"
AUTOMAKE="automake-${AUTOMAKE_VER}"
LIBTOOL_VER="2.4.6"
LIBTOOL="libtool-${LIBTOOL_VER}"
MAKE_VER="4.2"
MAKE_PKG="make-${MAKE_VER}"

## Download our source packages
cd "${TAR}"
wget -N "http://ftp.jaist.ac.jp/pub/GNU/make/${MAKE_PKG}.tar.gz"
wget -N "https://ftp.gnu.org/gnu/m4/${M4}.tar.xz"
wget -N "https://ftp.gnu.org/gnu/autoconf/${AUTOCONF}.tar.xz"
wget -N "https://ftp.gnu.org/gnu/automake/${AUTOMAKE}.tar.xz"
wget -N "https://ftp.gnu.org/gnu/libtool/${LIBTOOL}.tar.xz"

## Extract source packages
cd "${BUILD}"
echo "Extracting make ..."
if [ ! -d "${BUILD}/${MAKE_PKG}" ]
then
    tar xf "${TAR}/${MAKE_PKG}.tar.gz"
fi

cd "${BUILD}"
echo "Extracting m4 ..."
if [ ! -d "${BUILD}/${M4}" ]
then
    tar xf "${TAR}/${M4}.tar.xz"
fi

cd "${BUILD}"
echo "Extracting autoconf ..."
if [ ! -d "${BUILD}/${AUTOCONF}" ]
then
    tar xf "${TAR}/${AUTOCONF}.tar.xz"
fi

cd "${BUILD}"
echo "Extracting automake ..."
if [ ! -d "${BUILD}/${AUTOMAKE}" ]
then
    tar xf "${TAR}/${AUTOMAKE}.tar.xz"
fi

cd "${BUILD}"
echo "Extracting libtool ..."
if [ ! -d "${BUILD}/${LIBTOOL}" ]
then
    tar xf "${TAR}/${LIBTOOL}.tar.xz"
fi

## Update our path to use the new compilers
export PATH="${PREFIX}/bin:${PREFIX}/${TARGET}/bin:$PATH"
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export CFLAGS="$CFLAGS -static --sysroot=${PREFIX}"
export CXXFLAGS="$CXXFLAGS -static --sysroot=${PREFIX}"
export FC="$TARGET-gfortran"
export FCFLAGS="$FCFLAGS -static --sysroot=${PREFIX}"
export M4="${PREFIX}/bin/m4"
export MAKE="${PREFIX}/bin/make"

## Build make
if [ ! -e "${PREFIX}/phase3_make_complete" ]
then
    echo "Phase 3: Building make ...."
    cd "${BUILD}"
    mkdir -p build-make
    cd build-make
    CROSS_COMPILE=" " "../${MAKE_PKG}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --disable-nls &> "${PREFIX}/phase3_make_configure.log"
    sh "build.sh" &> "${PREFIX}/phase3_make_build.log"
    ./make install &> "${PREFIX}/phase3_make_install.log"
    touch "${PREFIX}/phase3_make_complete"
else
    echo "Phase 3: make already built, skipping...."
fi

## Build m4
if [ ! -e "${PREFIX}/phase3_m4_complete" ]
then
    echo "Phase 3: Building m4 ...."
    cd "${BUILD}"
    mkdir -p build-m4
    cd build-m4
    CROSS_COMPILE=" " "../${M4}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-threads=posix \
        --enable-c++ \
        --enable-changeword \
        --with-packager="NUbots" \
        --with-packager-version="0.1" \
        --with-syscmd-shell="/bin/bash" &> "${PREFIX}/phase3_m4_configure.log"
    "${MAKE}" -j$(nproc) &> "${PREFIX}/phase3_m4_make.log"
    "${MAKE}" install &> "${PREFIX}/phase3_m4_install.log"
    touch "${PREFIX}/phase3_m4_complete"
else
    echo "Phase 3: m4 already built, skipping...."
fi

## Build autoconf
if [ ! -e "${PREFIX}/phase3_autoconf_complete" ]
then
    echo "Phase 3: Building autoconf ...."
    cd "${BUILD}"
    mkdir -p build-autoconf
    cd build-autoconf
    CROSS_COMPILE=" " "../${AUTOCONF}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${PREFIX}/phase3_autoconf_configure.log"
    "${MAKE}" -j$(nproc) &> "${PREFIX}/phase3_autoconf_make.log"
    "${MAKE}" install &> "${PREFIX}/phase3_autoconf_install.log"
    touch "${PREFIX}/phase3_autoconf_complete"
else
    echo "Phase 3: autoconf already built, skipping...."
fi

## Build automake
if [ ! -e "${PREFIX}/phase3_automake_complete" ]
then
    echo "Phase 3: Building automake ...."
    cd "${BUILD}"
    mkdir -p build-automake
    cd build-automake
    CROSS_COMPILE=" " "../${AUTOMAKE}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${PREFIX}/phase3_automake_configure.log"
    "${MAKE}" -j$(nproc) &> "${PREFIX}/phase3_automake_make.log"
    "${MAKE}" install &> "${PREFIX}/phase3_automake_install.log"
    touch "${PREFIX}/phase3_automake_complete"
else
    echo "Phase 3: automake already built, skipping...."
fi

## Build libtool
if [ ! -e "${PREFIX}/phase3_libtool_complete" ]
then
    echo "Phase 3: Building libtool ...."
    cd "${BUILD}"
    mkdir -p build-libtool
    cd build-libtool
    CROSS_COMPILE=" " "../${LIBTOOL}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-static \
        --with-sysroot="${PREFIX}" &> "${PREFIX}/phase3_libtool_configure.log"
    "${MAKE}" -j$(nproc) &> "${PREFIX}/phase3_libtool_make.log"
    "${MAKE}" install &> "${PREFIX}/phase3_libtool_install.log"
    touch "${PREFIX}/phase3_libtool_complete"
else
    echo "Phase 3: libtool already built, skipping...."
fi
