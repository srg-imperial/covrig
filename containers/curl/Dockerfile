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
    realpath \
	--no-install-recommends

# For curl to emit gcov properly, we need lcov 1.16 (likely to do with no one source dir)
RUN cd /tmp && curl -L https://github.com/linux-test-project/lcov/releases/download/v1.16/lcov-1.16.tar.gz | tar xz && cd lcov-* && make PREFIX=/usr install
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install

# Remove the old version of gcc
RUN apt-get remove gcc -y

RUN sudo apt install software-properties-common -y
RUN sudo add-apt-repository ppa:ubuntu-toolchain-r/test
RUN sudo apt update -y && sudo apt install gcc-9 -y
# Symbolic link between gcc-9, gcov-9 to gcc, gcov
RUN sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-9 100
RUN sudo update-alternatives --install /usr/bin/gcov gcov /usr/bin/gcov-9 100

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN apt-get install -yq \
    libssl-dev \
    stunnel4 \
    python3 \
    python-impacket

RUN apt-get install -yq --reinstall ca-certificates # Needed for higher ubuntu versions (e.g. 20)

RUN git clone https://github.com/curl/curl.git /home/curl

ADD measure-cov.sh /root/

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
