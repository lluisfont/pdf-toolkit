"""Pestaña «Fusionar» de PDF Toolkit."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from pypdf import PdfReader

from pdf_merge import RANGO_RE, Entrada, fusionar, orden_natural, paginas_de_rango


class FusionarFrame(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.entradas: dict[str, Entrada] = {}  # iid de la fila -> entrada
        self.arrastrando: str | None = None

        self.var_marcadores = tk.BooleanVar(value=False)
        self.var_password = tk.StringVar()
        self.var_estado = tk.StringVar(value="Añade archivos PDF para empezar.")

        self._construir()

    # ---------- interfaz ----------

    def _construir(self) -> None:
        barra = ttk.Frame(self, padding=(8, 8, 8, 0))
        barra.pack(fill="x")
        ttk.Button(barra, text="Añadir PDF…", command=self.anadir_archivos).pack(side="left")
        ttk.Button(barra, text="Añadir carpeta…", command=self.anadir_carpeta).pack(side="left", padx=4)
        ttk.Button(barra, text="Quitar", command=self.quitar).pack(side="left", padx=(12, 0))
        ttk.Button(barra, text="Vaciar", command=self.vaciar).pack(side="left", padx=4)
        ttk.Button(barra, text="▲ Subir", command=lambda: self.mover(-1)).pack(side="left", padx=(12, 0))
        ttk.Button(barra, text="▼ Bajar", command=lambda: self.mover(1)).pack(side="left", padx=4)
        ttk.Button(barra, text="Ordenar A-Z", command=self.ordenar_nombre).pack(side="left", padx=(12, 0))

        ttk.Label(self, textvariable=self.var_estado, relief="sunken", anchor="w",
                  padding=(6, 2)).pack(fill="x", side="bottom")

        opciones = ttk.Frame(self, padding=8)
        opciones.pack(fill="x", side="bottom")
        ttk.Checkbutton(opciones, text="Un marcador por archivo", variable=self.var_marcadores).pack(side="left")
        ttk.Label(opciones, text="Contraseña (PDF protegidos):").pack(side="left", padx=(16, 4))
        ttk.Entry(opciones, textvariable=self.var_password, show="•", width=16).pack(side="left")
        self.boton_fusionar = ttk.Button(opciones, text="Fusionar…", command=self.fusionar)
        self.boton_fusionar.pack(side="right")

        ttk.Label(self, padding=(8, 0), foreground="gray",
                  text="Arrastra las filas para reordenarlas. Doble clic para elegir páginas (p. ej. 1-3,5,8-)."
                  ).pack(anchor="w", side="bottom")

        marco = ttk.Frame(self, padding=8)
        marco.pack(fill="both", expand=True)
        self.tabla = ttk.Treeview(marco, columns=("archivo", "paginas", "rango", "carpeta"),
                                  show="headings", selectmode="extended")
        for col, titulo, ancho, estirar in [("archivo", "Archivo", 220, True), ("paginas", "Páginas", 70, False),
                                            ("rango", "Rango", 110, False), ("carpeta", "Carpeta", 260, True)]:
            self.tabla.heading(col, text=titulo)
            self.tabla.column(col, width=ancho, stretch=estirar, anchor="center" if not estirar else "w")
        scroll = ttk.Scrollbar(marco, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scroll.set)
        self.tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tabla.bind("<ButtonPress-1>", self._inicio_arrastre)
        self.tabla.bind("<B1-Motion>", self._arrastre)
        self.tabla.bind("<ButtonRelease-1>", lambda e: setattr(self, "arrastrando", None))
        self.tabla.bind("<Double-1>", self.editar_rango)
        self.tabla.bind("<Delete>", lambda e: self.quitar())

    # ---------- lista de archivos ----------

    def _agregar(self, ruta: Path) -> None:
        try:
            reader = PdfReader(ruta)
            paginas = "🔒" if reader.is_encrypted else str(len(reader.pages))
        except Exception:
            messagebox.showwarning("Archivo no válido", f"No se puede leer '{ruta.name}'; se omite.")
            return
        iid = self.tabla.insert("", "end", values=(ruta.name, paginas, "todas", str(ruta.parent)))
        self.entradas[iid] = Entrada(ruta)

    def anadir_archivos(self) -> None:
        rutas = filedialog.askopenfilenames(title="Elige los PDF", filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")])
        for r in rutas:
            self._agregar(Path(r))
        self._actualizar_estado()

    def anadir_carpeta(self) -> None:
        carpeta = filedialog.askdirectory(title="Elige una carpeta con PDF")
        if not carpeta:
            return
        pdfs = sorted((p for p in Path(carpeta).iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
                      key=orden_natural)
        if not pdfs:
            messagebox.showinfo("Sin PDF", "La carpeta no contiene archivos PDF.")
        for p in pdfs:
            self._agregar(p)
        self._actualizar_estado()

    def quitar(self) -> None:
        for iid in self.tabla.selection():
            self.tabla.delete(iid)
            self.entradas.pop(iid, None)
        self._actualizar_estado()

    def vaciar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        self.entradas.clear()
        self._actualizar_estado()

    def mover(self, paso: int) -> None:
        seleccion = list(self.tabla.selection())
        # Al bajar, mover primero las de abajo para que no se adelanten entre sí
        for iid in sorted(seleccion, key=self.tabla.index, reverse=paso > 0):
            nuevo = self.tabla.index(iid) + paso
            if 0 <= nuevo < len(self.tabla.get_children()):
                self.tabla.move(iid, "", nuevo)

    def ordenar_nombre(self) -> None:
        filas = sorted(self.tabla.get_children(), key=lambda i: orden_natural(self.entradas[i].ruta))
        for pos, iid in enumerate(filas):
            self.tabla.move(iid, "", pos)

    def _inicio_arrastre(self, evento: tk.Event) -> None:
        self.arrastrando = self.tabla.identify_row(evento.y) or None

    def _arrastre(self, evento: tk.Event) -> None:
        destino = self.tabla.identify_row(evento.y)
        if self.arrastrando and destino and destino != self.arrastrando:
            self.tabla.move(self.arrastrando, "", self.tabla.index(destino))

    def editar_rango(self, evento: tk.Event | None = None) -> None:
        iid = self.tabla.identify_row(evento.y) if evento else (self.tabla.selection() or [None])[0]
        if not iid:
            return
        entrada = self.entradas[iid]
        nuevo = simpledialog.askstring(
            "Páginas", f"Páginas de '{entrada.ruta.name}' (vacío = todas).\nEjemplos: 1-3,5   8-   3,1",
            initialvalue=entrada.rango or "", parent=self)
        if nuevo is None:
            return
        nuevo = nuevo.strip()
        if nuevo and not RANGO_RE.match(nuevo):
            messagebox.showerror("Rango no válido", f"'{nuevo}' no es un rango válido.")
            return
        total = self.tabla.set(iid, "paginas")
        if nuevo and total.isdigit():
            try:
                paginas_de_rango(nuevo, int(total))
            except ValueError as e:
                messagebox.showerror("Rango no válido", str(e))
                return
        entrada.rango = nuevo or None
        self.tabla.set(iid, "rango", nuevo or "todas")

    def _actualizar_estado(self) -> None:
        n = len(self.tabla.get_children())
        self.var_estado.set(f"{n} archivo(s) en la lista." if n else "Añade archivos PDF para empezar.")

    # ---------- fusión ----------

    def _progreso(self, texto: str) -> None:
        self.var_estado.set("Fusionando… " + texto.strip(" +"))
        self.update_idletasks()

    def fusionar(self) -> None:
        orden = [self.entradas[i] for i in self.tabla.get_children()]
        if not orden:
            messagebox.showinfo("Nada que fusionar", "Añade al menos un PDF.")
            return
        destino = filedialog.asksaveasfilename(title="Guardar PDF fusionado", defaultextension=".pdf",
                                               initialfile="fusionado.pdf", filetypes=[("PDF", "*.pdf")])
        if not destino:
            return
        salida = Path(destino)
        if any(e.ruta.resolve() == salida.resolve() for e in orden):
            messagebox.showerror("Destino no válido", "El archivo de salida no puede ser uno de los de entrada.")
            return

        ventana = self.winfo_toplevel()
        self.boton_fusionar.state(["disabled"])
        ventana.config(cursor="watch")
        self.var_estado.set("Fusionando…")
        self.update_idletasks()
        try:
            total = fusionar(orden, salida, self.var_marcadores.get(), self.var_password.get() or None,
                             informar=self._progreso)
        except Exception as e:
            self.var_estado.set("Error al fusionar.")
            messagebox.showerror("Error", str(e))
            return
        finally:
            self.boton_fusionar.state(["!disabled"])
            ventana.config(cursor="")
        self.var_estado.set(f"Listo: {salida} ({total} páginas)")
        messagebox.showinfo("Listo", f"PDF creado con {total} páginas:\n{salida}")
