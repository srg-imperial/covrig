# Set up a virtual machine to run our analytics.

# Prerequisites:

# Take in a username, e.g. abc123
UNAME=$1

# Setup for Imperial DoC VMs

# sudo apt-get install -y ufw
# sudo ufw allow 80
# sudo ufw allow 22
# sudo addgroup $UNAME
# useradd ${UNAME} -g ${UNAME}
# sudo usermod -a -G sudo $UNAME
# sudo usermod -a -G ssh $UNAME
# passwd ${UNAME}
# sudo mkdir /home/$UNAME
# sudo chown $UNAME:$UNAME /home/$UNAME
# mkdir /home/$UNAME/.ssh
# sudo chown $UNAME:$UNAME /home/$UNAME/.ssh

# From local machine
# For the machine to ssh into docker containers
# scp ~/.ssh/id_rsa $UNAME@cloud-vm-XX-XX.doc.ic.ac.uk:/home/$UNAME/.ssh/id_rsa

# For ssh'ing into the machine
# ssh-copy-id -i /home/tom/.ssh/id_ed25519.pub ${UNAME}@...

# git clone https://github.com/srg-imperial/covrig.git && cd covrig && git switch dev


# Then run this script on the VM:

sudo apt-get install -y python3.8-venv
python3.8 -m venv venv
source venv/bin/activate
pip install fabric==2.7.1 docker  # assuming bash, otherwise use . instead of source

sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world

sudo apt-get install -y parallel

sudo usermod -a -G docker $UNAME

# Then reboot to update permissions for docker

# cd covrig
# screen -S sessionX
# source venv/bin/activate
# docker build -t git -f containers/git/Dockerfile containers/git
# ./utils/run_analytics_parallel_nologs.sh git 100 4 git 0397305 5