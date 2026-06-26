NAMESPACE := dynamicalsystem
PACKAGE_NAME := gazette
DOCKER_IMAGE := $(NAMESPACE)/$(PACKAGE_NAME)
ENGINE ?= podman

.PHONY: all build check publish image test

all: test image

# Build the runnable image from local source. No PyPI round-trip.
image:
	$(ENGINE) build . --tag $(DOCKER_IMAGE)

test:
	uv run pytest --pyargs dynamicalsystem.pytests

# --- PyPI release (optional, NOT part of the image/deploy path) ---

build:
	uv build --wheel --package dynamicalsystem.gazette

check: build
	uvx twine check dist/*

publish: check
	uvx twine upload dist/*
