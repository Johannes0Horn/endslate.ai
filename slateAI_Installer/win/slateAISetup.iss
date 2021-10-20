#define MyAppName "slateAI"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "slateAI"
#define MyAppURL "http://www.endslate.ai/"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{9B408243-D46E-4344-A2E3-1002DBB79A64}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
;LicenseFile=C:\Users\johan\Desktop\License File.txt
;InfoBeforeFile=C:\Users\johan\Desktop\before Installation.txt
;InfoAfterFile=C:\Users\johan\Desktop\after installation.txt
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
OutputDir=C:\Users\johan\Desktop\innosetupoutput
OutputBaseFilename=EndSlateai
SetupIconFile=..\slateAIBackend\deployment_files\Windows/Slate_Logo.ico
UninstallDisplayIcon=..\slateAIBackend\deployment_files\Windows/Slate_Logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "C:\Users\johan\Desktop\pyinstaller\dist\slateAI/*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"

[Registry]
Root: "HKLM"; Subkey: "Software\slateAI"; ValueType: string; ValueName: "path"; ValueData: "{app}"; Flags: uninsdeletekey

[Files]
Source: "../slateAIBackend\deployment_files\Windows/VC_redist.x64.exe"; DestDir: {tmp}; Flags: deleteafterinstall

[Run]
Filename: {tmp}\VC_redist.x64.exe; Parameters: "/q /norestart"; \
    StatusMsg: "Installing VC++ 2019 Redistributables..."
    ;Check: VCRedistNeedsInstall; WorkingDir: {app}\bin;

