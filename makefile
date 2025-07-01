ENV ?= test
export ENV

NAMESPACE := dynamicalsystem
PACKAGE_NAME := gazette
DOCKER_IMAGE := ${NAMESPACE}/$(PACKAGE_NAME)
HOST_FOLDER := ${HOME}/.local/share
VERSION := $(shell grep -m 1 version pyproject.toml | grep -e '\d.\d.\d' -o)
TARBALL := ${NAMESPACE}_${VERSION}.tar.gz

.PHONY:
	container, publish, sync, test

all: sync test image

build:
	uv build --wheel --package dynamicalsystem.gazette

check: build
	uvx twine check dist/*

publish: check
	uvx twine upload dist/*

containers: image
	export HOST_FOLDER=${HOST_FOLDER} && \
	export SUBFOLDER=${NAMESPACE} && \
	export ENV=${ENV} && \
	echo $$HOST_FOLDER $$ENV && \
	docker compose -f docker-compose.yml up -d

	export HOST_FOLDER=${HOST_FOLDER} && \
	export SUBFOLDER=${NAMESPACE} && \
	export ENV=${ENV} && \
	echo $$HOST_FOLDER $$ENV && \
	docker compose -f docker-compose.yml create gazette

image: publish
	docker build . \
		--tag $(DOCKER_IMAGE) \
		--build-arg NAMESPACE=${NAMESPACE} \
		--build-arg SCRIPT=${PACKAGE_NAME}

test:
	pytest --pyargs dynamicalsystem.pytests
