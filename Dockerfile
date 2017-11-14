# Dockerfile for transtats
# http://transtats.org/
#
# Run Command: cd transtats
# Build Image: docker build -t transtats/transtats .
# Run Container with env variable: docker run -d --name container -p 8080:8014 -e DATABASE_NAME=transtats -e \
#                                  DATABASE_USER=postgres -e DATABASE_PASSWD=postgres -e DATABASE_HOST=localhost transtats/transtats

FROM registry.fedoraproject.org/fedora:latest
LABEL maintainer="spathare@redhat.com,suanand@redhat.com"

# Environment variable 
ENV DATABASE_NAME=transtats \
    DATABASE_USER=postgres \
    DATABASE_PASSWD=postgres \
    DATABASE_HOST=localhost \
    PYTHONUNBUFFERED=1
    
RUN echo 'root:root' | chpasswd

RUN dnf -y update && \
    dnf -y install gcc cpio koji findutils git python python3-pip python3-devel redhat-rpm-config \
    sudo postgresql-server postgresql-contrib postgresql-devel openssh-server openssl-devel && \
    dnf clean all

RUN /usr/bin/ssh-keygen -A

RUN su - postgres -c "PGDATA=/var/lib/pgsql/data initdb"

ADD deploy/docker/conf/pg_hba.conf /var/lib/pgsql/data/pg_hba.conf

RUN chown -R 26:26 /var/lib/pgsql/data

RUN mkdir /workspace

WORKDIR /workspace

ADD / /workspace

ADD deploy/docker/conf/sample_keys.json /workspace/transtats/settings/keys.json

RUN pip3 install -r /workspace/requirements/dev.txt

RUN mkdir /var/run/sshd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

EXPOSE 22 8014 8015

CMD ["/usr/sbin/sshd", "-D"]
