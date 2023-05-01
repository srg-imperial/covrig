# Select a correct base image
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
RUN cd /tmp && curl -L http://downloads.sourceforge.net/project/cloc/cloc/v1.64/cloc-1.64.tar.gz | tar xz && cd cloc-* && make install

RUN mkdir -p /var/run/sshd

RUN mkdir /root/.ssh
# Copy your public certificate to /root/.ssh/authorized_keys
ADD id_rsa.pub /root/.ssh/authorized_keys
RUN chown -R root:root /root/.ssh
RUN chmod -R 700 /root/.ssh

RUN echo "root:root" | chpasswd

ADD measure-cov.sh /root/

# Install all the build dependencies
# e.g. RUN apt-get install -yq python zlib1g-dev

# Copy the git repository to /home/<name>
# e.g. RUN git clone https://github.com/<name>/<name>.git /home/<name>

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
