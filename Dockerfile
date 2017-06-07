# Dockerfile for transtats
# http://transtats.org/
#
# Run Command: cd /transtats
# docker build -t transtats .
# docker run -d --name container -p 8080:8015 transtats

FROM fedora
MAINTAINER Sachin Pathare <spathare@redhat.com>

# Environment variable 
ENV DATABASE_NAME=transtats \
    DATABASE_USER=postgres \
    DATABASE_PASSWD=postgres \
    DATABASE_HOST=localhost \
    TRANSIFEX_USER=suanand \
    TRANSIFEX_PASSWD=transtats \
    PYTHONUNBUFFERED=1
    
RUN dnf -y update && \
    dnf -y install gcc findutils git python3-pip python3-devel sudo redhat-rpm-config \
    postgresql-server postgresql-contrib postgresql-devel && \
    dnf clean all

RUN su - postgres -c "PGDATA=/var/lib/pgsql/data initdb"

ADD deploy/docker/conf/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf

RUN chown -R 26:26 /var/lib/pgsql/data

RUN mkdir /workspace

WORKDIR /workspace

ADD / /workspace

ADD deploy/docker/conf/sample_keys.json /workspace/transtats/settings/keys.json

RUN pip3 install -r /workspace/requirements/base.txt

ADD deploy/docker/launch.sh /usr/bin/transtats.sh

EXPOSE 8015

CMD ["/usr/bin/transtats.sh"]
