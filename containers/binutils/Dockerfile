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

RUN apt-get -yq install flex bison texinfo libncurses5-dev dejagnu libelf-dev bc libjansson-dev zlib1g-dev

RUN apt-get install -yq --reinstall ca-certificates # Needed for higher ubuntu versions (e.g. 20)

RUN git clone git://sourceware.org/git/binutils.git /home/binutils
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
