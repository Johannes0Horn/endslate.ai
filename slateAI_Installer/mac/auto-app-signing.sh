#!/bin/zsh

read -p "Name of Application to sign: " application_name

#Clean from all sorts of stuff
echo "-----------------------------"
printf "\e[32mClean up.\e[m\n"
echo "-----------------------------"
sudo xattr -cr $application_name

#Run Python script that Cleans . Files
echo "-----------------------------"
printf "\e[32mMove Files containing Dots.\e[m\n"
echo "-----------------------------"
python fix_app_folder_names.py $application_name

#Extrasign FFMPEG
echo "-----------------------------"
printf "\e[32mExtrasign FFMPEG.\e[m\n"
echo "-----------------------------"
construct_path=${application_name}/Contents/Resources/imageio_ffmpeg/binaries/ffmpeg-osx64-v4.2.2
codesign --timestamp --force --deep --options runtime  --entitlements entitlement.plist --sign "Developer ID Application: Christian Hofmann (CKPM9TLBU6)" $construct_path

#Signing
echo "-----------------------------"
printf "\e[32mSigning Application.\e[m\n"
echo "-----------------------------"
codesign --timestamp --force --deep --options runtime  --entitlements entitlement.plist --sign "Developer ID Application: Christian Hofmann (CKPM9TLBU6)" $application_name


#Compress file
echo "-----------------------------"
printf "\e[32mCompressing File.\e[m\n"
echo "-----------------------------"
construct_path=${application_name}.zip
/usr/bin/ditto -c -k --sequesterRsrc --keepParent $application_name $construct_path

#Send .app file to Notary Service 
echo "-----------------------------"
printf "\e[32mSend .app file to Apple.\e[m\n"
echo "-----------------------------"
notarize --package $construct_path --username christian.hofi@googlemail.com --password zvmr-vshy-tpdv-vavh --primary-bundle-id com.slateai.slateai

#Create DragnDrop-Installer
echo "-----------------------------"
printf "\e[32mCreate DragnDrop-Installer.\e[m\n"
echo "-----------------------------"
create-dmg  $application_name

#Send .app file to Notary Service
echo "-----------------------------"
printf "\e[32mSend .dmg file to Apple.\e[m\n"
echo "-----------------------------"
construct_path=EndSlate.ai 0.0.1.dmg.zip
notarize --package $construct_path --username christian.hofi@googlemail.com --password zvmr-vshy-tpdv-vavh --primary-bundle-id com.slateai.slateai
