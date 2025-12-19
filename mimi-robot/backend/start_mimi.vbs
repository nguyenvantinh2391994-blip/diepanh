Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "E:\diepanh\mimi-robot\backend\src"
WshShell.Run "cmd /c python main.py --foreground > ..\data\mimi.log 2>&1", 0
Set WshShell = Nothing
