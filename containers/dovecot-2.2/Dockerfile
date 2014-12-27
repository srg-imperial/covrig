FROM ubuntu:12.04

RUN apt-get update && apt-get install -y \
	sudo \
	build-essential \
	autoconf \
	automake \
	libtool \
	git \
	hg \
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

RUN apt-get install -yq \
	gettext \
	libssl-dev \
	pkg-config \
  wget \
  realpath

RUN cd /tmp && https://github.com/cosmin/git-hg.git && cd git-hg && make && make install

RUN git-hg clone http://hg.dovecot.org/dovecot-2.2/ /home/dovecot-2.2
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
