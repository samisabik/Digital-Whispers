#!/bin/bash
clear

#Global apt setup + cleanup
apt-get update && apt-get -y upgrade
apt-get install -y git build-essential python-dev python-setuptools python-pip sox portaudio19-dev python-pyaudio
apt-get -y remove --auto-remove --purge 'libx11-.*'
apt-get -y autoremove --purge

#Install Portaudi -- jack dependencie
wget http://portaudio.com/archives/pa_stable_v19_20140130.tgz
tar xvf pa_stable_v19_20140130.tgz
cd portaudio
./configure --without-jack
make clean && make && make install
cd ..

#Install Watson Python SDK
git clone https://github.com/watson-developer-cloud/python-sdk.git
cd python-sdk
python setup.py install
cd ..

# cleanup
rm -r python-sdk portaudio pa_stable_v19_20140130.tgz

#Set new hostname
#Copy edited alsa.conf with default USB audio
cp alsa.conf /usr/share/alsa/alsa.conf
