
black:
	black .

clean:
	-rm -r build/*
	-rm -r dist/*
	find src/ -name '*.pyc' -exec sudo rm -f {} +
	find src/ -name '*.pyo' -exec sudo rm -f {} +
	find src/ -name '*~' -exec rm -f {} +
	find src/ -name '__pycache__' -exec sudo rm -fr {} +
	find src/ -name '*.htm' -exec rm -f {} +
	find src/ -name '*.html' -exec rm -f {} +
	find src/ -name '*.so' -exec rm -f {} +
	find src/ -name 'octave-workspace' -exec rm -f {} +

docs:
	@(cd docs; make clean; make html)

release:
	make clean
	flit build
	gpg --detach-sign -a dist/abgleich*.whl
	gpg --detach-sign -a dist/abgleich*.tar.gz

install:
	pip install -v -e .[dev,gui]

upload:
	for filename in $$(ls dist/*.tar.gz dist/*.whl) ; do \
		twine upload $$filename $$filename.asc ; \
	done

.PHONY: docs
