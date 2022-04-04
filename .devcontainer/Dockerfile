
FROM ubuntu:focal-20220113


# procadesdev:latest

ENV DEBIAN_FRONTEND noninteractive

# Various cli tools
RUN apt-get update && \
    apt-get install -y wget mlocate tree

# C++ and CMAKE
RUN apt-get -y install gcc mono-mcs cmake && \
    apt install -y build-essential libcgicc-dev gdb

# Miniconda
RUN apt-get update
RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh \
    && bash Miniconda3-py39_4.10.3-Linux-x86_64.sh -b -p /usr/miniconda3 \
    && rm -f Miniconda3-py39_4.10.3-Linux-x86_64.sh  

ENV PATH="/usr/miniconda3/bin:${PATH}"
ARG PATH="/usr/miniconda3/bin:${PATH}"
RUN conda --version
RUN conda create -n ades-dev python=3.8 python=3.8 workflow-executor=1.0.23 jinja2 cookiecutter=1.7.2 boto3 coverage -y -c conda-forge -c eoepca -c anaconda


ENV LD_LIBRARY_PATH="/usr/miniconda3/envs/ades-dev/lib:$LD_LIBRARY_PATH"


# Install Docker CE CLI
RUN apt-get update \
    && apt-get install -y apt-transport-https ca-certificates curl gnupg2 lsb-release \
    && curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | apt-key add - 2>/dev/null \
    && echo "deb [arch=amd64] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli

# Install Docker Compose
RUN LATEST_COMPOSE_VERSION=$(curl -sSL "https://api.github.com/repos/docker/compose/releases/latest" | grep -o -P '(?<="tag_name": ").+(?=")') \
    && curl -sSL "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose