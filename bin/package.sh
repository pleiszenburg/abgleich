#!/usr/bin/env bash

set -euxo pipefail

TARGET=$1
VERSION=$(python -c "from tomllib import loads; f = open('abgleich-lib/Cargo.toml'); print(loads(f.read())['package']['version'])")

DIST=$(pwd)/dist
EXECUTABLE=target/$TARGET/release/abgleich
ARCHIVE=abgleich-$VERSION-$TARGET.tar.gz
SRC_FILES="$EXECUTABLE LICENSE README.md"
TGT_FILES="abgleich LICENSE README.md"
PLATFORM=$(echo $TARGET | cut -d "-" -f 3)

echo "Packaging abgleich $VERSION for $TARGET..."

echo "Cleanup ..."
just clean-build

echo "Building abgleich..."
just release $TARGET

echo "Validation test run ..."
ABGLEICH_TEST_RELEASE=1 ABGLEICH_TEST_TARGET=$TARGET just test $PLATFORM

echo "Copying release files..."
mkdir -p $DIST
cp -r $SRC_FILES $DIST

cd $DIST

echo "Creating release archive..."
if [ -f $ARCHIVE ]; then
    rm $ARCHIVE
fi
tar czf $ARCHIVE $TGT_FILES
rm $TGT_FILES

cd ..
