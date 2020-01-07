

install:
	pip3 install --user -e . --no-deps

test:
	python3 -m unittest -v --failfast schecker/tests/tests.py

lint:
	pylint3 --disable=too-many-instance-attributes schecker/schecker.py

setup:
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal

upload: setup
	twine upload dist/*

bootstrap:
	python3 -m pip install --user --upgrade setuptools wheel twine

clean:
	rm -rf schecker.egg-info build dist

really-clean:
	git clean -fdx
