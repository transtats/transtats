# Dockerfile for transtats
# https://hub.docker.com/r/transtats/transtats-sa

FROM registry.fedoraproject.org/f26/python3:latest 
LABEL maintainer="suanand@redhat.com, bhavin7392@gmail.com"

USER root
RUN dnf -y update && \
    dnf -y install koji && \
    dnf clean all

ENV PYTHONUNBUFFERED 1
RUN mkdir /workspace
WORKDIR /workspace
RUN git clone -b devel https://github.com/transtats/transtats.git .
RUN cp deploy/docker-compose/transtats/sample_keys.json transtats/settings/keys.json
RUN pip3 install -r /workspace/requirements/base.txt
ADD launch.sh /usr/bin/transtats.sh
ADD wait-for-it.sh /usr/bin/wait-for-it.sh
ADD datadump.json /workspace/data.json
EXPOSE 8080
ENTRYPOINT ["/usr/bin/transtats.sh"]
