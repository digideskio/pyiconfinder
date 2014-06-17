PYTHON_BIN?=python
NOSETESTS_BIN?=nosetests
FLAKE8_BIN?=flake8

all:

test:
	@$(PYTHON_BIN) setup.py test

nose:
	@$(NOSETESTS_BIN)

flake8:
	@$(FLAKE8_BIN) pyiconfinder tests setup.py

publish:
	@$(PYTHON_BIN) setup.py sdist upload

clean:
	@rm -rf build dist *.egg*

.PHONY: test flake8 publish clean
