#!/bin/bash

#activate conda
source /usr/local/anaconda3/etc/profile.d/conda.sh

#Remove old envirement
conda env remove --name deployment -y

#install new envirement
conda create --name deployment python=3.7 -y

#activate envirement
conda activate deployment

install_pips1=(
pycrypto
imageio_ffmpeg
opencv-python-headless
tensorflow==1.14.0
plaidml-keras
easydict
pyqt5
asyncqt
pyside2
fleep
get-video-properties
websockets
psutil
sklearn
librosa
ffmpeg
setuptools
)

## LOOP
for i in ${install_pips1[@]}

do
    pip3 install $i
done

#Uninstall enum34, because it produces errors
pip uninstall enum34 -y


install_pips2=(
pyinstaller
pyarmor
)

# LOOP
for i in ${install_pips2[@]}

do
    pip3 install $i
done

pyarmor register pyarmor-regfile-1.zip
