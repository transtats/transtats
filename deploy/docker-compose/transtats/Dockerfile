# Dockerfile for transtats
# https://hub.docker.com/r/transtats/transtats-sa

FROM registry.fedoraproject.org/fedora:latest
LABEL maintainer="suanand@redhat.com, bhavin7392@gmail.com"

USER root
RUN useradd -ms /bin/bash tsuser
RUN dnf -y update && \
    dnf -y install git make cpio koji file patch intltool libtool gtk3-devel npm supervisor redis && \
    dnf clean all

RUN mkdir /workspace
ENV PYTHONUNBUFFERED 1
WORKDIR /workspace
RUN git clone -b master https://github.com/transtats/transtats.git .
RUN pip3 install -r /workspace/requirements/base.txt
RUN cp deploy/docker-compose/transtats/launch.sh /usr/bin/transtats.sh
RUN cp deploy/docker-compose/transtats/wait-for-it.sh /usr/bin/wait-for-it.sh
RUN cp deploy/docker-compose/transtats/conf/redis.ini /etc/supervisord.d/
RUN cp deploy/docker-compose/transtats/conf/transtats_celery.ini /etc/supervisord.d/
RUN cp deploy/docker-compose/transtats/conf/transtats_celerybeat.ini /etc/supervisord.d/
RUN mkdir staticfiles false run transtats/logs/celery
RUN touch /workspace/transtats/logs/celery/redis.log
RUN touch /workspace/transtats/logs/celery/redis_err.log
RUN touch /workspace/transtats/logs/celery/transtats_worker.log
RUN touch /workspace/transtats/logs/celery/transtats_beat.log
RUN chmod -R g+w transtats/logs transtats/node dashboard/sandbox staticfiles false run
RUN chown -R tsuser /workspace
EXPOSE 8080
USER tsuser
ENTRYPOINT ["/usr/bin/transtats.sh"]
