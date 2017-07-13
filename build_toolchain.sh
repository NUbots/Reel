#!/bin/bash

# Taking inspiration from
# https://jstrapko.github.io/musl-gcc/
# http://wiki.osdev.org/GCC_Cross-Compiler
# http://preshing.com/20141119/how-to-build-a-gcc-cross-compiler/

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

## We can't exactly build over the tools we are using to build with
## so create a new folder to build to
export BOOTSTRAP_PREFIX="${SOURCE}/bootstrap_tools"

## Make our directories
mkdir -p "${PREFIX}"
mkdir -p "${BOOTSTRAP_PREFIX}"
mkdir -p "${SOURCE}"
mkdir -p "${TAR}"
mkdir -p "${BUILD}"
mkdir -p "${BUILD_LOGS}"

## Add a symlink so usr ends up in the same folder
cd "${PREFIX}"
ln -nfs . usr
cd "${BOOTSTRAP_PREFIX}"
ln -nfs . usr

# Set package versions
MUSL_VER="1.1.16"
MUSL="musl-${MUSL_VER}"
BINUTILS_VER="2.28"
BINUTILS="binutils-${BINUTILS_VER}"
GCC_VER="7.1.0"
GCC="gcc-${GCC_VER}"

## Download our source packages
cd "${TAR}"
wget -N "https://www.musl-libc.org/releases/${MUSL}.tar.gz"
wget -N "https://ftpmirror.gnu.org/gnu/gcc/${GCC}/${GCC}.tar.bz2"
wget -N "https://ftpmirror.gnu.org/gnu/binutils/${BINUTILS}.tar.bz2"

## Extract source packages
if [ ! -d "${BUILD}/${GCC}" ]
then
    cd "${BUILD}"
    echo "Extracting gcc ..."
    tar xf "${TAR}/${GCC}.tar.bz2"

    # Get gcc to download its extras
    cd "${BUILD}/${GCC}"
    ./contrib/download_prerequisites
else
    echo "gcc already extracted, skipping ..."
fi

if [ ! -d "${BUILD}/${BINUTILS}" ]
then
    cd "${BUILD}"
    echo "Extracting binutils ..."
    tar xf "${TAR}/${BINUTILS}.tar.bz2"
else
    echo "binutils already extracted, skipping ..."
fi

if [ ! -d "${BUILD}/${MUSL}" ]
then
    cd "${BUILD}"
    echo "Extracting musl ..."
    tar xf "${TAR}/${MUSL}.tar.gz"
else
    echo "musl already extracted, skipping ..."
fi

#### BOOTSTRAP MUSL BASED GCC COMPILER ####

## Build bootstrap musl
if [ ! -e "${BUILD}/phase1_musl_complete" ]
then
    echo "Phase 1: Building musl ...."
    cd "${BUILD}"
    mkdir -p build-musl-bootstrap
    cd build-musl-bootstrap
    CROSS_COMPILE=" " "../${MUSL}/configure" \
        --prefix="${BOOTSTRAP_PREFIX}" \
        --target="${ARCH}" \
        --disable-shared &> "${BUILD_LOGS}/phase1_musl_configure.log"
    make -j$(nproc) &> "${BUILD_LOGS}/phase1_musl_make.log"
    make install &> "${BUILD_LOGS}/phase1_musl_install.log"
    touch "${BUILD}/phase1_musl_complete"
else
    echo "Phase 1: musl already built, skipping...."
fi

## Build bootstrap binutils
if [ ! -e "${BUILD}/phase1_binutils_complete" ]
then
    echo "Phase 1: Building binutils ...."
    cd "${BUILD}"
    mkdir -p build-binutils-bootstrap
    cd build-binutils-bootstrap
    "../${BINUTILS}/configure" \
        --prefix="${BOOTSTRAP_PREFIX}" \
        --target="${TARGET}" \
        --with-sysroot \
        --disable-nls \
        --disable-bootstrap \
        --disable-werror &> "${BUILD_LOGS}/phase1_binutils_configure.log"
    make -j$(nproc) &> "${BUILD_LOGS}/phase1_binutils_make.log"
    make install &> "${BUILD_LOGS}/phase1_binutils_install.log"
    touch "${BUILD}/phase1_binutils_complete"
else
    echo "Phase 1: binutils already built, skipping...."
fi

## Build bootstrap gcc
## For bootstrapping we only need c and c++
if [ ! -e "${BUILD}/phase1_gcc_complete" ]
then
    echo "Phase 1: Building gcc ...."
    cd "${BUILD}"
    mkdir -p build-gcc-bootstrap
    cd build-gcc-bootstrap
    "../${GCC}/configure" \
        --prefix="${BOOTSTRAP_PREFIX}" \
        --target="${TARGET}" \
        --enable-languages=c,c++ \
        --with-sysroot="${BOOTSTRAP_PREFIX}" \
        --disable-nls \
        --disable-multilib \
        --disable-bootstrap \
        --disable-werror \
        --disable-shared &> "${BUILD_LOGS}/phase1_gcc_configure.log"
    make -j$(nproc) all-gcc &> "${BUILD_LOGS}/phase1_gcc_make_gccc.log"
    make -j$(nproc) all-target-libgcc &> "${BUILD_LOGS}/phase1_gcc_make_libgcc.log"
    make -j$(nproc) all-target-libstdc++-v3 &> "${BUILD_LOGS}/phase1_gcc_make_stdc++.log"
    make install-gcc &> "${BUILD_LOGS}/phase1_gcc_install_gcc.log"
    make install-target-libgcc &> "${BUILD_LOGS}/phase1_gcc_install_libgcc.log"
    make install-target-libstdc++-v3 &> "${BUILD_LOGS}/phase1_gcc_install_stdc++.log"
    touch "${BUILD}/phase1_gcc_complete"
else
    echo "Phase 1: gcc already built, skipping...."
fi

#### BUILD MUSL BASED GCC COMPILER ####

## Update our path to use the new compilers
export PATH="$BOOTSTRAP_PREFIX/bin:$PATH"
export CC="$TARGET-gcc"
export CXX="$TARGET-g++"
export CFLAGS="$CFLAGS -static --sysroot=$BOOTSTRAP_PREFIX"
export CXXFLAGS="$CXXFLAGS -static --sysroot=$BOOTSTRAP_PREFIX"

## Build final musl
if [ ! -e "${BUILD}/phase2_musl_complete" ]
then
    echo "Phase 2: Building musl ...."
    cd "${BUILD}"
    mkdir -p build-musl
    cd build-musl
    CROSS_COMPILE="$TARGET-" "../${MUSL}/configure" \
        --prefix="${PREFIX}" \
        --target="${ARCH}" \
        --syslibdir="${PREFIX}/lib" \
        --disable-shared &> "${BUILD_LOGS}/phase2_musl_configure.log"
    make -j$(nproc) &> "${BUILD_LOGS}/phase2_musl_make.log"
    make install &> "${BUILD_LOGS}/phase2_musl_install.log"
    touch "${BUILD}/phase2_musl_complete"
else
    echo "Phase 2: musl already built, skipping...."
fi

## Build final binutils
if [ ! -e "${BUILD}/phase2_binutils_complete" ]
then
    echo "Phase 2: Building binutils ...."
    cd "${BUILD}"
    mkdir -p build-binutils
    cd build-binutils
    "../${BINUTILS}/configure" \
        --prefix="${PREFIX}" \
        --target="${TARGET}" \
        --with-sysroot \
        --disable-nls \
        --disable-bootstrap \
        --disable-werror &> "${BUILD_LOGS}/phase2_binutils_configure.log"
    make -j$(nproc) &> "${BUILD_LOGS}/phase2_binutils_make.log"
    make install &> "${BUILD_LOGS}/phase2_binutils_install.log"
    touch "${BUILD}/phase2_binutils_complete"
else
    echo "Phase 2: binutils already built, skipping...."
fi

## Build final gcc
## This time we build c, c++ and fortran
if [ ! -e "${BUILD}/phase2_gcc_complete" ]
then
    echo "Phase 2: Building gcc ...."
    cd "${BUILD}"
    mkdir -p build-gcc
    cd build-gcc
    "../${GCC}/configure" \
        --prefix="${PREFIX}" \
        --target="${TARGET}" \
        --enable-languages=c,c++,fortran \
        --enable-gold \
        --enable-bfd \
        --with-sysroot="${PREFIX}" \
        --disable-nls \
        --disable-multilib \
        --disable-bootstrap \
        --disable-werror \
        --disable-shared &> "${BUILD_LOGS}/phase2_gcc_configure.log"
    make -j$(nproc) all-gcc &> "${BUILD_LOGS}/phase2_gcc_make_gcc.log"
    make -j$(nproc) all-target-libgcc &> "${BUILD_LOGS}/phase2_gcc_make_libgcc.log"
    make -j$(nproc) all-target-libstdc++-v3 &> "${BUILD_LOGS}/phase2_gcc_make_stdc++.log"
    make install-gcc &> "${BUILD_LOGS}/phase2_gcc_install_gcc.log"
    make install-target-libgcc &> "${BUILD_LOGS}/phase2_gcc_install_libgcc.log"
    make install-target-libstdc++-v3 &> "${BUILD_LOGS}/phase2_gcc_install_stdc++.log"
    touch "${BUILD}/phase2_gcc_complete"
else
    echo "Phase 2: gcc already built, skipping...."
fi
