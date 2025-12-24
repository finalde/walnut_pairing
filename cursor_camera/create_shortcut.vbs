Set WshShell = WScript.CreateObject("WScript.Shell")
Set oShellLink = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") + "\Camera Capture.lnk")
oShellLink.TargetPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) + "\run_camera_capture.bat"
oShellLink.WorkingDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
oShellLink.Description = "Launch 8-Camera Capture Application"
oShellLink.Save
WScript.Echo "Desktop shortcut created successfully!"

