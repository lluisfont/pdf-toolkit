#!/usr/bin/env python3
"""Crea el acceso directo «PDF Toolkit» en el escritorio y en el menú Inicio (Windows).

El acceso directo abre la ventana con pythonw (sin consola), usando el Python que ejecuta
este script y el código de esta carpeta. Vuelve a ejecutarlo si mueves la carpeta del
proyecto o cambias de Python:

    python crear_acceso_directo.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROYECTO = Path(__file__).resolve().parent

# PowerShell en línea (no le afecta la política de ejecución de scripts); recibe los datos por
# variables de entorno para no tener que escapar comillas en las rutas.
CREAR_LNK = r"""
$shell = New-Object -ComObject WScript.Shell
foreach ($carpeta in [Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs')) {
    $ruta = Join-Path $carpeta 'PDF Toolkit.lnk'
    $acceso = $shell.CreateShortcut($ruta)
    $acceso.TargetPath = $env:PDFTK_PYTHONW
    $acceso.Arguments = '"' + $env:PDFTK_PROGRAMA + '"'
    $acceso.WorkingDirectory = $env:PDFTK_PROYECTO
    $acceso.IconLocation = $env:PDFTK_ICONO + ',0'
    $acceso.Description = 'Fusionar y dividir PDF'
    $acceso.Save()
    Write-Output $ruta
}
"""


def main() -> int:
    if sys.platform != "win32":
        print("Este script solo sirve en Windows.", file=sys.stderr)
        return 1
    try:
        import pypdf  # noqa: F401
        import tkinter  # noqa: F401
    except ImportError as e:
        print(f"Este Python no tiene {e.name}. Instálalo con: pip install -r requirements.txt", file=sys.stderr)
        return 1
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.exists():
        print(f"No se encuentra {pythonw}.", file=sys.stderr)
        return 1

    entorno = dict(os.environ,
                   PDFTK_PYTHONW=str(pythonw),
                   PDFTK_PROGRAMA=str(PROYECTO / "pdf_toolkit.py"),
                   PDFTK_PROYECTO=str(PROYECTO),
                   PDFTK_ICONO=str(PROYECTO / "assets" / "pdf_toolkit.ico"))
    resultado = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", CREAR_LNK],
                               env=entorno, capture_output=True, text=True)
    if resultado.returncode != 0:
        print(f"Error al crear el acceso directo:\n{resultado.stderr}", file=sys.stderr)
        return 1
    for ruta in resultado.stdout.split("\n"):
        if ruta.strip():
            print(f"Creado: {ruta.strip()}")
    print(f"Abre la ventana con: {pythonw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
