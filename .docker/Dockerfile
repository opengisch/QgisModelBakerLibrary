ARG QGIS_TEST_VERSION=latest
FROM  qgis/qgis:${QGIS_TEST_VERSION}

RUN apt-get update && \
    apt-get -y install openjdk-8-jre \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# MSSQL: client side
RUN apt-get install -y curl locales postgresql-client
RUN apt-get install -y unixodbc unixodbc-dev odbcinst unixodbc-common libodbcinst2 libodbccr2 libodbc2 libqt5sql5-odbc

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | tee /etc/apt/sources.list.d/msprod.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools

COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Avoid sqlcmd termination due to locale -- see https://github.com/Microsoft/mssql-docker/issues/163
RUN echo "nb_NO.UTF-8 UTF-8" > /etc/locale.gen
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen
ENV PATH="/usr/local/bin:${PATH}"

ENV LANG=C.UTF-8

WORKDIR /
