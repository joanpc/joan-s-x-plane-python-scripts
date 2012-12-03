;
; NSIS X-Plane Python Scripts Installer for windows
;

; This script can be build with NSIS: http://nsis.sourceforge.net
;
; Required NSIS plugins:
; ----------------------
; INETC:  http://nsis.sourceforge.net/Inetc_plug-in
; ZIPDLL: http://nsis.sourceforge.net/ZipDLL_plug-in

; Copyright (C) 2012  Joan Perez i Cauhe
;
; ---
; This program is free software; you can redistribute it and/or
; modify it under the terms of the GNU General Public License
; as published by the Free Software Foundation; either version 2
; of the License, or any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
; ---


!include "LogicLib.nsh"
!include "MUI2.nsh"

; The name of the installer
Name    "X-Plane Python Plugins Net Installer"
caption "X-Plane Python Plugins Net Installer"

; The file to write
OutFile "PythonScriptsNetInstaller.exe"

; Default installation directory
InstallDir "$PROGRAMFILES"

; Request application privileges for Windows Vista
RequestExecutionLevel user

; --------------
; CUSTOM Strings
; --------------

!define MUI_DIRECTORYPAGE_TEXT_TOP          "Please locate your X-Plane installation folder in wich to install the plugins"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION  "X-Plane folder"

!define MUI_COMPONENTSPAGE_TEXT_TOP         "Choose wich components to install"
!define MUI_COMPONENTSPAGE_TEXT_COMPLIST    "Select wich components you want to install."

!define MUI_FINISHPAGE_TITLE                "Thanks for installing my plugins!"
!define MUI_FINISHPAGE_TEXT                 "Installation finished. $\n$\nEnjoy and send-me your comments on the .org!$\n$\n$\n joanpc."

!define MUI_FINISHPAGE_NOREBOOTSUPPORT ; Force disable reboot

; -----
; PAGES
; -----

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

DirText "Please select your X-Plane installation Folder."

InstType "32bit"
InstType "64bit"


; ----------------
; GLOBAL VARIABLES
; ----------------

Var /GLOBAL SCRIPTS
var /GLOBAL SRC
var /GLOBAL SOURCE
var /GLOBAL NAME
var /GLOBAL DOWNLOADS


; Check X-Plane folder
Function .onVerifyInstDir
    IfFileExists "$INSTDIR\X-Plane.exe" PathGood
      Abort ;
    PathGood:
FunctionEnd


Function .onInit
   IfFileExists "$PROGRAMFILES\X-Plane" 0 +2
   StrCpy $INSTDIR "$PROGRAMFILES\X-Plane"
   IfFileExists "$PROGRAMFILES\X-Plane 9" 0 +2
   StrCpy $INSTDIR "$PROGRAMFILES\X-Plane 9"
   IfFileExists "$PROGRAMFILES\X-Plane 10" 0 +2
   StrCpy $INSTDIR "$PROGRAMFILES\X-Plane 10"
FunctionEnd

; --------
; SECTIONS
; --------

Section "Python 2.7 (32bit)" python32
  SectionIn 1
  Call dirCheck
  IfFileExists "$DOWNLOADS\python-2.7.3.msi" 0 +2
  MessageBox MB_YESNO "A previously downloaded Python installer is avaliable on the hard disk. $\n\
                       Do you want to use-it?" IDYES Install
  inetc::get /NOCANCEL http://python.org/ftp/python/2.7.2/python-2.7.3.msi python-2.7.3.msi
  Install:
  ExecWait '"msiexec" /i "$DOWNLOADS\python-2.7.3.msi"'
SectionEnd

Section "Python 2.7 (64bit)" python64
  SectionIn 2
  Call dirCheck
  IfFileExists "$DOWNLOADS\python-2.7.3.amd64.msi" 0 +2
  MessageBox MB_YESNO "A previously downloaded Python installer is avaliable on the hard disk. $\n\
                       Do you want to use-it?" IDYES Install
  inetc::get /NOCANCEL http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi python-2.7.3.amd64.msi
  Install:
  ExecWait '"msiexec" /i "$DOWNLOADS\python-2.7.3.amd64.msi"'
SectionEnd

Section "Python interface - Sandy Barbour" pyinterface
  SectionIn 1 2
  Call dirCheck
  inetc::get /NOCANCEL http://www.xpluginsdk.org/downloads/latest/Python27/PythonInterface.zip PythonInterface.zip
  Delete "$INSTDIR\Resources\plugins\PythonInterfaceWin27.xpl"
  Delete "$INSTDIR\Resources\plugins\PythonInterfaceWin26.xpl"
  Delete "$INSTDIR\Resources\plugins\PythonInterface.ini"
  ZipDLL::extractall  $DOWNLOADS\PythonInterface.zip "$INSTDIR\Resources\plugins"
SectionEnd

Section "OpenSceneryX" opensceneryx
  SectionIn 1 2
  Call dirCheck
  IfFileExists "$DOWNLOADS\OpenSceneryX-Installer-Windows.zip" 0 +2
  MessageBox MB_YESNO "A previously downloaded  OpenSceneryX installer is avaliable on the hard disk. $\n\
                       Do you want to use-it?" IDYES Install
  inetc::get /NOCANCEL http://www.opensceneryx.com/downloads/OpenSceneryX-Installer-Windows.zip OpenSceneryX-Installer-Windows.zip
  Install:
  ZipDLL::extractall  $DOWNLOADS\OpenSceneryX-Installer-Windows.zip "$DOWNLOADS"
  ExecWait '$DOWNLOADS\OpenSceneryX Installer\OpenSceneryX Installer.exe'
  RmDir /r '$DOWNLOADS\OpenSceneryX Installer'
SectionEnd

Section "XGFS NOAA Weather" xgfs
  SectionIn 1 2
  StrCpy $SOURCE "https://github.com/joanpc/XplaneNoaaWeather/zipball/master"
  StrCpy $NAME "XnoaaWeather"
  Call githubInstall
SectionEnd

Section "Ground Services" groundServices
  SectionIn 1 2
  StrCpy $SOURCE "https://github.com/joanpc/GroundServices/zipball/master"
  StrCpy $NAME "GroundServices"
  Call githubInstall
SectionEnd

Section "xJoyMap" xjoymap
  SectionIn 1 2
  StrCpy $SOURCE "https://github.com/joanpc/xJoyMap/zipball/master"
  StrCpy $NAME "xJoyMap"
  Call githubInstall
SectionEnd

Section "FastPlan" fastplan
  SectionIn 1 2
  Call dirCheck
  inetc::get /NOCANCEL https://raw.github.com/joanpc/joan-s-x-plane-python-scripts/master/PI_FastPlan.py PI_FastPlan.py
  Rename /REBOOTOK "$DOWNLOADS\PI_FastPlan.py" "$SCRIPTS\PI_FastPlan.py"
SectionEnd

Section "ScriptsUpdater" scriptsupdater
  SectionIn 1 2
  Call dirCheck
  inetc::get /NOCANCEL https://raw.github.com/joanpc/joan-s-x-plane-python-scripts/master/PI_ScriptsUpdater.py PI_ScriptsUpdater.py
  Rename /REBOOTOK "$DOWNLOADS\PI_ScriptsUpdater.py" "$SCRIPTS\PI_ScriptsUpdater.py"
SectionEnd

Function .onSelChange
  ; 64 or 32 not both
  # keep section 'test' selected
  SectionGetFlags ${python32} $0
  SectionGetFlags ${python64} $1
  

  IntOp $4 ${SF_SELECTED} | ${SF_RO}

  StrCmp $0 $1 0 +3
  SectionSetFlags ${python32} 0
  SectionSetFlags ${python64} 0


FunctionEnd

Function githubInstall
  ;
  ; Install a zip file from github
  ;
 
  Call dirCheck
  inetc::get /NOCANCEL $SOURCE $DOWNLOADS\$NAME.zip

  ZipDLL::extractall $DOWNLOADS\$NAME.zip "$DOWNLOADS"
  
  ; Find zip subdir
  FindFirst $0 $1 "$DOWNLOADS\joanpc-*"
  StrCpy $SRC "$DOWNLOADS\$1"
  DetailPrint $SRC
  FindClose $0
  
  ; Move subdir contents outside
  FindFirst $0 $1 "$SRC\*.*"
  loop:
    StrCmp $1 "" done
    Rename /REBOOTOK "$SRC\$1" "$SCRIPTS\$1"
    FindNext $0 $1
    Goto loop
  done:
  FindClose $0
  
  ; Delete directory
  RMDIR /r $SRC
FunctionEnd

Function dirCheck
  ; Create and set directories
  CreateDirectory   "$INSTDIR\Resources"
  CreateDirectory   "$INSTDIR\Resources\Downloads"
  CreateDirectory   "$INSTDIR\Resources\plugins"
  CreateDirectory   "$INSTDIR\Resources\plugins\PythonScripts"
  StrCpy $DOWNLOADS "$INSTDIR\Resources\Downloads"
  StrCpy $SCRIPTS   "$INSTDIR\Resources\plugins\PythonScripts"
  SetOutPath        "$DOWNLOADS"
FunctionEnd

; Section Descriptions

  ;Language strings
  LangString DESC_python ${LANG_ENGLISH} "Required by all plugins. $\n$\n\
  This will download and install python 2.7. $\n$\n\
  Select this option unless you've installed python 2.7 before."

  LangString DESC_pyinterface ${LANG_ENGLISH} "Required by all plugins. $\n$\n\
  Sandy Barbour's X-Plane Python Interface brings the power of python to X-Plane. $\n$\n\
  This will install the last version avaliable."

  LangString DESC_groundServices ${LANG_ENGLISH} "Provides ground services with object animations using OpenSceneryX objects. $\n$\n\
  A nice plugin to have some movement around your plane, and do your push-back and refueling."

  LangString DESC_opensceneryx ${LANG_ENGLISH} "Required by ground services. $\n$\n\
  The OpenSceneryX project is a free to use library of scenery objects for X-Plane and used by a lot of scenery addons."
  
  LangString DESC_xgfs ${LANG_ENGLISH} "Uses NOAA Global Forecast data to set XPlane Weather. $\n\
  Provides correct upper wind levels and jet-streams over the globe and close-to real weather on remote locations without a close METAR report."

  LangString DESC_xjoymap ${LANG_ENGLISH} "xJoyMap is the simplest way to modify datarefs \
  with your joystick and keystrokes. It also allows to create advanced combined commands."

  LangString DESC_fastplan ${LANG_ENGLISH} "Just enter your departure and destination airports and FastPlan will find a route using \
  rfinder.asalink.net and program your FMC."
  
  LangString DESC_scriptsupdater ${LANG_ENGLISH} "Update all these scripts from x-plane plugins menu"

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${python32} $(DESC_python)
    !insertmacro MUI_DESCRIPTION_TEXT ${python64} $(DESC_python)
    !insertmacro MUI_DESCRIPTION_TEXT ${pyinterface} $(DESC_pyinterface)
    !insertmacro MUI_DESCRIPTION_TEXT ${groundServices} $(DESC_GroundServices)
    !insertmacro MUI_DESCRIPTION_TEXT ${xgfs} $(DESC_xgfs)
    !insertmacro MUI_DESCRIPTION_TEXT ${xjoymap} $(DESC_xjoymap)
    !insertmacro MUI_DESCRIPTION_TEXT ${opensceneryx} $(DESC_opensceneryx)
    !insertmacro MUI_DESCRIPTION_TEXT ${fastplan} $(DESC_fastplan)
    !insertmacro MUI_DESCRIPTION_TEXT ${scriptsupdater} $(DESC_scriptsupdater)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END
