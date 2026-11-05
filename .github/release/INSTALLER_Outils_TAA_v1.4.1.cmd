@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Installation Outils TAA v1.4.1
echo.
echo ==============================================================
echo    Outils TAA v1.4.1 - Installation utilisateur sans admin
echo    Revit 2025.4 / pyRevit 5.x
echo ==============================================================
echo.
if not defined APPDATA goto ERROR_ENV
if not defined TEMP goto ERROR_ENV
where powershell.exe >nul 2>&1
if errorlevel 1 goto ERROR_POWERSHELL
tasklist /FI "IMAGENAME eq Revit.exe" 2>nul | find /I "Revit.exe" >nul
if not errorlevel 1 goto ERROR_REVIT

set "TAA_DOWNLOAD_URL=https://github.com/midka33/Outils-TAA/releases/download/v1.4.1/Outils-TAA_v1.4.1.zip"
set "TAA_SHA_URL=https://github.com/midka33/Outils-TAA/releases/download/v1.4.1/SHA256SUMS.txt"
set "TAA_INSTALL_DIR=%APPDATA%\pyRevit\Extensions"
set "TAA_DEST_DIR=%TAA_INSTALL_DIR%\OutilsTAA.extension"
set "TAA_BACKUP_DIR=%TAA_INSTALL_DIR%\OutilsTAA.extension_backup_v1.4.1_%RANDOM%_%RANDOM%"
set "TAA_TEMP_DIR=%TEMP%\OutilsTAA_v1.4.1_%RANDOM%_%RANDOM%"
mkdir "%TAA_TEMP_DIR%" 2>nul
if errorlevel 1 goto ERROR_DOWNLOAD
echo Telechargement et verification SHA-256 des fichiers...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $t = $env:TAA_TEMP_DIR; $zip = Join-Path $t 'Outils-TAA_v1.4.1.zip'; $sums = Join-Path $t 'SHA256SUMS.txt'; Invoke-WebRequest -UseBasicParsing -Uri $env:TAA_DOWNLOAD_URL -OutFile $zip; Invoke-WebRequest -UseBasicParsing -Uri $env:TAA_SHA_URL -OutFile $sums; $line = Get-Content -LiteralPath $sums | Where-Object { $_ -match 'Outils-TAA_v1[.]4[.]0[.]zip$' } | Select-Object -First 1; if (!$line) { throw 'Somme SHA-256 introuvable' }; $expected = ($line.Trim() -split '\s+')[0].ToLowerInvariant(); $actual = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant(); if ($actual -ne $expected) { throw 'SHA-256 invalide' }; Expand-Archive -LiteralPath $zip -DestinationPath (Join-Path $t 'unpacked') -Force; if (!(Test-Path -LiteralPath (Join-Path $t 'unpacked\OutilsTAA.extension\OutilsTAA.tab\Export.panel'))) { throw 'Archive sans module Export' }; if (!(Test-Path -LiteralPath (Join-Path $t 'unpacked\OutilsTAA.extension\OutilsTAA.tab\PlansDeVente.panel'))) { throw 'Archive sans Plans de vente' }"
if errorlevel 1 goto ERROR_DOWNLOAD

if not exist "%TAA_INSTALL_DIR%" mkdir "%TAA_INSTALL_DIR%" 2>nul
if errorlevel 1 goto ERROR_INSTALL
if exist "%TAA_DEST_DIR%" (
  echo Sauvegarde de l'extension actuelle...
  move "%TAA_DEST_DIR%" "%TAA_BACKUP_DIR%" >nul
  if errorlevel 1 goto ERROR_INSTALL
)
echo Installation de la nouvelle extension...
move "%TAA_TEMP_DIR%\unpacked\OutilsTAA.extension" "%TAA_DEST_DIR%" >nul
if errorlevel 1 goto ERROR_ROLLBACK
if exist "%TAA_TEMP_DIR%" rmdir /s /q "%TAA_TEMP_DIR%" >nul 2>&1
echo.
echo Installation terminee : %TAA_DEST_DIR%
if exist "%TAA_BACKUP_DIR%" echo Sauvegarde : %TAA_BACKUP_DIR%
echo Relancer Revit ou recharger pyRevit.
pause
exit /b 0

:ERROR_ROLLBACK
echo ERREUR : la copie a echoue. Restauration de la version precedente...
if exist "%TAA_BACKUP_DIR%" if not exist "%TAA_DEST_DIR%" move "%TAA_BACKUP_DIR%" "%TAA_DEST_DIR%" >nul
goto ERROR_INSTALL

:ERROR_ENV
echo ERREUR : variables APPDATA ou TEMP introuvables.
goto FAILED
:ERROR_POWERSHELL
echo ERREUR : Windows PowerShell est necessaire.
goto FAILED
:ERROR_REVIT
echo ERREUR : fermez completement Revit avant la mise a jour.
goto FAILED
:ERROR_DOWNLOAD
echo ERREUR : telechargement, verification ou extraction impossible.
echo Aucune ancienne extension n'a ete remplacee.
goto FAILED
:ERROR_INSTALL
echo ERREUR : installation impossible. Controlez les droits utilisateur.
goto FAILED
:FAILED
if defined TAA_TEMP_DIR if exist "%TAA_TEMP_DIR%" rmdir /s /q "%TAA_TEMP_DIR%" >nul 2>&1
pause
exit /b 1
