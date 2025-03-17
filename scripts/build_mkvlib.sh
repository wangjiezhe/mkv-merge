#!/usr/bin/env sh
set -e

CGO_CFLAGS="$(pkg-config --cflags libass libpng16) -DHB_EXPERIMENTAL_API -Os"
CGO_LDFLAGS="-lass -lfreetype -lm -lz -lfontconfig -lpng -lfribidi -lharfbuzz -lharfbuzz-subset -lexpat"
export CGO_CFLAGS CGO_LDFLAGS

LDFLAGS="-s -w"

ROOT_PATH="$(dirname "$(readlink -f "$0")")/.."

cd "${ROOT_PATH}/third-party/MkvAutoSubset/mkvlib/sdk" || exit 1
mkdir -p "${ROOT_PATH}/mkv_merge/mkvlib"

go mod tidy
go build -ldflags "${LDFLAGS}" -buildmode c-shared -o "${ROOT_PATH}/mkv_merge/mkvlib/mkvlib.so" && rm "${ROOT_PATH}/mkv_merge/mkvlib/mkvlib.h"
