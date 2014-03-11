#!/usr/bin/env sh

sudo yum -y groupinstall "Development Tools"
sudo yum -y groupinstall "Development Libraries"
sudo yum -y install git
sudo yum -y install python
sudo yum -y install python-devel
sudo yum -y install libevent-devel
sudo easy_install pyzmq
sudo easy_install locustio
sudo easy_install boto
sudo easy_install fabric
echo "done bootstrappin'"
