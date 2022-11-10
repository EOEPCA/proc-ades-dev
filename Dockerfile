FROM ubuntu:focal-20220113


# to build:
# docker build --rm -t ades:latest .
# to run:
# docker run --rm -ti -p 80:80  ades:latest

# procadesdev:latest
ENV DEBIAN_FRONTEND noninteractive

########################################
### DEV TOOLS 
RUN apt-get update -qqy --no-install-recommends \
# Various cli tools
 && apt-get install -qqy --no-install-recommends  \
    wget \
    mlocate tree \
    # C++ and CMAKE
    gcc \
    mono-mcs \
    cmake \
    build-essential  \
    libcgicc-dev  \
    gdb \
    gettext

ARG PY_VER=3.8
# Miniconda
RUN wget -nv --no-check-certificate \
    https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh \
    && bash Miniconda3-py39_4.10.3-Linux-x86_64.sh -b -p /usr/miniconda3 \
    && rm -f Miniconda3-py39_4.10.3-Linux-x86_64.sh  
ENV PATH="/usr/miniconda3/envs/ades-dev/bin:/usr/miniconda3/bin:${PATH}"
COPY assets/ades-dev_env.yaml /tmp/ades-dev_env.yaml
RUN conda install mamba -n base -c conda-forge && \
    mamba env create --file /tmp/ades-dev_env.yaml &&\
    rm /tmp/ades-dev_env.yaml

########################################
# ZOO_Prerequisites

RUN apt-get update -qqy --no-install-recommends && apt-get install -qqy --no-install-recommends  software-properties-common \
&& add-apt-repository ppa:ubuntugis/ubuntugis-unstable \
&& add-apt-repository ppa:ubuntugis/ppa \
&& apt-get update -qqy  --no-install-recommends  \
&& apt-get install -qqy  --no-install-recommends \
    git \
    wget \
    vim  \
    flex \
    bison \
    libfcgi-dev \
    libxml2 \
    libxml2-dev \
    curl \
    libssl-dev \
    autoconf \
    apache2 \
    libmozjs185-dev \
    python3-dev \
    python3-setuptools \
    build-essential \
    libxslt1-dev \
    uuid-dev \
    libjson-c-dev \
    libmapserver-dev \
    libgdal-dev \
    librabbitmq4 \
    librabbitmq-dev \
    apache2 \
    libapache2-mod-fcgid \
    libtinyxml-dev \
    libfftw3-dev \
    r-base-dev \
&& a2enmod actions fcgid alias proxy_fcgi \
&& /etc/init.d/apache2 restart \
&& rm -rf /var/lib/apt/lists/* 

########################################
# ZOO_KERNEL
ARG ZOO_PRJ_GIT_BRANCH='feature/deploy-undeploy-ogcapi-route'
RUN cd /opt && git clone https://github.com/terradue/ZOO-Project.git -b $ZOO_PRJ_GIT_BRANCH

WORKDIR /opt/ZOO-Project
RUN make -C ./thirds/cgic206 libcgic.a
RUN cd ./zoo-project/zoo-kernel \
     && autoconf \
#     && ./configure --with-rabbitmq=yes --with-python=/usr/miniconda3/envs/ades-dev --with-pyvers=$PY_VER --with-js=/usr --with-mapserver=/usr --with-ms-version=7 --with-json=/usr  --prefix=/usr --with-db-backend --with-metadb=yes\
     && ./configure --with-rabbitmq=yes --with-python=/usr/miniconda3/envs/ades-dev --with-pyvers=$PY_VER --with-js=/usr --with-mapserver=/usr --with-ms-version=7 --with-json=/usr  --prefix=/usr --with-db-backend \
     && echo "ZOOMakefile.opts content:" \
     && cat ZOOMakefile.opts \
     && sed -i "s/-DACCEPT_USE_OF_DEPRECATED_PROJ_API_H/-DPROJ_VERSION_MAJOR=8/g" ./ZOOMakefile.opts \
     && make -j4\
     && make install \
     && cp zoo_loader_fpm /usr/lib/cgi-bin \
     && cp main.cfg /usr/lib/cgi-bin \
     && cp zoo_loader.cgi /usr/lib/cgi-bin \
     && cp oas.cfg /usr/lib/cgi-bin \
     && sed -i "s%http://www.zoo-project.org/zoo/%http://127.0.0.1%g" /usr/lib/cgi-bin/main.cfg \
     && sed -i "s%../tmpPathRelativeToServerAdress/%http://localhost/temp/%g" /usr/lib/cgi-bin/main.cfg \
     && echo "\n[env]\nPYTHONPATH=/usr/miniconda3/envs/ades-dev/lib/python${PY_VER}/site-packages"\
          >> /usr/lib/cgi-bin/main.cfg \
     && a2enmod cgi rewrite \
     && sed "s:AllowOverride None:AllowOverride All:g" -i /etc/apache2/apache2.conf && \
     cd /opt/ZOO-Project && \
     cp ./docker/.htaccess /var/www/html/.htaccess && \
     ln -s /tmp/ /var/www/html/temp && \
     cd .. && rm -rf ZOO-Project

COPY assets/default.conf /etc/apache2/sites-available/000-default.conf

RUN chmod -R 777 /usr/lib/cgi-bin

RUN mkdir /tmp/cookiecutter-templates && \
    chmod -R 777 /tmp/cookiecutter-templates

COPY ./docker/startUp.sh /
RUN chmod 755 /startUp.sh

EXPOSE 80
CMD ["apachectl", "-D", "FOREGROUND"]
