@echo off
rem The ground inspector: fly through any stadium model (tools/inspect/ground_inspector.gd).
rem   inspect_ground.bat              opens the MCG
rem   inspect_ground.bat scg          opens the first ground whose name has "scg" in it
rem   set GODOT=C:\path\to\Godot.exe  if Godot is not on PATH
setlocal
set "ROOT=%~dp0..\.."
if "%GODOT%"=="" (
  for %%G in (godot.exe godot4.exe Godot_v4.7.2-stable_win64.exe Godot.exe) do (
    if "%GODOT%"=="" for %%P in (%%G) do if not "%%~$PATH:P"=="" set "GODOT=%%~$PATH:P"
  )
)
if "%GODOT%"=="" (
  echo Godot was not found. Set GODOT to your Godot 4.7 exe, for example:
  echo   set GODOT=C:\Godot\Godot_v4.7.2-stable_win64.exe
  pause
  exit /b 1
)
set "PICK=%~1"
if "%PICK%"=="" set "PICK=mcg"
"%GODOT%" --path "%ROOT%" res://tools/inspect/GroundInspector.tscn -- --ground=%PICK% %2 %3
