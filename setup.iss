; ArtCore Player installer — Inno Setup 6.3+
; Build: run build.bat (libmpv + PyInstaller first, then this script).
; Expects the PyInstaller output in dist\ArtCorePlayer\.

#define AppName      "ArtCore Player"
#define AppVersion   "1.4.0"
#define AppPublisher "ArtCore"
#define AppURL       "https://github.com/Ruf790/artcore-player"
#define AppExe       "ArtCorePlayer.exe"
#define OldProg      "ArtCorePlayer.video"
#define CapKey       "Software\ArtCore\ArtCore Player\Capabilities"

[Setup]
; Never change AppId: Windows uses it to find the installed copy for updates/uninstall
AppId={{CC3B3D27-0C3A-4387-AF84-F55A8919C074}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=installer
OutputBaseFilename=ArtCorePlayer-Setup-{#AppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
AppCopyright=Copyright (C) 2026 Ruf790 — GNU GPL v3
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
AppMutex=ArtCorePlayerMutex
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes
ShowLanguageDialog=auto
UsedUserAreasWarning=no

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
ru.GroupIntegration=Интеграция с Windows:
en.GroupIntegration=Windows integration:
ru.OpenWith=Добавить в «Открыть с помощью» для видеофайлов
en.OpenWith=Add to "Open with" for video files
ru.VideoFile=Видеофайл
en.VideoFile=Video file
ru.DiscImage=Образ диска
en.DiscImage=Disc image
ru.MakeDefault=Сделать плеером по умолчанию (откроются Параметры Windows)
en.MakeDefault=Make it the default player (opens Windows Settings)

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "openwith";    Description: "{cm:OpenWith}";          GroupDescription: "{cm:GroupIntegration}"

[Files]
Source: "dist\ArtCorePlayer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\formats\*.ico"; DestDir: "{app}\formats"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; DestName: "LICENSE.txt"; Flags: ignoreversion
Source: "THIRD-PARTY.md"; DestDir: "{app}"; DestName: "THIRD-PARTY.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "ArtCore.Player"
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; HKA = HKLM for "all users", HKCU for "just me"
; ── the file types the player offers (never forced on the user: Windows asks / Settings → Apps → Default apps)
; every format has its own ProgId and its own icon ({app}\formats\<ext>.ico, tools/make_format_icons.py);
; the shared ProgId of 1.0–1.2 is removed
Root: HKA; Subkey: "Software\Classes\{#OldProg}"; ValueType: none; Flags: deletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#AppName}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Video player (mpv): 4K, HDR, Blu-ray, any tracks and subtitles"; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}"; ValueType: string; ValueName: "ApplicationIcon"; ValueData: """{app}\{#AppExe}"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#AppName}"; ValueData: "{#CapKey}"; Flags: uninsdeletevalue; Tasks: openwith
; >>> formats (tools/make_format_icons.py --iss)
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mkv"; ValueType: string; ValueName: ""; ValueData: "MKV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mkv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mkv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mkv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mkv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mkv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mkv"; ValueData: "ArtCorePlayer.mkv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mp4"; ValueType: string; ValueName: ""; ValueData: "MP4 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mp4\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mp4.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mp4\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mp4"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mp4"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mp4"; ValueData: "ArtCorePlayer.mp4"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m4v"; ValueType: string; ValueName: ""; ValueData: "M4V — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m4v\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\m4v.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m4v\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.m4v"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m4v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".m4v"; ValueData: "ArtCorePlayer.m4v"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avi"; ValueType: string; ValueName: ""; ValueData: "AVI — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avi\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\avi.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avi\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.avi"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".avi"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".avi"; ValueData: "ArtCorePlayer.avi"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mov"; ValueType: string; ValueName: ""; ValueData: "MOV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mov\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mov.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mov\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mov"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mov"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mov"; ValueData: "ArtCorePlayer.mov"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wmv"; ValueType: string; ValueName: ""; ValueData: "WMV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wmv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\wmv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wmv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.wmv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".wmv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".wmv"; ValueData: "ArtCorePlayer.wmv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.webm"; ValueType: string; ValueName: ""; ValueData: "WEBM — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.webm\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\webm.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.webm\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.webm"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".webm"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".webm"; ValueData: "ArtCorePlayer.webm"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ts"; ValueType: string; ValueName: ""; ValueData: "TS — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ts\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\ts.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ts\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.ts"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".ts"; ValueData: "ArtCorePlayer.ts"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2ts"; ValueType: string; ValueName: ""; ValueData: "M2TS — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2ts\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\m2ts.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2ts\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.m2ts"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m2ts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".m2ts"; ValueData: "ArtCorePlayer.m2ts"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mts"; ValueType: string; ValueName: ""; ValueData: "MTS — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mts\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mts.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mts\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mts\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mts\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mts"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mts"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mts"; ValueData: "ArtCorePlayer.mts"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpg"; ValueType: string; ValueName: ""; ValueData: "MPG — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpg\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mpg.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpg\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mpg"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mpg"; ValueData: "ArtCorePlayer.mpg"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpeg"; ValueType: string; ValueName: ""; ValueData: "MPEG — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpeg\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mpeg.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpeg\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mpeg"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpeg"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mpeg"; ValueData: "ArtCorePlayer.mpeg"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.vob"; ValueType: string; ValueName: ""; ValueData: "VOB — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.vob\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\vob.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.vob\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.vob\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.vob\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.vob"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".vob"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".vob"; ValueData: "ArtCorePlayer.vob"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.flv"; ValueType: string; ValueName: ""; ValueData: "FLV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.flv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\flv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.flv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.flv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".flv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".flv"; ValueData: "ArtCorePlayer.flv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3gp"; ValueType: string; ValueName: ""; ValueData: "3GP — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3gp\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\3gp.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3gp\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.3gp\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.3gp\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.3gp"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".3gp"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".3gp"; ValueData: "ArtCorePlayer.3gp"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3g2"; ValueType: string; ValueName: ""; ValueData: "3G2 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3g2\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\3g2.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.3g2\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.3g2\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.3g2\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.3g2"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".3g2"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".3g2"; ValueData: "ArtCorePlayer.3g2"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogv"; ValueType: string; ValueName: ""; ValueData: "OGV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\ogv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.ogv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ogv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".ogv"; ValueData: "ArtCorePlayer.ogv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogm"; ValueType: string; ValueName: ""; ValueData: "OGM — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogm\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\ogm.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ogm\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogm\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ogm\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.ogm"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ogm"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".ogm"; ValueData: "ArtCorePlayer.ogm"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rm"; ValueType: string; ValueName: ""; ValueData: "RM — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rm\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\rm.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rm\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.rm\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.rm\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.rm"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".rm"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".rm"; ValueData: "ArtCorePlayer.rm"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rmvb"; ValueType: string; ValueName: ""; ValueData: "RMVB — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rmvb\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\rmvb.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.rmvb\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.rmvb\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.rmvb\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.rmvb"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".rmvb"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".rmvb"; ValueData: "ArtCorePlayer.rmvb"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.divx"; ValueType: string; ValueName: ""; ValueData: "DIVX — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.divx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\divx.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.divx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.divx\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.divx\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.divx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".divx"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".divx"; ValueData: "ArtCorePlayer.divx"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.xvid"; ValueType: string; ValueName: ""; ValueData: "XVID — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.xvid\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\xvid.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.xvid\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.xvid\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.xvid\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.xvid"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".xvid"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".xvid"; ValueData: "ArtCorePlayer.xvid"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.asf"; ValueType: string; ValueName: ""; ValueData: "ASF — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.asf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\asf.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.asf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.asf\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.asf\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.asf"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".asf"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".asf"; ValueData: "ArtCorePlayer.asf"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.f4v"; ValueType: string; ValueName: ""; ValueData: "F4V — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.f4v\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\f4v.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.f4v\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.f4v\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.f4v\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.f4v"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".f4v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".f4v"; ValueData: "ArtCorePlayer.f4v"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.hevc"; ValueType: string; ValueName: ""; ValueData: "HEVC — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.hevc\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\hevc.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.hevc\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.hevc\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.hevc\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.hevc"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".hevc"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".hevc"; ValueData: "ArtCorePlayer.hevc"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h264"; ValueType: string; ValueName: ""; ValueData: "H.264 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h264\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\h264.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h264\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.h264\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.h264\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.h264"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".h264"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".h264"; ValueData: "ArtCorePlayer.h264"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h265"; ValueType: string; ValueName: ""; ValueData: "H.265 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h265\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\h265.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.h265\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.h265\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.h265\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.h265"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".h265"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".h265"; ValueData: "ArtCorePlayer.h265"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.264"; ValueType: string; ValueName: ""; ValueData: "H.264 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.264\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\264.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.264\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.264\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.264\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.264"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".264"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".264"; ValueData: "ArtCorePlayer.264"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.265"; ValueType: string; ValueName: ""; ValueData: "H.265 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.265\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\265.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.265\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.265\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.265\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.265"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".265"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".265"; ValueData: "ArtCorePlayer.265"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avc"; ValueType: string; ValueName: ""; ValueData: "AVC — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avc\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\avc.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.avc\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.avc\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.avc\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.avc"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".avc"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".avc"; ValueData: "ArtCorePlayer.avc"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ivf"; ValueType: string; ValueName: ""; ValueData: "IVF — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ivf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\ivf.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.ivf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ivf\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.ivf\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.ivf"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ivf"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".ivf"; ValueData: "ArtCorePlayer.ivf"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.obu"; ValueType: string; ValueName: ""; ValueData: "AV1 — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.obu\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\obu.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.obu\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.obu\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.obu\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.obu"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".obu"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".obu"; ValueData: "ArtCorePlayer.obu"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.y4m"; ValueType: string; ValueName: ""; ValueData: "Y4M — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.y4m\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\y4m.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.y4m\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.y4m\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.y4m\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.y4m"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".y4m"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".y4m"; ValueData: "ArtCorePlayer.y4m"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2v"; ValueType: string; ValueName: ""; ValueData: "M2V — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2v\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\m2v.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m2v\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m2v\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m2v\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.m2v"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m2v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".m2v"; ValueData: "ArtCorePlayer.m2v"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m1v"; ValueType: string; ValueName: ""; ValueData: "M1V — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m1v\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\m1v.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.m1v\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m1v\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.m1v\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.m1v"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m1v"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".m1v"; ValueData: "ArtCorePlayer.m1v"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpe"; ValueType: string; ValueName: ""; ValueData: "MPE — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpe\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mpe.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpe\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpe\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpe\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mpe"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpe"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mpe"; ValueData: "ArtCorePlayer.mpe"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpv"; ValueType: string; ValueName: ""; ValueData: "MPV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mpv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mpv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mpv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mpv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mpv"; ValueData: "ArtCorePlayer.mpv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mxf"; ValueType: string; ValueName: ""; ValueData: "MXF — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mxf\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mxf.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mxf\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mxf\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mxf\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mxf"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mxf"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mxf"; ValueData: "ArtCorePlayer.mxf"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mk3d"; ValueType: string; ValueName: ""; ValueData: "MK3D — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mk3d\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mk3d.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mk3d\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mk3d\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mk3d\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mk3d"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mk3d"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mk3d"; ValueData: "ArtCorePlayer.mk3d"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.qt"; ValueType: string; ValueName: ""; ValueData: "QT — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.qt\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\qt.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.qt\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.qt\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.qt\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.qt"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".qt"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".qt"; ValueData: "ArtCorePlayer.qt"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dv"; ValueType: string; ValueName: ""; ValueData: "DV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\dv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.dv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.dv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.dv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".dv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".dv"; ValueData: "ArtCorePlayer.dv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.nut"; ValueType: string; ValueName: ""; ValueData: "NUT — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.nut\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\nut.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.nut\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.nut\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.nut\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.nut"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".nut"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".nut"; ValueData: "ArtCorePlayer.nut"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.amv"; ValueType: string; ValueName: ""; ValueData: "AMV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.amv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\amv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.amv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.amv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.amv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.amv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".amv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".amv"; ValueData: "ArtCorePlayer.amv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wtv"; ValueType: string; ValueName: ""; ValueData: "WTV — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wtv\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\wtv.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.wtv\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wtv\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.wtv\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.wtv"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".wtv"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".wtv"; ValueData: "ArtCorePlayer.wtv"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dvr-ms"; ValueType: string; ValueName: ""; ValueData: "DVR-MS — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dvr-ms\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\dvr-ms.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.dvr-ms\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.dvr-ms\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.dvr-ms\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.dvr-ms"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".dvr-ms"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".dvr-ms"; ValueData: "ArtCorePlayer.dvr-ms"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mod"; ValueType: string; ValueName: ""; ValueData: "MOD — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mod\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\mod.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.mod\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mod\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.mod\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.mod"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mod"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".mod"; ValueData: "ArtCorePlayer.mod"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tod"; ValueType: string; ValueName: ""; ValueData: "TOD — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tod\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\tod.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tod\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.tod\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.tod\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.tod"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".tod"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".tod"; ValueData: "ArtCorePlayer.tod"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.evo"; ValueType: string; ValueName: ""; ValueData: "EVO — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.evo\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\evo.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.evo\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.evo\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.evo\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.evo"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".evo"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".evo"; ValueData: "ArtCorePlayer.evo"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.trp"; ValueType: string; ValueName: ""; ValueData: "TRP — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.trp\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\trp.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.trp\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.trp\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.trp\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.trp"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".trp"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".trp"; ValueData: "ArtCorePlayer.trp"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tp"; ValueType: string; ValueName: ""; ValueData: "TP — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tp\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\tp.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.tp\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.tp\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.tp\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.tp"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".tp"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".tp"; ValueData: "ArtCorePlayer.tp"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.bik"; ValueType: string; ValueName: ""; ValueData: "BIK — {cm:VideoFile}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.bik\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\bik.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.bik\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.bik\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.bik\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.bik"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".bik"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".bik"; ValueData: "ArtCorePlayer.bik"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.iso"; ValueType: string; ValueName: ""; ValueData: "ISO — {cm:DiscImage}"; Flags: uninsdeletekey; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.iso\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: """{app}\formats\iso.ico"",0"; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\ArtCorePlayer.iso\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.iso\OpenWithProgids"; ValueType: none; ValueName: "{#OldProg}"; Flags: deletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\.iso\OpenWithProgids"; ValueType: string; ValueName: "ArtCorePlayer.iso"; ValueData: ""; Flags: uninsdeletevalue; Tasks: openwith
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".iso"; ValueData: ""; Tasks: openwith
Root: HKA; Subkey: "{#CapKey}\FileAssociations"; ValueType: string; ValueName: ".iso"; ValueData: "ArtCorePlayer.iso"; Tasks: openwith
; <<< formats

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
; silent update from the player itself: start it again afterwards
Filename: "{app}\{#AppExe}"; Flags: nowait runasoriginaluser; Check: WizardSilent
Filename: "ms-settings:defaultapps?registeredAppUser={#AppName}"; Description: "{cm:MakeDefault}"; Flags: shellexec nowait postinstall skipifsilent unchecked; Tasks: openwith

[UninstallDelete]
; Settings and resume positions in %APPDATA%\ArtCorePlayer are kept on purpose.
Type: filesandordirs; Name: "{app}"
