import 'docs/top-level.just'
import 'tests/vagrant/top-level.just'

default:
    @just --list

fmt:
    cargo fmt

clippy:
    cargo clippy -- -D clippy::pedantic -D clippy::nursery -A clippy::missing_errors_doc -A clippy::module_inception

clean-build:
    cargo clean

clean-dist:
    rm -r dist

dist:
    #!/usr/bin/env bash
    for target in "x86_64-unknown-linux-gnu" "x86_64-unknown-linux-musl" "x86_64-unknown-freebsd"; do
       ./bin/package.sh $target
    done

build target=("x86_64-unknown-linux-gnu" / "x86_64-unknown-linux-musl" / "x86_64-unknown-freebsd"):
    cross build --target {{target}}

release target=("x86_64-unknown-linux-gnu" / "x86_64-unknown-linux-musl" / "x86_64-unknown-freebsd"): clean-build
    #!/usr/bin/env bash
    RUSTFLAGS="--deny warnings $RUSTFLAGS" cross build --release --target {{target}}
    [[ "{{target}}" == *linux* ]] &&  upx --best --lzma target/{{target}}/release/abgleich || true

test-internal:
    cargo test

test-features:
    cargo hack check --feature-powerset --no-dev-deps  # https://github.com/taiki-e/cargo-hack?tab=readme-ov-file#--feature-powerset
