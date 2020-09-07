help:
	@echo "Usage:"
	@echo "    make help             prints this help."
	@echo "    make deploy           deploy the project."
	@echo "    make fix              fix formatting and import sort ordering."
	@echo "    make format-js        run the JavaScript format checker (prettier)."
	@echo "    make format-py        run the Python format checker (black)."
	@echo "    make lint-js          run the JavaScript linter (eslint)."
	@echo "    make lint-py          run the Python linter (flake8)."
	@echo "    make run              run the dev server."
	@echo "    make setup            set up/update the local dev env."
	@echo "    make sort             run the sort checker (isort)."
	@echo "    make test-js          run the JavaScript test suite."
	@echo "    make test-py          run the Python test suite."
	@echo "    make test             run all test suites."

.PHONY: deploy
deploy:
	fab deploy

.PHONY: fix
fix:
	black .
	isort .

.PHONY: format-js
format-js:
	npx prettier . --check || exit 1

.PHONY: format-py
format-py:
	@echo "Running black" && \
		black --check . \
		|| exit 1

.PHONY: lint-js
lint-js:
	npx eslint static/src/js/builder.jsx static/src/js/hierarchy.js

.PHONY: lint-py
lint-py:
	@echo "Running flake8" && \
		flake8 \
		|| exit 1

.PHONY: run
run:
	python manage.py runserver

.PHONY: setup
setup:
	pip install -r requirements.txt
	pre-commit install

.PHONY: sort
sort:
	@echo "Running Isort" && \
		isort --check-only --diff . \
		|| exit 1

.PHONY: test-js
test-js:
	npm run test

.PHONY: test-py
test-py:
	pytest \
		--cov=builder \
		--cov=codelists \
		--cov=coding_systems \
		--cov=mappings \
		--cov=opencodelists

.PHONY: test
test: test-js test-py
