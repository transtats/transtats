# Dockerfile for transtats
# https://hub.docker.com/r/transtats/transtats/
#
# Run Command: docker run -d --name container_name -p 8080:8015 transtats/transtats

FROM registry.fedoraproject.org/fedora:latest
LABEL maintainer="suanand@redhat.com"

RUN dnf -y update && \
    dnf -y install gcc make cpio koji findutils git python python3-pip python3-devel redhat-rpm-config \
    sudo postgresql-server postgresql-contrib postgresql-devel openssh-server openssl-devel patch && \
    dnf clean all

RUN su - postgres -c "PGDATA=/var/lib/pgsql/data initdb"
ADD conf/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf
RUN chown -R 26:26 /var/lib/pgsql/data

ENV PYTHONUNBUFFERED 1
RUN mkdir /workspace
WORKDIR /workspace
RUN git clone -b master https://github.com/transtats/transtats.git .
ADD conf/sample_keys.json /workspace/transtats/settings/keys.json
RUN pip3 install -r /workspace/requirements/base.txt
ADD launch.sh /usr/bin/transtats.sh

EXPOSE 8015

CMD ["/usr/bin/transtats.sh"]
