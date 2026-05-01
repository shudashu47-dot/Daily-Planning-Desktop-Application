Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """C:\Program Files\Python311\pythonw.exe"" """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\main.py""", 0, False
Set WshShell = Nothing
