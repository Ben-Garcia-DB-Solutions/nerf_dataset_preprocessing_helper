:: This script was created by Epic Games Slovakia & Ben Garcia

:: Switch off console output.
@echo off

set Venue=%1
set ImagesFolder=%2
set savePath=%3
set PLYPath=%4
set CSVPath=%5
set ExportSettings=%6
set DirectionString=%~7

:: Path to RealityCapture application.
set RealityCaptureExe="C:\Program Files\Capturing Reality\RealityCapture\RealityCapture.exe"

:: Root path to work folders where all the datasets are stored
set RootFolder=%~dp0

:: Select images which end on "f" before the extensions
set Images_F=g/[_f]\./

:: We run this with surpress errors to surpress the 'Not all images are aligned error', which is dangerous, but I don't know a better way.
:: We should run this headless.

@echo on

:: Run RealityCapture
%RealityCaptureExe% -load %savePath% ^
        -selectMaximalComponent ^
        -selectAllImages -exportRegistration %CSVPath% ^
        -exportSparsePointCloud %PLYPath% ^
        -quit

