#!/bin/bash

# Error on failure
set -e

## Set our environment variables
PREFIX="$(pwd)/toolchain"
SOURCE="${PREFIX}/src"
TAR="${SOURCE}/tar"
BUILD="${SOURCE}/build"
BUILD_LOGS="${BUILD}/logs"

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
wget -N "https://ftpmirror.gnu.org/gnu/make/${MAKE_PKG}.tar.gz"
wget -N "https://ftpmirror.gnu.org/gnu/m4/${M4}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/autoconf/${AUTOCONF}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/automake/${AUTOMAKE}.tar.xz"
wget -N "https://ftpmirror.gnu.org/gnu/libtool/${LIBTOOL}.tar.xz"

## Extract source packages
echo "Extracting make ..."
if [ ! -d "${BUILD}/${MAKE_PKG}" ]
then
    cd "${BUILD}"
    tar xf "${TAR}/${MAKE_PKG}.tar.gz"
fi

echo "Extracting m4 ..."
if [ ! -d "${BUILD}/${M4}" ]
then
    cd "${BUILD}"
    tar xf "${TAR}/${M4}.tar.xz"
fi

echo "Extracting autoconf ..."
if [ ! -d "${BUILD}/${AUTOCONF}" ]
then
    cd "${BUILD}"
    tar xf "${TAR}/${AUTOCONF}.tar.xz"
fi

echo "Extracting automake ..."
if [ ! -d "${BUILD}/${AUTOMAKE}" ]
then
    cd "${BUILD}"
    tar xf "${TAR}/${AUTOMAKE}.tar.xz"
fi

echo "Extracting libtool ..."
if [ ! -d "${BUILD}/${LIBTOOL}" ]
then
    cd "${BUILD}"
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
if [ ! -e "${BUILD}/phase3_make_complete" ]
then
    echo "Phase 3: Building make ...."
    cd "${BUILD}"
    mkdir -p build-make
    cd build-make
    CROSS_COMPILE=" " "../${MAKE_PKG}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --disable-nls &> "${BUILD_LOGS}/phase3_make_configure.log"
    sh "build.sh" &> "${BUILD_LOGS}/phase3_make_build.log"
    ./make install &> "${BUILD_LOGS}/phase3_make_install.log"
    touch "${BUILD}/phase3_make_complete"
else
    echo "Phase 3: make already built, skipping...."
fi

## Build m4
if [ ! -e "${BUILD}/phase3_m4_complete" ]
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
        --with-syscmd-shell="/bin/bash" &> "${BUILD_LOGS}/phase3_m4_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_m4_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_m4_install.log"
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
    CROSS_COMPILE=" " "../${AUTOCONF}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${BUILD_LOGS}/phase3_autoconf_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_autoconf_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_autoconf_install.log"
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
    CROSS_COMPILE=" " "../${AUTOMAKE}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" &> "${BUILD_LOGS}/phase3_automake_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_automake_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_automake_install.log"
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
    CROSS_COMPILE=" " "../${LIBTOOL}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --host="${ARCH}" \
        --enable-static \
        --with-sysroot="${PREFIX}" &> "${BUILD_LOGS}/phase3_libtool_configure.log"
    "${MAKE}" -j$(nproc) &> "${BUILD_LOGS}/phase3_libtool_make.log"
    "${MAKE}" install &> "${BUILD_LOGS}/phase3_libtool_install.log"
    touch "${BUILD}/phase3_libtool_complete"
else
    echo "Phase 3: libtool already built, skipping...."
fi
