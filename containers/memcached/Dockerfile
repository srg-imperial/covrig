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
    cloc \
    realpath \
    psmisc \
	--no-install-recommends

RUN cd /tmp && curl -L https://ftp.gnu.org/gnu/automake/automake-1.12.1.tar.gz --insecure | tar xz && cd automake-* && ./configure --prefix=/usr && make install
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

#FROM ubuntu:20.04
#
#RUN apt-get update && apt-get install -y \
#	apt-utils \
#	sudo \
#	build-essential \
#	automake \
#	autoconf \
#    autotools-dev \
#    pkg-config \
#	libtool \
#	git \
#	curl \
#	openssh-server \
#    wget \
#    lcov \
#    cloc \
#	--no-install-recommends
#
#RUN mkdir -p /var/run/sshd
#
#RUN mkdir /root/.ssh
#ADD id_rsa.pub /root/.ssh/authorized_keys
#RUN chown -R root:root /root/.ssh
#RUN chmod -R 700 /root/.ssh
#
#RUN echo "root:root" | chpasswd
#
#RUN adduser --gecos "" --disabled-password regular
#
#RUN apt-get -yq install libevent-dev
#
#RUN sudo apt-get install -yq --reinstall ca-certificates
#
#RUN git clone https://github.com/memcached/memcached.git /home/memcached
##RUN git config --global --add safe.directory /home/memcached
##RUN chown -R root:root /home/memcached
##RUN cd /home/memcached && git status && cd ../..
##RUN chown -R regular /home/memcached
##RUN su regular -c pwd && cd /home/memcached && git status && cd ../..
## Don't know if this is necessary still get a dubious certificate error if we run commands as regular (su regular).
#
## autogen.sh doesn't seem to work properly if we do it inline. Run here instead
#RUN cd /home/memcached && ./autogen.sh && cd ../..
#
#ADD measure-cov.sh /root/
#
#EXPOSE 22
#CMD ["/usr/sbin/sshd", "-D"]
