#!/usr/bin/env python3
"""PDF Toolkit: ventana con una pestaña por herramienta.

Ejecutar:  python pdf_toolkit.py   (o pythonw para que no se abra la consola)
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from gui_dividir import DividirFrame
from gui_fusionar import FusionarFrame

if sys.platform == "win32":
    # Sin esto, con el escalado de pantalla >100 % Windows estira la ventana y el texto sale borroso
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("PDF Toolkit")
        icono = Path(__file__).parent / "assets" / "pdf_toolkit.ico"
        if sys.platform == "win32" and icono.exists():
            self.iconbitmap(default=str(icono))
        escala = self.winfo_fpixels("1i") / 96  # 1.0 al 100 %, 1.5 al 150 %...
        self.geometry(f"{int(920 * escala)}x{int(580 * escala)}")
        self.minsize(int(760 * escala), int(460 * escala))

        self.pestanas = ttk.Notebook(self)
        self.pestanas.pack(fill="both", expand=True, padx=6, pady=6)
        self.fusionar = FusionarFrame(self.pestanas)
        self.dividir = DividirFrame(self.pestanas)
        self.pestanas.add(self.fusionar, text="  Fusionar  ")
        self.pestanas.add(self.dividir, text="  Dividir  ")


if __name__ == "__main__":
    App().mainloop()
