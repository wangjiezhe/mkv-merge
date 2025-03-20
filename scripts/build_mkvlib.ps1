# 保存当前目录
$originalLocation = Get-Location

# 切换到脚本所在目录
Set-Location -Path $PSScriptRoot

$env:BUILD_PATH = "$PSScriptRoot\..\mkv_merge\mkvlib"

# 设置 VCPKG_ROOT 环境变量
if (-not $env:VCPKG_ROOT) {
  $env:VCPKG_ROOT = "$env:USERPROFILE\vcpkg"
}

# 如果 VCPKG_ROOT 目录不存在，则克隆 vcpkg 仓库并初始化
if (-not (Test-Path -Path $env:VCPKG_ROOT)) {
  git clone https://github.com/microsoft/vcpkg $env:VCPKG_ROOT
  & "$env:VCPKG_ROOT\bootstrap-vcpkg.bat" -disableMetrics
}

# 设置 vcpkg 的默认 triplet 和构建类型
# $env:VCPKG_DEFAULT_TRIPLET = "x64-mingw-static"
$env:VCPKG_DEFAULT_HOST_TRIPLET = "x64-mingw-static"
$env:VCPKG_BUILD_TYPE = "Release"

# 使用 vcpkg 安装所需的库
& "$env:VCPKG_ROOT\vcpkg" install fribidi "freetype[core, zlib, png]" "harfbuzz[core, experimental-api]"
& "$env:VCPKG_ROOT\vcpkg" install libass

# 设置路径变量
$env:PATH_ROOT = "$env:VCPKG_ROOT\installed\$env:VCPKG_DEFAULT_HOST_TRIPLET"
$env:H_PATH = "$env:PATH_ROOT\include"
$env:L_PATH = "$env:PATH_ROOT\lib"
$env:CGO_CFLAGS = "-I$env:H_PATH -DHB_EXPERIMENTAL_API -Os"
$env:CGO_LDFLAGS = "-L$env:L_PATH -lharfbuzz-subset -lass -lpng -lfreetype -lharfbuzz -lfribidi -lzlib -lgdi32"

# 设置 LDFLAGS
$env:LDFLAGS = "-s -w"

Set-Location -Path "$PSScriptRoot\..\third-party\MkvAutoSubset"
git apply "$PSScriptRoot\mkvlib.patch"

# 构建 mkvlib.so
Set-Location -Path "mkvlib\sdk"
go mod tidy
go build -o "$env:BUILD_PATH\mkvlib.so" -ldflags="$env:LDFLAGS" -buildmode c-shared
Remove-Item -Path "$env:BUILD_PATH\mkvlib.h" -ErrorAction SilentlyContinue

git apply -R "$PSScriptRoot\mkvlib.patch"

Set-Location -Path $originalLocation
