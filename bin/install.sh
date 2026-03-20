#!/usr/bin/env bash

set -eu

# Check pipefail support in a subshell, ignore if unsupported
# shellcheck disable=SC3040
(set -o pipefail 2> /dev/null) && set -o pipefail

help() {
  cat <<'EOF'
Install a binary release of abgleich hosted on GitHub

USAGE:
    install.sh [options]

FLAGS:
    -h, --help      Display this message
    -f, --force     Force overwriting an existing binary

OPTIONS:
    --tag TAG       Tag (version) of the crate to install, defaults to latest release
    --to LOCATION   Where to install the binary [default: ~/bin]
    --target TARGET
EOF
}

crate=abgleich
url=https://github.com/pleiszenburg/abgleich
releases=$url/releases

say() {
  echo "install: $*" >&2
}

err() {
  if [ -n "${td-}" ]; then
    rm -rf "$td"
  fi

  say "error: $*"
  exit 1
}

need() {
  if ! command -v "$1" > /dev/null 2>&1; then
    err "need $1 (command not found)"
  fi
}

download() {
  url="$1"
  output="$2"

  args=()
  if [ -n "${GITHUB_TOKEN+x}" ]; then
    args+=(--header "Authorization: Bearer $GITHUB_TOKEN")
  fi

  if command -v curl > /dev/null; then
    curl --proto =https --tlsv1.2 -sSfL ${args[@]+"${args[@]}"} "$url" -o"$output"
  else
    wget --https-only --secure-protocol=TLSv1_2 --quiet ${args[@]+"${args[@]}"} "$url" -O"$output"
  fi
}

force=false
while test $# -gt 0; do
  case $1 in
    --force | -f)
      force=true
      ;;
    --help | -h)
      help
      exit 0
      ;;
    --tag)
      tag=$2
      shift
      ;;
    --target)
      target=$2
      shift
      ;;
    --to)
      dest=$2
      shift
      ;;
    *)
      say "error: unrecognized argument '$1'. Usage:"
      help
      exit 1
      ;;
  esac
  shift
done

command -v curl > /dev/null 2>&1 ||
  command -v wget > /dev/null 2>&1 ||
  err "need wget or curl (command not found)"

need mkdir
need mktemp
need tar

if [ -z "${tag-}" ]; then
  need grep
  need cut
fi

if [ -z "${target-}" ]; then
  need cut
fi

if [ -z "${dest-}" ]; then
  dest="$HOME/bin"
fi

if [ -z "${tag-}" ]; then
  tag=$(
    download https://api.github.com/repos/pleiszenburg/abgleich/releases/latest - |
    grep tag_name |
    cut -d'"' -f4
  )
fi

if [ -z "${target-}" ]; then
  kernel=$(uname -s | cut -d- -f1)
  uname_target="$(uname -m)-$kernel"

  case $uname_target in
    x86_64-Linux)  target=x86_64-unknown-linux-musl;;
    amd64-FreeBSD) target=x86_64-unknown-freebsd;;
    *)
      # shellcheck disable=SC2016
      err 'Could not determine target from output of `uname -m`-`uname -s`, please use `--target`:' "$uname_target"
    ;;
  esac
fi

archive="$releases/download/$tag/$crate-$tag-$target.tar.gz"

say "Repository:  $url"
say "Crate:       $crate"
say "Tag:         $tag"
say "Target:      $target"
say "Destination: $dest"
say "Archive:     $archive"

td=$(mktemp -d || mktemp -d -t tmp)

download "$archive" - | tar -C "$td" -xz

if [ -e "$dest/abgleich" ] && [ "$force" = false ]; then
  err "\`$dest/abgleich\` already exists"
else
  mkdir -p "$dest"
  cp "$td/abgleich" "$dest/abgleich"
  chmod 755 "$dest/abgleich"
fi

rm -rf "$td"
