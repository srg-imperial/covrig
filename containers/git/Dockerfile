RUN apt-get install -yq \
	sudo \
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

RUN apt-get -y install \
	zlib1g-dev \
	libpcre3-dev \
	gettext \
	libcurl4-gnutls-dev \
	libexpat1-dev \
	libyaml-perl \
	tcl \
	libhttp-date-perl \
	libtime-modules-perl \
	python \
	unzip \
	libio-pty-perl \
	libssl-dev \
	realpath

RUN git clone https://github.com/git/git.git /home/git
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
