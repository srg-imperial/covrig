FROM ubuntu:12.04

RUN apt-get update && apt-get install -y \
	sudo \
	build-essential \
	autoconf \
	automake \
	libtool \
	git \
	curl \
	openssh-server \
	--no-install-recommends

RUN cd /tmp && curl -L http://downloads.sourceforge.net/ltp/lcov-1.10.tar.gz | tar xz && cd lcov-* && make install
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.60/cloc-1.60.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN apt-get install -y \
	realpath \
	libglib2.0-dev \
	libev-dev \
	libssl-dev \
	libpcre3-dev \
	zlib1g-dev \
	libbz2-dev \
	liblua5.1-dev

RUN git clone https://github.com/lighttpd/lighttpd1.4.git /home/lighttpd1.4/
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
