# Set up a virtual machine to run our analytics.

# Prerequisites:

# e.g. tfb19
UNAME=$1
# Oneliner can also be done with export UNAME=tfb19, etc.:
# sudo apt-get install -y ufw && sudo ufw allow 80 && sudo ufw allow 22 && sudo addgroup $UNAME && sudo usermod -a G sudo $UNAME && sudo usermod -a -G ssh $UNAME && sudo mkdir /home/$UNAME && sudo chown $UNAME:$UNAME /home/$UNAME && mkdir /home/$UNAME/.ssh && sudo chown $UNAME:$UNAME /home/$UNAME/.ssh

# sudo apt-get install -y ufw
# sudo ufw allow 80
# sudo ufw allow 22
# sudo addgroup $UNAME
# sudo usermod -a G sudo $UNAME
# sudo usermod -a -G ssh $UNAME
# sudo mkdir /home/$UNAME
# sudo chown $UNAME:$UNAME /home/$UNAME
# mkdir /home/$UNAME/.ssh

# From local machine
# scp ~/.ssh/id_rsa $UNAME@cloud-vm-XX-XX.doc.ic.ac.uk:/home/$UNAME/.ssh/id_rsa

# git clone https://github.com/srg-imperial/covrig.git && cd covrig && git switch dev

sudo apt-get install -y python3.8-venv
python3.8 -m venv venv
source venv/bin/activate
pip install fabric==2.7.1 docker

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

# reboot

# source venv/bin/activate
# screen -S sessionX
# docker build -t git -f containers/git/Dockerfile containers/git
# ./utils/run_analytics_parallel_nologs.sh git 100 4 git 0397305 5