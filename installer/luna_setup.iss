; ============================================================
;  luna_setup.iss - Kich ban Inno Setup dong goi Luna thanh
;  Luna_Setup.exe (bo cai kieu app Windows: Next -> Next -> Finish).
;
;  CACH BIEN DICH:
;    1. Tai Inno Setup: https://jrsoftware.org/isdl.php
;    2. Mo file nay bang Inno Setup Compiler
;    3. Build (Ctrl+F9) -> ra installer\Output\Luna_Setup.exe
;
;  Bo cai se: chep ma nguon -> tao shortcut -> chay install.bat
;  (install.bat lo phan nang: venv, thu vien, tai model, train).
; ============================================================

#define AppName "Luna"
#define AppVersion "1.0"
#define AppPublisher "Lozens"
#define AppURL "https://github.com/plastma65/luna-vi-companion"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppSupportURL={#AppURL}
; Khong can quyen admin: cai vao thu muc nguoi dung
PrivilegesRequired=lowest
DefaultDirName={userdocs}\Luna
DefaultGroupName=Luna
DisableProgramGroupPage=yes
OutputBaseFilename=Luna_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; AppIcon: bo comment neu co file icon
; SetupIconFile=luna.ico

[Languages]
Name: "vi"; MessagesFile: "compiler:Default.isl"

[Files]
; Chep toan bo ma nguon (tru moi truong ao, model nang, du lieu ca nhan)
Source: "..\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs; \
  Excludes: "\.git\*,\.venv\*,\.venv-tts\*,installer\Output\*,data\memory\*,data\knowledge\*,data\rag_index\*,checkpoints\*,voices\*,logs\*,__pycache__\*,*.pyc"

[Icons]
; Shortcut chay Luna (an, chi hien orb)
Name: "{group}\Luna";        Filename: "wscript.exe"; Parameters: """{app}\Luna.vbs"""; WorkingDir: "{app}"
Name: "{group}\Luna (giong noi)"; Filename: "{app}\Luna_Jarvis.bat"; WorkingDir: "{app}"
Name: "{group}\Dung Luna";   Filename: "wscript.exe"; Parameters: """{app}\Luna_Stop.vbs"""; WorkingDir: "{app}"
Name: "{group}\Cai dat lai (buoc 2)"; Filename: "{app}\install.bat"; WorkingDir: "{app}"
Name: "{group}\Go cai Luna"; Filename: "{uninstallexe}"
; Shortcut ngoai desktop (tuy chon)
Name: "{userdesktop}\Luna"; Filename: "wscript.exe"; Parameters: """{app}\Luna.vbs"""; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong ngoai man hinh"; GroupDescription: "Tuy chon:"

[Run]
; Sau khi chep xong, chay install.bat (tai model + train). Nguoi dung thay cua so tien trinh.
Filename: "{app}\install.bat"; Description: "Cai dat thu vien va model cho Luna (BAT BUOC, chay 1 lan, ~15-40 phut)"; \
  Flags: postinstall shellexec skipifsilent runasoriginaluser

[UninstallDelete]
; Khi go cai, xoa luon nhung thu install.bat tao ra
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\checkpoints"
Type: filesandordirs; Name: "{app}\voices"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"

[Code]
{ Canh bao neu khong tim thay Python 3.11 truoc khi cai }
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  HasPy: Boolean;
begin
  HasPy := False;
  { Thu 'py -3.11' }
  if Exec('cmd.exe', '/c py -3.11 --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    if ResultCode = 0 then HasPy := True;
  { Thu 'python --version' co chua 3.11 }
  if not HasPy then
    if Exec('cmd.exe', '/c python --version 2>&1 | findstr 3.11', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      if ResultCode = 0 then HasPy := True;

  if not HasPy then
  begin
    if MsgBox('Luna can Python 3.11 (chua thay tren may nay).' + #13#10 +
              'Anh/chi hay cai Python 3.11 truoc (nho tick "Add Python to PATH"), roi chay lai bo cai.' + #13#10#13#10 +
              'Van tiep tuc? (installer se chep file, nhung buoc cai model se bao loi neu thieu Python)',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
  Result := True;
end;
