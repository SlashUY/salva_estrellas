Dim shell
Set shell = CreateObject("WScript.Shell")
shell.Run "pythonw """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\salva_estrellas.py""", 0, False
Set shell = Nothing
