.DEFAULT_GOAL := help

WORKING_DIR := problem_builder
JS_TARGET := $(WORKING_DIR)/public/js/translations
EXTRACT_DIR := $(WORKING_DIR)/translations/en/LC_MESSAGES
EXTRACTED_DJANGO := $(EXTRACT_DIR)/django-partial.po
EXTRACTED_DJANGOJS := $(EXTRACT_DIR)/djangojs-partial.po
EXTRACTED_TEXT := $(EXTRACT_DIR)/django.po

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

upgrade:
	pip-compile --output-file test_requirements.txt test_requirements.in

extract_translations: ## extract strings to be translated, outputting .po files
	cd $(WORKING_DIR) && i18n_tool extract
	msgcat $(EXTRACTED_DJANGO) $(EXTRACTED_DJANGOJS) -o $(EXTRACTED_TEXT)
	rm $(EXTRACTED_DJANGO)
	rm $(EXTRACTED_DJANGOJS)
	sed -i'' -e 's/nplurals=INTEGER/nplurals=2/' $(EXTRACTED_TEXT)
	sed -i'' -e 's/plural=EXPRESSION/plural=\(n != 1\)/' $(EXTRACTED_TEXT)

compile_translations: ## compile translation files, outputting .mo files for each supported language
	cd $(WORKING_DIR) && i18n_tool generate
	python manage.py compilejsi18n --namespace ProblemBuilderXBlockI18N --output $(JS_TARGET)

detect_changed_source_translations:
	cd $(WORKING_DIR) && i18n_tool changed

dummy_translations: ## generate dummy translation (.po) files
	cd $(WORKING_DIR) && i18n_tool dummy

build_dummy_translations: dummy_translations compile_translations ## generate and compile dummy translation files

validate_translations: build_dummy_translations detect_changed_source_translations ## validate translations

pull_translations: ## pull translations from transifex
	cd $(WORKING_DIR) && i18n_tool transifex pull

push_translations: ## push translations to transifex
	cd $(WORKING_DIR) && i18n_tool transifex push
