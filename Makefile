

install:
	pip3 install --user -e . --no-deps

test:
	python3 -m unittest -v --failfast builddriver/tests/tests.py

lint:
	pylint3 --disable=too-many-instance-attributes builddriver/builddriver.py

setup:
	python3 setup.py sdist
	python3 setup.py bdist_wheel --universal

upload: setup
	twine upload dist/*

bootstrap:
	python3 -m pip install --user --upgrade setuptools wheel twine

really-clean:
	git clean -fdx
