#activate conda
source /usr/local/anaconda3/etc/profile.d/conda.sh

#activate envirement
conda activate deployment

#compile
pyarmor pack --clean -e "--noconfirm --windowed --icon=Slate_Logo.icns --osx-bundle-identifier="com.slateai.slateai"" --with-license /Users/christianhofmann/OneDrive/EndslateAI/Development/Deployment/Zertifikate/Pyarmor\ License/Testlicense/licenses/testlicense/license.lic slateAI.py
