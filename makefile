ENV ?= test
export ENV

NAMESPACE := dynamicalsystem
PACKAGE_NAME := gazette
DOCKER_IMAGE := ${NAMESPACE}/$(PACKAGE_NAME)
HOST_FOLDER := ${HOME}/.local/share
SUBFOLDER := ${NAMESPACE}
VERSION := $(shell grep -m 1 version pyproject.toml | grep -e '\d.\d.\d' -o)
TARBALL := ${NAMESPACE}_${VERSION}.tar.gz

.PHONY:
	docker_container, sync, test

all: sync test build docker_image

build:
	uv build gazette

check: build
	uvx twine check gazette/dist/*

publish: check
	uvx twine upload gazette/dist/*

docker_container:
	export HOST_FOLDER=${HOST_FOLDER} && \
	export SUBFOLDER=${SUBFOLDER} && \
	export ENV=${ENV} && \
	echo $$HOST_FOLDER $$ENV && \
	docker compose -f docker-compose.yml up -d

	export HOST_FOLDER=${HOST_FOLDER} && \
	export SUBFOLDER=${SUBFOLDER} && \
	export ENV=${ENV} && \
	echo $$HOST_FOLDER $$ENV && \
	docker compose -f docker-compose.yml create poohsticks

docker_image:
	docker build . \
		--tag $(DOCKER_IMAGE) \
		--build-arg SUBFOLDER=${SUBFOLDER} \
		--build-arg SCRIPT=${PACKAGE_NAME}

# Create and push a tarball for production
production:
	@echo ${TARBALL}
	tar czvf prod/$(TARBALL) makefile dist dockerfile docker-compose.yml
	mkdir -p "/Volumes/Dynamical System’s Public Folder/Drop Box/${NAMESPACE}.${VERSION}"
	cp prod/$(TARBALL) "/Volumes/Dynamical System’s Public Folder/Drop Box/${NAMESPACE}.${VERSION}"
	@echo 'tar -xzf ${TARBALL}' on the prod server to extract the tarball
	@echo 'make docker_image'
	@echo 'make docker_container ENV=prod'


test:
	pytest --pyargs dynamicalsystem.pytests
