# syntax=docker/dockerfile:1

FROM ubuntu:23.10
WORKDIR /root
RUN apt-get update -yq && apt-get install -yq build-essential && \
    apt-get install -y lcov parallel cloc
FROM python:3.10
RUN python --version

# No need to create a venv as we are using a container
RUN pip install --upgrade pip && \
    pip install fabric==2.7.1 requests==2.28.1 docker==6.0.1

# Install docker inside the webserver container
RUN apt-get install -y curl && \
    curl -sSL https://get.docker.com/ | sh
ENV SHARE_DIR /usr/local/share

# Move this as late as possible to avoid invalidating the cache
COPY . /root
# Run sshkeygen, and copy the public key to id_rsa.pub in every subdirectory of containers/
RUN /bin/bash -c 'ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa'
RUN /bin/bash -c 'for d in /root/containers/*/; do if [ -d "$d" ]; then cp /root/.ssh/id_rsa.pub "$d"/id_rsa.pub; fi; done'

ENV SSH_PRIVATE_KEY_PATH /root/.ssh/id_rsa

EXPOSE 3000
CMD ["/bin/bash"]