"""Pestaña «Dividir» de PDF Toolkit."""

from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from pypdf import PdfReader

from pdf_split import (Parte, dividir, hacer_unicos, limpiar_nombre_archivo, lineas_de_pagina,
                       nombre_en_lineas, partes_hoja_a_hoja, partes_por_rangos)


class DividirFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.ruta: Path | None = None
        self.reader: PdfReader | None = None
        self.lineas: list[list[str] | None] = []  # texto de cada página, leído bajo demanda
        self.linea_fija: int | None = None        # línea del nombre elegida con clic (respaldo del ancla)
        self.partes: list[Parte] = []

        self.var_pdf = tk.StringVar()
        self.var_info = tk.StringVar()
        self.var_modo = tk.StringVar(value="hojas")
        self.var_nombrar = tk.StringVar(value="numerar")
        self.var_ancla = tk.StringVar()
        self.var_rangos = tk.StringVar()
        self.var_carpeta = tk.StringVar()
        self.var_estado = tk.StringVar(value="Elige el PDF que quieres dividir.")

        self._construir()
        self._cambiar_modo()

    # ---------- interfaz ----------

    def _construir(self) -> None:
        arriba = ttk.Frame(self, padding=(8, 8, 8, 0))
        arriba.pack(fill="x")
        ttk.Label(arriba, text="PDF:").pack(side="left")
        ttk.Entry(arriba, textvariable=self.var_pdf, state="readonly").pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(arriba, text="Elegir…", command=self.elegir_pdf).pack(side="left")
        ttk.Label(arriba, textvariable=self.var_info, width=12, anchor="e").pack(side="left", padx=(8, 0))

        ttk.Label(self, textvariable=self.var_estado, relief="sunken", anchor="w",
                  padding=(6, 2)).pack(fill="x", side="bottom")

        abajo = ttk.Frame(self, padding=8)
        abajo.pack(fill="x", side="bottom")
        ttk.Label(abajo, text="Guardar en:").pack(side="left")
        ttk.Entry(abajo, textvariable=self.var_carpeta).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(abajo, text="Elegir…", command=self.elegir_carpeta).pack(side="left")
        self.boton_dividir = ttk.Button(abajo, text="Dividir", command=self.dividir)
        self.boton_dividir.pack(side="left", padx=(16, 0))

        cuerpo = ttk.Frame(self, padding=(8, 8, 8, 0))
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1, uniform="col")
        cuerpo.columnconfigure(1, weight=1, uniform="col")
        cuerpo.rowconfigure(0, weight=1)

        # --- columna izquierda: cómo dividir ---
        izq = ttk.Frame(cuerpo)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        modo = ttk.LabelFrame(izq, text="Cómo dividir", padding=6)
        modo.pack(fill="x")
        ttk.Radiobutton(modo, text="Hoja a hoja (un PDF por página)", value="hojas",
                        variable=self.var_modo, command=self._cambiar_modo).pack(anchor="w")
        ttk.Radiobutton(modo, text="Por rangos (un PDF por rango)", value="rangos",
                        variable=self.var_modo, command=self._cambiar_modo).pack(anchor="w")

        # Opciones de «hoja a hoja»
        self.marco_hojas = ttk.LabelFrame(izq, text="Nombre de cada archivo", padding=6)
        ttk.Radiobutton(self.marco_hojas, text="Numerados (documento_001.pdf…)", value="numerar",
                        variable=self.var_nombrar, command=self._cambiar_modo).pack(anchor="w")
        ttk.Radiobutton(self.marco_hojas, text="Con un nombre leído de la página (p. ej. el alumno)",
                        value="leer", variable=self.var_nombrar, command=self._cambiar_modo).pack(anchor="w")
        self.marco_leer = ttk.Frame(self.marco_hojas)
        ttk.Label(self.marco_leer, foreground="gray", wraplength=360, justify="left",
                  text="Haz clic en la línea donde está el nombre. Se usa el texto que va justo "
                       "antes como referencia en todas las páginas.").pack(anchor="w", pady=(6, 2))
        lista = ttk.Frame(self.marco_leer)
        lista.pack(fill="both", expand=True)
        self.lista_lineas = tk.Listbox(lista, height=7, activestyle="none", exportselection=False)
        scroll = ttk.Scrollbar(lista, orient="vertical", command=self.lista_lineas.yview)
        self.lista_lineas.configure(yscrollcommand=scroll.set)
        self.lista_lineas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.lista_lineas.bind("<<ListboxSelect>>", self._linea_elegida)
        fila = ttk.Frame(self.marco_leer)
        fila.pack(fill="x", pady=(6, 0))
        ttk.Label(fila, text="Texto antes del nombre:").pack(side="left")
        entrada = ttk.Entry(fila, textvariable=self.var_ancla)
        entrada.pack(side="left", fill="x", expand=True, padx=4)
        entrada.bind("<Return>", lambda e: self.actualizar_vista())
        ttk.Button(fila, text="Detectar", command=self.actualizar_vista).pack(side="left")

        # Opciones de «por rangos»
        self.marco_rangos = ttk.LabelFrame(izq, text="Rangos", padding=6)
        ttk.Label(self.marco_rangos, foreground="gray", wraplength=360, justify="left",
                  text="Un archivo por cada rango, separados por comas.\n"
                       "Ejemplo: 1-3, 4-6, 7-   (7- = de la 7 al final)").pack(anchor="w")
        entrada = ttk.Entry(self.marco_rangos, textvariable=self.var_rangos)
        entrada.pack(fill="x", pady=(4, 0))
        entrada.bind("<KeyRelease>", lambda e: self.actualizar_vista())

        # --- columna derecha: vista previa ---
        der = ttk.LabelFrame(cuerpo, text="Vista previa (doble clic para cambiar un nombre)", padding=6)
        der.grid(row=0, column=1, sticky="nsew")
        self.tabla = ttk.Treeview(der, columns=("paginas", "archivo"), show="headings", selectmode="browse")
        self.tabla.heading("paginas", text="Páginas")
        self.tabla.heading("archivo", text="Archivo de salida")
        self.tabla.column("paginas", width=70, stretch=False, anchor="center")
        self.tabla.column("archivo", width=260)
        self.tabla.tag_configure("sin_nombre", foreground="#b35c00")
        scroll = ttk.Scrollbar(der, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tabla.bind("<Double-1>", self.renombrar)

    def _cambiar_modo(self) -> None:
        self.marco_hojas.pack_forget()
        self.marco_rangos.pack_forget()
        self.marco_leer.pack_forget()
        if self.var_modo.get() == "hojas":
            self.marco_hojas.pack(fill="both", expand=True, pady=(8, 0))
            if self.var_nombrar.get() == "leer":
                self.marco_leer.pack(fill="both", expand=True)
        else:
            self.marco_rangos.pack(fill="x", pady=(8, 0))
        self.actualizar_vista()

    # ---------- carga del PDF ----------

    def elegir_pdf(self) -> None:
        ruta = filedialog.askopenfilename(title="Elige el PDF que quieres dividir",
                                          filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        if ruta:
            self.cargar(Path(ruta))

    def cargar(self, ruta: Path) -> None:
        try:
            reader = PdfReader(ruta)
            if reader.is_encrypted:
                clave = simpledialog.askstring("PDF protegido", f"Contraseña de '{ruta.name}':",
                                               show="•", parent=self)
                if not clave or not reader.decrypt(clave):
                    messagebox.showerror("PDF protegido", "Falta la contraseña o no es correcta.")
                    return
            total = len(reader.pages)
        except Exception as e:
            messagebox.showerror("Archivo no válido", f"No se puede leer '{ruta.name}':\n{e}")
            return

        self.ruta, self.reader = ruta, reader
        self.lineas = [None] * total
        self.linea_fija = None
        self.var_ancla.set("")
        self.var_pdf.set(str(ruta))
        self.var_info.set(f"{total} páginas")
        self.var_carpeta.set(str(ruta.with_name(f"{ruta.stem}_dividido")))

        self.lista_lineas.delete(0, "end")
        primera = self._lineas(0)
        for linea in primera:
            self.lista_lineas.insert("end", linea)
        if not primera:
            self.lista_lineas.insert("end", "(la página 1 no tiene texto: ¿es un PDF escaneado?)")
        self.actualizar_vista()

    def _lineas(self, indice: int) -> list[str]:
        if self.lineas[indice] is None:
            self.lineas[indice] = lineas_de_pagina(self.reader, indice)
        return self.lineas[indice]

    def _linea_elegida(self, _evento: tk.Event) -> None:
        seleccion = self.lista_lineas.curselection()
        if not seleccion or not self.reader or not self._lineas(0):
            return
        k = seleccion[0]
        self.linea_fija = k
        self.var_ancla.set(self._lineas(0)[k - 1] if k > 0 else "")
        self.actualizar_vista()

    def elegir_carpeta(self) -> None:
        carpeta = filedialog.askdirectory(title="Carpeta donde guardar los PDF")
        if carpeta:
            self.var_carpeta.set(carpeta)

    # ---------- vista previa ----------

    def actualizar_vista(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        self.partes = []
        if not self.reader:
            return
        total, base = len(self.reader.pages), self.ruta.stem
        sin_nombre: list[int] = []
        try:
            if self.var_modo.get() == "rangos":
                if not self.var_rangos.get().strip():
                    self.var_estado.set("Escribe los rangos, p. ej. 1-3, 4-6, 7-")
                    return
                self.partes = partes_por_rangos(self.var_rangos.get(), total, base)
            elif self.var_nombrar.get() == "leer":
                ancla = self.var_ancla.get().strip()
                if not ancla and self.linea_fija is None:
                    self.var_estado.set("Haz clic en la línea del nombre o escribe el texto que va antes.")
                    return
                self._ocupado(True)
                nombres = []
                for i in range(total):
                    nombres.append(nombre_en_lineas(self._lineas(i), ancla, self.linea_fija))
                    if i % 20 == 0:
                        self.var_estado.set(f"Leyendo nombres… página {i + 1} de {total}")
                        self.update_idletasks()
                sin_nombre = [i for i, n in enumerate(nombres) if not n]
                self.partes = partes_hoja_a_hoja(total, base, nombres)
            else:
                self.partes = partes_hoja_a_hoja(total, base)
        except ValueError as e:
            self.var_estado.set(f"Rango no válido: {e}")
            return
        finally:
            self._ocupado(False)

        for parte in self.partes:
            paginas = parte.paginas
            etiqueta = str(paginas[0] + 1) if len(paginas) == 1 else f"{paginas[0] + 1}-{paginas[-1] + 1}"
            tags = ("sin_nombre",) if len(paginas) == 1 and paginas[0] in sin_nombre else ()
            self.tabla.insert("", "end", values=(etiqueta, parte.archivo), tags=tags)

        texto = f"Se crearán {len(self.partes)} archivo(s)."
        if sin_nombre:
            texto += f" {len(sin_nombre)} página(s) sin nombre detectado (en naranja): se numeran."
        self.var_estado.set(texto)

    def renombrar(self, evento: tk.Event) -> None:
        iid = self.tabla.identify_row(evento.y)
        if not iid:
            return
        n = self.tabla.index(iid)
        actual = self.partes[n].archivo.removesuffix(".pdf")
        nuevo = simpledialog.askstring("Nombre del archivo", "Nombre (sin .pdf):", initialvalue=actual, parent=self)
        if not nuevo or not limpiar_nombre_archivo(nuevo):
            return
        self.partes[n].archivo = limpiar_nombre_archivo(nuevo) + ".pdf"
        self.tabla.set(iid, "archivo", self.partes[n].archivo)
        self.tabla.item(iid, tags=())

    # ---------- división ----------

    def _ocupado(self, si: bool) -> None:
        self.winfo_toplevel().config(cursor="watch" if si else "")
        self.boton_dividir.state(["disabled"] if si else ["!disabled"])
        self.update_idletasks()

    def dividir(self) -> None:
        if not self.partes:
            messagebox.showinfo("Nada que dividir", "Elige un PDF y cómo dividirlo.")
            return
        archivos = [p.archivo for p in self.partes]
        if len({a.lower() for a in archivos}) != len(archivos):
            # Puede pasar tras renombrar a mano: se desambiguan antes de escribir
            for parte, unico in zip(self.partes, hacer_unicos(archivos)):
                parte.archivo = unico
        carpeta = Path(self.var_carpeta.get().strip() or self.ruta.with_name(f"{self.ruta.stem}_dividido"))
        existentes = [p.archivo for p in self.partes if (carpeta / p.archivo).exists()]
        if existentes and not messagebox.askyesno(
                "Archivos existentes", f"{len(existentes)} archivo(s) ya existen en:\n{carpeta}\n\n¿Sobrescribirlos?"):
            return

        self._ocupado(True)
        try:
            n = dividir(self.reader, self.partes, carpeta, informar=self._progreso)
        except Exception as e:
            self.var_estado.set("Error al dividir.")
            messagebox.showerror("Error", str(e))
            return
        finally:
            self._ocupado(False)
        self.var_estado.set(f"Listo: {n} archivo(s) en {carpeta}")
        if messagebox.askyesno("Listo", f"Se han creado {n} archivo(s) en:\n{carpeta}\n\n¿Abrir la carpeta?") \
                and sys.platform == "win32":
            os.startfile(carpeta)

    def _progreso(self, texto: str) -> None:
        self.var_estado.set("Dividiendo… " + texto.strip())
        self.update_idletasks()
