FROM ubuntu:20.04

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

#RUN cd /tmp && curl -L http://downloads.sourceforge.net/ltp/lcov-1.10.tar.gz | tar xz && cd lcov-* && make install
#RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN adduser --gecos "" --disabled-password regular

RUN apt-get -yq install libevent-dev

#RUN wget --version
#
#RUN wget https://letsencrypt.org/certs/isrg-root-x1-cross-signed.pem --no-check-certificate
#RUN sudo cp isrg-root-x1-cross-signed.pem /etc/ssl/certs/
RUN sudo apt-get install -yq --reinstall ca-certificates

RUN git clone https://github.com/memcached/memcached.git /home/memcached
RUN git config --global --add safe.directory /home/memcached
RUN chown -R root:root /home/memcached
RUN cd /home/memcached && git status && cd ../..
RUN chown -R regular /home/memcached
RUN su regular -c pwd && cd /home/memcached && git status && cd ../..
# Don't know if this is necessary.

# autogen.sh doesn't seem to work properly if we do it inline. Run here instead
RUN cd /home/memcached && ./autogen.sh && cd ../..

ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
