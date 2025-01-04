# syntax=docker/dockerfile:1
FROM python:3.12-alpine

# pass in the following build arguments from the makefile
ARG SUBFOLDER
ARG SCRIPT

# Install the package
RUN python -m pip install uv
RUN mkdir -p /dist
RUN --mount=source=dist,target=/dist uv pip install --no-cache /dist/*.whl --system

# Create the image's folder(s)
RUN echo "Subfolder: ${SUBFOLDER}"
RUN mkdir -p /${SUBFOLDER}/config
RUN mkdir -p /${SUBFOLDER}/data

# Set image's environment variables
RUN echo "   Script: ${SCRIPT}"
ENV SCRIPT=${SCRIPT}

# Run the module on launch
CMD ["sh", "-c", "${SCRIPT}"]
