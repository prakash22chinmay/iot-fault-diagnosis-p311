' Run P_311 Assistant silently in the background 24/7
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c start_assistant.bat", 0, False
Set WshShell = Nothing
