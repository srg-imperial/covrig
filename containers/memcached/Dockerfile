FROM ubuntu:14.04

RUN apt-get update && apt-get install -y \
	apt-utils \
	sudo \
	build-essential \
	autoconf \
#	automake \ - need to install from source
	libtool \
	git \
	curl \
	openssh-server \
    lcov \
    realpath \
    psmisc \
	--no-install-recommends

RUN cd /tmp && curl -L https://ftp.gnu.org/gnu/automake/automake-1.11.1.tar.gz --insecure | tar xz && cd automake-* && ./configure --prefix=/usr && make install
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install
RUN cd /tmp && curl -L https://pkgconfig.freedesktop.org/releases/pkg-config-0.28.tar.gz --insecure | tar xz && cd pkg-config-* && ./configure --prefix=/usr \
            --with-internal-glib \
            --disable-host-tool  \
            --docdir=/usr/share/doc/pkg-config-0.28 && make && make install

#RUN cd /tmp && curl -L http://downloads.sourceforge.net/ltp/lcov-1.10.tar.gz | tar xz && cd lcov-* && make install
#RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.60/cloc-1.60.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN adduser --gecos "" --disabled-password regular

RUN apt-get -yq install libevent-dev

RUN git clone https://github.com/memcached/memcached.git /home/memcached

# allow regular user full access to the memcached directory
RUN chown -R regular /home/memcached

ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
