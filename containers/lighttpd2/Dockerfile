FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
	sudo \
	build-essential \
	autoconf \
	automake \
	libtool \
	git \
	curl \
	openssh-server \
    lcov \
    realpath \
	--no-install-recommends

#RUN cd /tmp && curl -L http://downloads.sourceforge.net/ltp/lcov-1.10.tar.gz | tar xz && cd lcov-* && make install
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN apt-get install -yq \
	libglib2.0-dev \
	libev-dev \
	libssl-dev \
	libgnutls28-dev \
	zlib1g-dev \
	libbz2-dev \
	liblua5.1-dev \
	ragel \
	python-pycurl

RUN apt-get install -yq --reinstall ca-certificates

RUN git clone https://github.com/lighttpd/lighttpd2.git /home/lighttpd2
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
