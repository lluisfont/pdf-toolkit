#!/usr/bin/env python3
"""Divide un PDF en varios.

Modos:
  - Hoja a hoja: un PDF por página, numerado o con un nombre leído de la propia página
    (p. ej. el nombre del alumno en un diploma).
  - Por rangos: un PDF por cada rango indicado.

Ejemplos:
    python pdf_split.py diplomas.pdf --hojas
    python pdf_split.py diplomas.pdf --hojas --nombre-tras "Se otorga el presente diploma a"
    python pdf_split.py libro.pdf --rangos "1-3, 4-6, 7-"
    python pdf_split.py diplomas.pdf --ver-texto 1      # muestra el texto de la página 1
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from pdf_merge import paginas_de_rango

CARACTERES_PROHIBIDOS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class Parte:
    paginas: list[int]  # índices base 0
    archivo: str        # nombre del PDF de salida, con extensión


# ---------- lectura de nombres ----------

def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def lineas_de_pagina(reader: PdfReader, indice: int) -> list[str]:
    """Líneas de texto no vacías de una página (base 0)."""
    texto = reader.pages[indice].extract_text() or ""
    return [l for l in (_normalizar(l) for l in texto.splitlines()) if l]


def nombre_en_lineas(lineas: list[str], ancla: str | None, linea_fija: int | None = None) -> str | None:
    """Busca el nombre en las líneas de una página.

    Con ancla: el nombre es lo que sigue a ese texto en la misma línea o, si no hay nada
    detrás, la siguiente línea; si el ancla no aparece, no hay nombre (mejor numerar que
    adivinar). Sin ancla se usa la línea número linea_fija.
    """
    if ancla:
        ancla_n = _normalizar(ancla).lower()
        for i, linea in enumerate(lineas):
            pos = linea.lower().find(ancla_n)
            if pos == -1:
                continue
            resto = linea[pos + len(ancla_n):].strip(" :,.-")
            if resto:
                # "otorgado a: Luis Gómez, con aprovechamiento" -> "Luis Gómez"
                return resto.split(",")[0].strip()
            if i + 1 < len(lineas):
                return lineas[i + 1].strip(" :,.")
            return None
        return None
    if linea_fija is not None and 0 <= linea_fija < len(lineas):
        return lineas[linea_fija].strip(" :,.")
    return None


def detectar_nombres(reader: PdfReader, ancla: str | None, linea_fija: int | None = None) -> list[str | None]:
    return [nombre_en_lineas(lineas_de_pagina(reader, i), ancla, linea_fija) for i in range(len(reader.pages))]


def limpiar_nombre_archivo(nombre: str) -> str:
    """Quita los caracteres que Windows no admite en nombres de archivo."""
    limpio = CARACTERES_PROHIBIDOS.sub(" - ", nombre)
    return " ".join(limpio.split()).strip(" .")[:150]


def hacer_unicos(nombres: list[str]) -> list[str]:
    """Si dos archivos se llamarían igual, añade (2), (3)... a los repetidos."""
    vistos: dict[str, int] = {}
    resultado = []
    for nombre in nombres:
        clave = nombre.lower()
        vistos[clave] = vistos.get(clave, 0) + 1
        if vistos[clave] > 1:
            base, ext = nombre.rsplit(".", 1)
            nombre = f"{base} ({vistos[clave]}).{ext}"
        resultado.append(nombre)
    return resultado


# ---------- planificación de las partes ----------

def partes_hoja_a_hoja(total: int, base: str, nombres: list[str | None] | None = None) -> list[Parte]:
    """Un PDF por página. Las páginas sin nombre detectado se numeran."""
    ancho = max(3, len(str(total)))
    archivos = []
    for i in range(total):
        nombre = limpiar_nombre_archivo(nombres[i]) if nombres and nombres[i] else ""
        archivos.append(f"{nombre or f'{base}_{i + 1:0{ancho}d}'}.pdf")
    return [Parte([i], a) for i, a in enumerate(hacer_unicos(archivos))]


def partes_por_rangos(texto: str, total: int, base: str) -> list[Parte]:
    """'1-3, 4-6, 7-' -> tres PDF. Cada elemento separado por comas es un archivo."""
    partes = []
    for trozo in (t.strip() for t in texto.split(",")):
        if not trozo:
            continue
        paginas = paginas_de_rango(trozo, total)
        etiqueta = f"{paginas[0] + 1}-{paginas[-1] + 1}" if len(paginas) > 1 else f"{paginas[0] + 1}"
        partes.append(Parte(paginas, f"{base}_pag_{etiqueta}.pdf"))
    if not partes:
        raise ValueError("indica al menos un rango, p. ej. 1-3, 4-6")
    return partes


# ---------- escritura ----------

def dividir(reader: PdfReader, partes: list[Parte], carpeta: Path, informar=print) -> int:
    carpeta.mkdir(parents=True, exist_ok=True)
    for n, parte in enumerate(partes, 1):
        writer = PdfWriter()
        for i in parte.paginas:
            writer.add_page(reader.pages[i])
        with open(carpeta / parte.archivo, "wb") as f:
            writer.write(f)
        informar(f"  [{n}/{len(partes)}] {parte.archivo}")
    return len(partes)


def abrir(ruta: Path, password: str | None) -> PdfReader:
    reader = PdfReader(ruta)
    if reader.is_encrypted and (not password or not reader.decrypt(password)):
        raise PermissionError(f"'{ruta.name}' está protegido: falta la contraseña o no es correcta")
    return reader


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Divide un PDF en varios.")
    parser.add_argument("pdf", help="PDF que se va a dividir")
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--hojas", action="store_true", help="un PDF por página")
    modo.add_argument("--rangos", help="un PDF por rango, p. ej. \"1-3, 4-6, 7-\"")
    modo.add_argument("--ver-texto", type=int, metavar="PAGINA",
                      help="muestra las líneas de texto de una página para elegir el texto de --nombre-tras")
    parser.add_argument("--nombre-tras", metavar="TEXTO",
                        help="con --hojas: nombra cada archivo con lo que sigue a este texto en la página")
    parser.add_argument("-d", "--carpeta", help="carpeta de salida (por defecto: <nombre>_dividido junto al PDF)")
    parser.add_argument("--password", help="contraseña si el PDF está protegido")
    parser.add_argument("-f", "--forzar", action="store_true", help="sobrescribe archivos existentes")
    args = parser.parse_args(argv)

    ruta = Path(args.pdf)
    try:
        reader = abrir(ruta, args.password)
        total = len(reader.pages)

        if args.ver_texto is not None:
            if not 1 <= args.ver_texto <= total:
                raise ValueError(f"la página debe estar entre 1 y {total}")
            for n, linea in enumerate(lineas_de_pagina(reader, args.ver_texto - 1), 1):
                print(f"{n:3d}  {linea}")
            return 0

        if args.hojas:
            nombres = detectar_nombres(reader, args.nombre_tras) if args.nombre_tras else None
            if nombres is not None:
                sin_nombre = [i + 1 for i, n in enumerate(nombres) if not n]
                if sin_nombre:
                    print(f"Aviso: sin nombre en las páginas {sin_nombre}; se numeran.", file=sys.stderr)
            partes = partes_hoja_a_hoja(total, ruta.stem, nombres)
        else:
            partes = partes_por_rangos(args.rangos, total, ruta.stem)
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    carpeta = Path(args.carpeta) if args.carpeta else ruta.with_name(f"{ruta.stem}_dividido")
    existentes = [p.archivo for p in partes if (carpeta / p.archivo).exists()]
    if existentes and not args.forzar:
        print(f"Error: {len(existentes)} archivo(s) ya existen en '{carpeta}'. Usa -f para sobrescribirlos.",
              file=sys.stderr)
        return 1

    print(f"Dividiendo {ruta.name} ({total} páginas) en {len(partes)} archivo(s):")
    dividir(reader, partes, carpeta)
    print(f"Listo: {carpeta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
