' Dung Luna: tat orb + server TTS + voice_luna (chi tat dung tien trinh cua Luna).
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell -NoProfile -WindowStyle Hidden -Command ""Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'overlay\.py|voice_luna\.py|chat_voice_luna\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }""", 0, False
