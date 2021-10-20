#!/bin/zsh

#source /usr/local/anaconda3/etc/profile.d/conda.sh 

#read  -p "do you have the envirement macos_deploy already and is it up to date [y,n]: " macos_deploy


#if [[ "$macos_deploy" == "n" ]]; then
#	read  -p "Enter path to dependency_list: " dep_list
#	conda create -n macos_deploy python=3.7 --yes
#	conda activate macos_deploy
#	conda install --yes --file $dep_list
#
#elif [[ "$macos_deploy" == "y" ]]; then
#        echo "Aktiviere Conda-Envirement"
#	conda activate macos_deploy
#
#fi 


#conda activate macos_deploy
# signing Adobe Plugin

read  -p "path to premiere plugin folder: " plugin_path


#read  -p "path to ZXPSignCmd-64bit: " zxp

zxp=./ZXPSignCmd-64bit

# read -p "package sign name (com.endslateExtension.panel): " package_name
package_name=com.endslateai.panel

#read  -p "path to developerID_application.p12: " p12
p12=/Users/christianhofmann/OneDrive/EndslateAI/Development/Deployment/Zertifikate/developerID_application.p12 

#read -p "password for developerID_application.p12: " pass
pass=ioVmm4Lpy4mvQvkTA933uncMM6Lr

mkdir -p "build"

$zxp -sign $plugin_path build/Endslatai.zxp $p12 $pass -tsa http://timestamp.apple.com/ts01

echo "------------Adobe Plugin signing done----------"
echo ""


$zxp -verify ./build/Endslatai.zxp



# creating .app File





