#!/usr/bin/env python3
"""Fusiona varios PDF en uno solo.

Ejemplos:
    python pdf_merge.py a.pdf b.pdf c.pdf -o resultado.pdf
    python pdf_merge.py carpeta_con_pdfs -o resultado.pdf
    python pdf_merge.py informe.pdf:1-3,5 anexo.pdf:2- -o final.pdf --marcadores
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter

RANGO_RE = re.compile(r"^\s*\d*\s*(-\s*\d*\s*)?(,\s*\d*\s*(-\s*\d*\s*)?)*$")


@dataclass
class Entrada:
    ruta: Path
    rango: str | None = None  # p. ej. "1-3,5,8-"; None = todas las páginas


def orden_natural(ruta: Path) -> list:
    """Ordena 'doc2' antes que 'doc10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", ruta.name)]


def separar_rango(arg: str) -> Entrada:
    """Separa 'archivo.pdf:1-3,5' en ruta y rango. Respeta letras de unidad (C:\\...)."""
    if Path(arg).exists():
        return Entrada(Path(arg))
    if ":" in arg:
        ruta, rango = arg.rsplit(":", 1)
        if rango and RANGO_RE.match(rango) and Path(ruta).exists():
            return Entrada(Path(ruta), rango)
    return Entrada(Path(arg))


def paginas_de_rango(rango: str, total: int) -> list[int]:
    """Convierte '1-3,5,8-' (base 1) en índices base 0. '8-' llega hasta el final, '-3' desde el inicio."""
    paginas: list[int] = []
    for parte in rango.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            ini_txt, fin_txt = (p.strip() for p in parte.split("-", 1))
            ini = int(ini_txt) if ini_txt else 1
            fin = int(fin_txt) if fin_txt else total
        else:
            ini = fin = int(parte)
        if ini < 1 or fin > total or ini > fin:
            raise ValueError(f"rango '{parte}' fuera de límites (el documento tiene {total} páginas)")
        paginas.extend(range(ini - 1, fin))
    return paginas


def expandir_entradas(args: list[str], orden: str, salida: Path) -> list[Entrada]:
    entradas: list[Entrada] = []
    for arg in args:
        entrada = separar_rango(arg)
        if entrada.ruta.is_dir():
            pdfs = [p for p in entrada.ruta.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
            pdfs = [p for p in pdfs if p.resolve() != salida.resolve()]
            if orden == "fecha":
                pdfs.sort(key=lambda p: p.stat().st_mtime)
            else:
                pdfs.sort(key=orden_natural)
            if not pdfs:
                print(f"Aviso: la carpeta '{entrada.ruta}' no contiene PDF.", file=sys.stderr)
            entradas.extend(Entrada(p) for p in pdfs)
        elif entrada.ruta.is_file():
            entradas.append(entrada)
        else:
            raise FileNotFoundError(f"no existe: {arg}")
    return entradas


def fusionar(entradas: list[Entrada], salida: Path, marcadores: bool, password: str | None,
             informar=print) -> int:
    writer = PdfWriter()
    total_paginas = 0
    for entrada in entradas:
        reader = PdfReader(entrada.ruta)
        if reader.is_encrypted:
            if not password or not reader.decrypt(password):
                raise PermissionError(f"'{entrada.ruta.name}' está protegido: falta la contraseña o no es correcta")
        n = len(reader.pages)
        paginas = paginas_de_rango(entrada.rango, n) if entrada.rango else list(range(n))
        writer.append(
            reader,
            pages=paginas,
            outline_item=entrada.ruta.stem if marcadores else None,
            import_outline=not marcadores,
        )
        total_paginas += len(paginas)
        informar(f"  + {entrada.ruta.name}: {len(paginas)} de {n} páginas")

    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "wb") as f:
        writer.write(f)
    writer.close()
    return total_paginas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fusiona varios PDF en uno solo.",
        epilog="Rangos de páginas: añade ':1-3,5,8-' al nombre del archivo (base 1).",
    )
    parser.add_argument("entradas", nargs="+", help="archivos PDF y/o carpetas, en el orden deseado")
    parser.add_argument("-o", "--salida", default="fusionado.pdf", help="archivo de salida (por defecto: fusionado.pdf)")
    parser.add_argument("--orden", choices=["nombre", "fecha"], default="nombre",
                        help="orden de los PDF dentro de una carpeta (por defecto: nombre natural)")
    parser.add_argument("--marcadores", action="store_true", help="añade un marcador por cada archivo de origen")
    parser.add_argument("--password", help="contraseña para PDF protegidos")
    parser.add_argument("-f", "--forzar", action="store_true", help="sobrescribe la salida si ya existe")
    args = parser.parse_args(argv)

    salida = Path(args.salida)
    if salida.suffix.lower() != ".pdf":
        salida = salida.with_suffix(".pdf")
    if salida.exists() and not args.forzar:
        print(f"Error: '{salida}' ya existe. Usa -f para sobrescribirlo.", file=sys.stderr)
        return 1

    try:
        entradas = expandir_entradas(args.entradas, args.orden, salida)
        if not entradas:
            print("Error: no hay PDF que fusionar.", file=sys.stderr)
            return 1
        print(f"Fusionando {len(entradas)} archivo(s):")
        total = fusionar(entradas, salida, args.marcadores, args.password)
    except PermissionError as e:
        print(f"Error: {e} (usa --password)", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Listo: {salida} ({total} páginas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
