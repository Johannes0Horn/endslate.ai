REM activate envirement
conda activate deployment

REM compile
pyarmor pack --clean -e "--noconfirm --windowed --icon=Slate_Logo.ico" --with-license /Users/christianhofmann/OneDrive/EndslateAI/Development/Deployment/Zertifikate/Pyarmor\ License/Testlicense/licenses/testlicense/license.lic slateAI.py
