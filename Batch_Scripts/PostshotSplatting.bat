:: This script was created by Ben Garcia

:: Switch off console output.
@echo off

set ImagesFolder=%1
set savePath=%2

:: Path to RealityCapture application.
set PostShotExe="C:\Program Files\Jawset Postshot\bin\postshot-cli.exe"

:: Root path to work folders where all the datasets are stored
set RootFolder=%~dp0

:: @echo on

:: I'm only running to 10k iterations, which is low quality, with the idea that we'll come back and improve quality of any models needed and that if we have gotten to 10k iters, we've proved that it works.

%PostShotExe% train ^
--import %ImagesFolder% ^
-s 10 ^
--max-image-size 0 ^
--output %savePath% ^