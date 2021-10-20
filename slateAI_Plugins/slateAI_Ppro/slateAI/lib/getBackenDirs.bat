@echo off
FOR /F "tokens=2* skip=2" %%a in ('reg query "HKLM\SOFTWARE\Wow6432Node\SlateAI" /v "Path"') do set "test1=%%b"
FOR /F "tokens=2* skip=2" %%a in ('reg query "HKLM\SOFTWARE\SlateAI" 			 /v "Path"') do set "test2=%%b"
FOR /F "tokens=2* skip=2" %%a in ('reg query "HKCU\SOFTWARE\Wow6432Node\SlateAI" /v "Path"') do set "test3=%%b"
FOR /F "tokens=2* skip=2" %%a in ('reg query "HKCU\SOFTWARE\SlateAI" 			 /v "Path"') do set "test4=%%b"
echo %test1%;%test2%;%test3%;%test4%

