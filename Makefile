PYTHON ?= python3
ER ?= (a|b)*abb
CADENA ?= aabb
.PHONY: config build run clean test
config:
	$(PYTHON) --version
	@echo 'Solo se requiere Python 3.9+ y make. Sin dependencias externas.'
build:
	$(PYTHON) -m compileall -q src
	chmod +x er-afd
run: build
	@./er-afd '$(ER)' '$(CADENA)'; status=$$?; if [ $$status -eq 1 ]; then exit 0; else exit $$status; fi
test:
	$(PYTHON) -m unittest discover -s tests -v
clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
