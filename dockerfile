# syntax=docker/dockerfile:1
FROM python:3.13-alpine

# pass in the following build arguments from the makefile
ARG NAMESPACE
ARG SCRIPT

# Install the package
RUN python -m pip install --no-cache-dir --upgrade ${NAMESPACE}.${SCRIPT}

# Create the image's folder(s)
RUN echo "Subfolder: ${NAMESPACE}"
RUN mkdir -p /${NAMESPACE}/config
RUN mkdir -p /${NAMESPACE}/data

# Set image's environment variables
RUN echo "   Script: ${SCRIPT}"
ENV SCRIPT=${SCRIPT}

# Run the module on launch
CMD ["sh", "-c", "${SCRIPT}"]
