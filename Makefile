.DEFAULT_GOAL := help

WORKING_DIR := problem_builder
JS_TARGET := $(WORKING_DIR)/public/js/translations
EXTRACT_DIR := $(WORKING_DIR)/translations/en/LC_MESSAGES

FIREFOX_VERSION := "110.0.1"
GECKODRIVER_VERSION := "0.32.2"

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## remove generated byte code, coverage reports, and build artifacts
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

extract_translations: ## extract strings to be translated, outputting .po files
	cd $(WORKING_DIR) && i18n_tool extract
	cd $(EXTRACT_DIR) && \
		msgcat underscore.po djangojs-partial.po -o textjs.po && \
		cat django-partial.po > text.po && \
		sed -i'' -e 's/nplurals=INTEGER/nplurals=2/' -- text.po textjs.po && \
		sed -i'' -e 's/plural=EXPRESSION/plural=\(n != 1\)/' -- text.po textjs.po && \
		rm -fv django*.*o underscore.*o

compile_translations: ## compile translation files, outputting .mo files for each supported language
	cd $(WORKING_DIR) && i18n_tool generate
	python manage.py compilejsi18n --namespace ProblemBuilderXBlockI18N --output $(JS_TARGET)

detect_changed_source_translations: ## Detect changes in source code that affect translations
	cd $(WORKING_DIR) && i18n_tool changed

dummy_translations: ## generate dummy translation (.po) files
	cd $(WORKING_DIR) && i18n_tool dummy

build_dummy_translations: dummy_translations compile_translations ## generate and compile dummy translation files

validate_translations: build_dummy_translations detect_changed_source_translations ## validate translations

pull_translations: ## pull translations from transifex
	cd $(WORKING_DIR) && i18n_tool transifex pull

push_translations: ## push translations to transifex
	cd $(WORKING_DIR) && i18n_tool transifex push

isort: ## run isort on python source files
	isort -rc problem_builder

test.quality: selfcheck ## run quality checkers on the codebase
	tox -e quality

test.unit: ## run all unit tests
	tox -- $(TEST)

test.integration: ## run all integration tests
	tox -e integration42 -- $(TEST)

test: test.unit test.integration test.quality ## Run all tests

install_firefox:
	@mkdir -p external
	@test -f ./external/firefox/firefox && echo "Firefox already installed." || \
	(cd external && \
	wget -N "https://archive.mozilla.org/pub/firefox/releases/$(FIREFOX_VERSION)/linux-x86_64/en-US/firefox-$(FIREFOX_VERSION).tar.bz2" && \
	tar -xjf firefox-$(FIREFOX_VERSION).tar.bz2 && \
	wget -N https://github.com/mozilla/geckodriver/releases/download/v$(GECKODRIVER_VERSION)/geckodriver-v$(GECKODRIVER_VERSION)-linux64.tar.gz && \
	tar xzf geckodriver-v$(GECKODRIVER_VERSION)-linux64.tar.gz)

selfcheck: ## Check that the Makefile is well-formed
	@echo "The Makefile is well-formed."

piptools: ## install pinned version of pip-compile and pip-sync
	pip install -r requirements/pip.txt
	pip install -r requirements/pip-tools.txt

requirements: piptools  ## install test requirements locally
	pip-sync requirements/ci.txt

requirements_python: piptools  ## install all requirements locally
	pip-sync requirements/dev.txt requirements/private.*

# Define PIP_COMPILE_OPTS=-v to get more information during make upgrade.
PIP_COMPILE = pip-compile --upgrade $(PIP_COMPILE_OPTS)

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	$(PIP_COMPILE) --allow-unsafe -o requirements/pip.txt requirements/pip.in
	$(PIP_COMPILE) -o requirements/pip-tools.txt requirements/pip-tools.in
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	$(PIP_COMPILE) -o requirements/base.txt requirements/base.in
	$(PIP_COMPILE) -o requirements/test.txt requirements/test.in
	$(PIP_COMPILE) -o requirements/workbench.txt requirements/workbench.in
	$(PIP_COMPILE) -o requirements/quality.txt requirements/quality.in
	$(PIP_COMPILE) -o requirements/ci.txt requirements/ci.in
	$(PIP_COMPILE) -o requirements/dev.txt requirements/dev.in
	# Let tox control the Django version for tests & integration
	sed -i '/^[dD]jango==/d' requirements/test.txt
	sed -i '/^[dD]jango==/d' requirements/workbench.txt
