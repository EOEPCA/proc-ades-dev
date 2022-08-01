FROM ubuntu:focal-20220113


# to build:
# docker build --rm -t ades:latest .
# to run:
# docker run --rm -ti -p 80:80  ades:latest

# procadesdev:latest
ENV DEBIAN_FRONTEND noninteractive

########################################
### DEV TOOLS 

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
RUN conda create -n ades-dev python=3.8 workflow-executor=1.0.23 jinja2 cookiecutter=1.7.2 boto3 -y -c conda-forge -c eoepca -c anaconda 


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

########################################
# ZOO_Prerequisites

RUN apt-get update && apt-get install -y software-properties-common git wget vim \
    && rm -rf /var/lib/apt/lists/* \
    && add-apt-repository ppa:ubuntugis/ubuntugis-unstable \
    && apt-get update 
RUN apt-get install -y flex bison libfcgi-dev libxml2 libxml2-dev curl libssl-dev autoconf apache2 subversion libmozjs185-dev python3-dev python3-setuptools build-essential libxslt1-dev uuid-dev libjson-c-dev libmapserver-dev
RUN add-apt-repository ppa:ubuntugis/ppa && apt-get update -y
RUN apt-get -y install libgdal-dev
# if you remove --with-db-backend from the configure command, uncomment the following line
#RUN ln -s /usr/lib/x86_64-linux-gnu/libfcgi.a /usr/lib/
RUN apt-get update
RUN apt install -y apache2 libapache2-mod-fcgid wget \
                && a2enmod actions fcgid alias proxy_fcgi \
                && /etc/init.d/apache2 restart

########################################
# ZOO_KERNEL
RUN cd /opt && git clone https://github.com/terradue/ZOO-Project.git -b feature/deploy-undeploy-ogcapi-route
WORKDIR /opt/ZOO-Project
RUN make -C ./thirds/cgic206 libcgic.a
RUN cd ./zoo-project/zoo-kernel \
     && autoconf \
     && ./configure --with-python=/usr/miniconda3/envs/ades-dev --with-pyvers=3.8 --with-js=/usr --with-mapserver=/usr --with-ms-version=7 --with-json=/usr  --prefix=/usr \
     && sed -i "s/-DACCEPT_USE_OF_DEPRECATED_PROJ_API_H/-DPROJ_VERSION_MAJOR=8/g" ./ZOOMakefile.opts \
     && make -j4\
     && make install \
     && cp main.cfg /usr/lib/cgi-bin \
     && cp zoo_loader.cgi /usr/lib/cgi-bin \
     && cp oas.cfg /usr/lib/cgi-bin \
     && sed -i "s%http://www.zoo-project.org/zoo/%http://127.0.0.1%g" /usr/lib/cgi-bin/main.cfg \
     && sed -i "s%../tmpPathRelativeToServerAdress/%http://localhost/temp/%g" /usr/lib/cgi-bin/main.cfg \
     && echo '\n[env]\nPYTHONPATH=/usr/miniconda3/envs/ades-dev/lib/python3.8/site-packages'\
          >> /usr/lib/cgi-bin/main.cfg \
     && a2enmod cgi rewrite \
     && sed "s:AllowOverride None:AllowOverride All:g" -i /etc/apache2/apache2.conf

RUN cp ./docker/.htaccess /var/www/html/.htaccess \
     && ln -s /tmp/ /var/www/html/temp 

COPY assets/default.conf /etc/apache2/sites-available/000-default.conf

# Remove apt lists
RUN rm -rf /var/lib/apt/lists/*
RUN chmod -R 777 /usr/lib/cgi-bin


RUN mkdir /tmp/cookiecutter-templates && \
    chmod -R 777 /tmp/cookiecutter-templates


EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
