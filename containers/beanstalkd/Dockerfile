FROM ubuntu:12.04

RUN apt-get update && apt-get install -y \
	build-essential \
	autoconf \
	automake \
	libtool \
	git \
	curl \
	openssh-server \
	strace \
	--no-install-recommends

RUN cd /tmp && curl -L http://downloads.sourceforge.net/ltp/lcov-1.10.tar.gz | tar xz && cd lcov-* && make install
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

RUN apt-get install -y \
	realpath \
	libevent-dev \
	netcat

RUN git clone https://github.com/kr/beanstalkd.git /home/beanstalkd/
RUN git clone https://github.com/kr/ct.git /home/ct/
ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
