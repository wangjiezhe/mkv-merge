#!/usr/bin/env sh
set -e

CGO_CFLAGS="$(pkg-config --cflags libass libpng16) -DHB_EXPERIMENTAL_API"
CGO_LDFLAGS="-lass -lfreetype -lm -lz -lfontconfig -lpng -lfribidi -lharfbuzz -lharfbuzz-subset -lexpat"

DEBUG=true
if $DEBUG; then
  CGO_CFLAGS="${CGO_CFLAGS} -Og"
  DEBUG_CFLAGS=-gcflags="all=-N -l"
else
  CGO_CFLAGS="${CGO_CFLAGS} -Os"
  LDFLAGS="-s -w"
fi

export CGO_CFLAGS CGO_LDFLAGS

ROOT_PATH="$(dirname "$(readlink -f "$0")")/.."

cd "${ROOT_PATH}/third-party/MkvAutoSubset" || exit 1
git apply "${ROOT_PATH}/scripts/mkvlib.patch"

cd mkvlib/sdk || exit 1
mkdir -p "${ROOT_PATH}/mkv_merge/mkvlib"

go mod tidy
go build -ldflags "${LDFLAGS}" -buildmode c-shared "${DEBUG_CFLAGS}" -o "${ROOT_PATH}/mkv_merge/mkvlib/mkvlib.so" &&
  rm "${ROOT_PATH}/mkv_merge/mkvlib/mkvlib.h" &&
  chmod +x "${ROOT_PATH}/mkv_merge/mkvlib/mkvlib.so"

git apply -R "${ROOT_PATH}/scripts/mkvlib.patch"
