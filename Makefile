SHELL = /bin/sh

.PHONY: help deps coveragerc test integrated-test cov html-cov update-html-cov
.PHONY: dist-clean runtime-clean clean install build publish

all: help

# ***************** INSTRUCTIONS *****************
help:
	@echo "help		 				Show this help"
	@echo "deps 					Install development dependencies"
	@echo "coveragerc 				Generate config file for ``coverage``"
	@echo "test				 		Run tests (w/o install dependencies)"
	@echo "integrated-test	 		Run tests (w/ install dependencies)"
	@echo "cov				 		Re-generate coverage report (text-version)"
	@echo "html-cov			 		Re-generate coverage report (HTML-version). Find the report in ``"
	@echo "update-html-cov		 	Re-run tests (w/o install dependencies) and re-generate coverage report (HTML-version)"
	@echo "dist-clean			 	Clean distribution files"
	@echo "runtime-clean		 	Clean .pyc and pycache"
	@echo "clean				 	Run ``dist-clean`` and ``runtime-clean``"
	@echo "install				 	Install package from source code"
	@echo "build				 	Prepare python package for distribution"
	@echo "publish				 	Publish package to PyPI"

# ****************************************************

# ***************** BASIC OPERATIONS *****************
# dependencies
deps:
	pip install --upgrade -r requirements.txt

# test
coveragerc:
	PYTHONPATH=. python3 tests/generate_coverage_config.py
test: coveragerc
	SKIP_JS_TEST=1 python3 -m coverage run
integrated-test: deps test

# coverage
cov:
	python3 -m coverage report
html-cov:
	python3 -m coverage html
update-html-cov: test html-cov

# clean
dist-clean:
	rm -rf *.egg-info/ build/ dist/

runtime-clean:
	find . -name "*__pycache__" | xargs rm -rf
	find . -name "*.pyc" | xargs rm -rf

clean: dist-clean runtime-clean

# Install Dump HLS from source code
install:
	pip install --upgrade pip setuptools
	pip install --upgrade -e .
# ****************************************************

# ***************** PUBLISH OPERATIONS *****************
build: dist-clean runtime-clean
	python3 setup.py check
	python3 setup.py sdist bdist_wheel

publish: build
	# will not override existing version
	python3 -m twine upload -r testpypi -u milliele dist/*
	python3 -m twine upload -u milliele --skip-existing dist/*
# ****************************************************
