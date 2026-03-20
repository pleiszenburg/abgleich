SPHINXOPTS := env('SPHINXOPTS', '')
SPHINXBUILD := env('SPHINXBUILD', 'sphinx-build')
SOURCEDIR := 'source'
BUILDDIR := 'build'

clean-docs:
    cd {{ source_directory() }} && if [ -d build ]; then rm -r build; fi

docs-cli:
    python docs/update_cli.py

docs-help:
    cd {{ source_directory() }} && {{SPHINXBUILD}} -M help "{{SOURCEDIR}}" "{{BUILDDIR}}" {{SPHINXOPTS}}

# Sphinx builder by name, e.g. `just build html`.
docs-build TARGET="html": docs-cli
    cd {{ source_directory() }} && {{SPHINXBUILD}} -M {{TARGET}} "{{SOURCEDIR}}" "{{BUILDDIR}}" {{SPHINXOPTS}}
