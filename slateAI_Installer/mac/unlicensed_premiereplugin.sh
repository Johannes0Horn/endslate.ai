#! /bin/bash
u="$USER"
defaults write /Users/$u/Library/Preferences/com.adobe.CSXS.9.plist PlayerDebugMode 1

#ls|cat>/Users/christianhofmann/Downloads/test.txt
#echo $u>/Users/christianhofmann/Downloads/user.txt

mv  com.endslateExtension.panel /Library/Application\ Support/Adobe/CEP/extensions/
