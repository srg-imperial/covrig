FROM ubuntu:20.04
# TODO: Downgrade to 14.04 like the others?

RUN apt-get update && apt-get install -y \
	apt-utils \
	sudo \
	build-essential \
	automake \
	autoconf \
    autotools-dev \
    pkg-config \
	libtool \
	git \
	curl \
	openssh-server \
    wget \
    lcov \
    cloc \
	--no-install-recommends

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN adduser --gecos "" --disabled-password regular

RUN apt-get -yq install libevent-dev

RUN sudo apt-get install -yq --reinstall ca-certificates

RUN git clone https://github.com/memcached/memcached.git /home/memcached
#RUN git config --global --add safe.directory /home/memcached
#RUN chown -R root:root /home/memcached
#RUN cd /home/memcached && git status && cd ../..
#RUN chown -R regular /home/memcached
#RUN su regular -c pwd && cd /home/memcached && git status && cd ../..
# Don't know if this is necessary still get a dubious certificate error if we run commands as regular (su regular).

# autogen.sh doesn't seem to work properly if we do it inline. Run here instead
RUN cd /home/memcached && ./autogen.sh && cd ../..

ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
