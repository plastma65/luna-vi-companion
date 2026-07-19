' ==============================================================
'  Luna.vbs  -  Bat Luna CHI voi orb, khong hien terminal nao.
'  TTS chay trong tien trinh (piper) -> KHONG con server TTS.
'  Chi 2 tien trinh chay ngam: orb + voice_luna. Log ghi vao logs\.
'  Dung Luna: bam dup Luna_Stop.vbs.
' ==============================================================
Option Explicit
Dim fso, sh, base, q
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
q = Chr(34)

' Orb overlay
sh.Run q & base & "\.venv\Scripts\pythonw.exe" & q & " " & _
       q & base & "\scripts\overlay.py" & q & " --nodemo", 0, False

' Luna giong noi (piper TTS ben trong, khong server)
sh.Run q & base & "\.venv\Scripts\pythonw.exe" & q & " " & _
       q & base & "\scripts\voice_luna.py" & q, 0, False
