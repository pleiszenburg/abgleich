
clean:
	-rm -r build/*
	find src/ -name '*.pyc' -exec rm -f {} +
	find src/ -name '*.pyo' -exec rm -f {} +
	find src/ -name '*~' -exec rm -f {} +
	find src/ -name '__pycache__' -exec rm -fr {} +
	find src/ -name '*.htm' -exec rm -f {} +
	find src/ -name '*.html' -exec rm -f {} +
	find src/ -name '*.so' -exec rm -f {} +
	find src/ -name 'octave-workspace' -exec rm -f {} +
	-rm -r dist/*
	-rm -r src/*.egg-info

release:
	make clean
	# python setup.py sdist bdist_wheel
	python setup.py sdist
	# gpg --detach-sign -a dist/abgleich*.whl
	gpg --detach-sign -a dist/abgleich*.tar.gz

install:
	pip install -v -e .
