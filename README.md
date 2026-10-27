# PDF-Toolkit

```bash
pip install -r requirements.txt
```

## Ventana (pdf_toolkit.py)

```bash
pythonw pdf_toolkit.py
```

(`pythonw` no abre consola; `python` también funciona.)

**Acceso directo** (Windows): para abrirla con doble clic desde el escritorio o el menú Inicio, sin consola ni terminal, ejecuta una vez:

```bash
python crear_acceso_directo.py
```

Crea «PDF Toolkit» (con su icono) en el escritorio y en el menú Inicio; desde ahí se puede anclar a la barra de tareas. Usa el Python con el que lo ejecutes y el código de esta carpeta, así que siempre abre la versión actual. Vuelve a ejecutarlo si mueves la carpeta o cambias de Python.

Una pestaña por herramienta:

### Fusionar

- **Añadir PDF… / Añadir carpeta…**: carga archivos; los de una carpeta entran en orden natural.
- **Reordenar**: arrastra las filas, o usa ▲ Subir / ▼ Bajar (admite selección múltiple) u **Ordenar A-Z**.
- **Doble clic** en una fila: elige las páginas de ese archivo (`1-3,5`, `8-`, `3,1`…); vacío = todas.
- **Quitar** (o tecla Supr) y **Vaciar** limpian la lista.
- Los PDF protegidos aparecen con 🔒; escribe su contraseña en el campo de abajo antes de fusionar.
- **Fusionar…** pide dónde guardar el resultado.

### Dividir

1. **Elegir…** el PDF (si está protegido, pide la contraseña).
2. **Cómo dividir**:
   - **Hoja a hoja**: un PDF por página.
     - *Numerados*: `diplomas_001.pdf`, `diplomas_002.pdf`…
     - *Con un nombre leído de la página* (diplomas): aparece el texto de la página 1; **haz clic en la línea del alumno**. El texto que va justo antes (p. ej. «Se otorga el presente diploma a») se usa como referencia para encontrar el nombre en todas las páginas. También puedes escribirlo a mano en «Texto antes del nombre»; si el nombre va en la misma línea («otorgado a: Luis Gómez, con…»), escribe «otorgado a» y se toma lo que sigue hasta la coma.
   - **Por rangos**: `1-3, 4-6, 7-` → un PDF por rango.
3. Revisa la **vista previa**. Las páginas donde no se encontró nombre salen en naranja y se numeran. Doble clic en una fila para cambiar el nombre.
4. **Dividir**. Por defecto guarda en `<nombre>_dividido`, junto al PDF original. Los nombres repetidos reciben `(2)`, `(3)`… y los caracteres no válidos en Windows se sustituyen.

Solo funciona con PDF que tengan texto; en un PDF escaneado (imagen) no hay nombres que leer.

## Documentación con OpenSpec

El comportamiento de cada funcionalidad está descrito en `openspec/specs/` (`pdf-merge`, `pdf-split`, `desktop-app`). Para cualquier cambio nuevo, en Claude Code:

1. `/opsx:explore` — pensar la idea sin tocar código (opcional).
2. `/opsx:propose <idea>` — crea `openspec/changes/<cambio>/` con propuesta, diseño, tareas y los requisitos nuevos o modificados.
3. `/opsx:apply` — implementa las tareas.
4. `/opsx:archive` — incorpora los requisitos a `openspec/specs/` y archiva el cambio.

Comprobar que todo está bien formado: `openspec validate --all --strict`. Ver el estado: `openspec list --specs` u `openspec view`.

## Línea de comandos

### pdf_merge.py — fusionar

```bash
python pdf_merge.py a.pdf b.pdf c.pdf -o resultado.pdf
```

| Uso | Ejemplo |
|---|---|
| Archivos en el orden indicado | `python pdf_merge.py portada.pdf informe.pdf -o final.pdf` |
| Todos los PDF de una carpeta (orden natural: `doc2` antes que `doc10`) | `python pdf_merge.py .\facturas -o facturas.pdf` |
| Carpeta ordenada por fecha de modificación | `python pdf_merge.py .\escaneos --orden fecha -o todo.pdf` |
| Solo algunas páginas (base 1) | `python pdf_merge.py informe.pdf:1-3,5 anexo.pdf:2- -o final.pdf` |
| Un marcador por archivo de origen | `python pdf_merge.py .\capitulos --marcadores -o libro.pdf` |
| PDF protegidos | `python pdf_merge.py privado.pdf otro.pdf --password miclave -o final.pdf` |
| Sobrescribir la salida | `-f` |

Rangos: `1-3` (de la 1 a la 3), `5` (solo la 5), `8-` (de la 8 al final), `-3` (de la 1 a la 3). Se pueden repetir o reordenar: `doc.pdf:3,1`.

### pdf_split.py — dividir

| Uso | Ejemplo |
|---|---|
| Hoja a hoja, numerados | `python pdf_split.py diplomas.pdf --hojas` |
| Ver el texto de una página para elegir la referencia | `python pdf_split.py diplomas.pdf --ver-texto 1` |
| Hoja a hoja con el nombre del alumno | `python pdf_split.py diplomas.pdf --hojas --nombre-tras "Se otorga el presente diploma a"` |
| Por rangos | `python pdf_split.py libro.pdf --rangos "1-3, 4-6, 7-"` |
| Otra carpeta de salida / sobrescribir | `-d .\salida` / `-f` |
