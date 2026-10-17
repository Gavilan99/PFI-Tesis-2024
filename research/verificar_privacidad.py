# -*- coding: utf-8 -*-
"""Chequeo antes de subir research/ al repositorio público.

    python research/verificar_privacidad.py

Falla (código 1) si encuentra, en cualquier archivo de texto de research/ fuera de las carpetas de
datos: un código de respondente (R seguido de tres dígitos, salvo el ejemplo R017 del formulario),
una dirección de email, o un archivo de datos que el .gitignore debería estar bloqueando.
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
CODIGO = re.compile(r"\bR(?!017\b)\d{3}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
TEXTO = (".py", ".gs", ".json", ".csv", ".md", ".txt")
DATOS = re.compile(r"(responses|respuestas|tipificaciones|version_por_respondente).*\.csv$|code_fixes\.json$|"
                   r"excluidos\.txt$|_vistos\.txt$|e3_entrenamiento\.txt$|\.xlsx$")
SALTEAR = {"data", "__pycache__", ".git"}


def main():
    problemas = []
    for d, sub, files in os.walk(RAIZ):
        sub[:] = [s for s in sub if s not in SALTEAR and "_out" not in s]
        for f in files:
            p = os.path.join(d, f); rel = os.path.relpath(p, RAIZ)
            if DATOS.search(f):
                problemas.append(f"{rel}: archivo de datos fuera de data/")
                continue
            if not f.endswith(TEXTO) or f == os.path.basename(__file__):
                continue
            for n, linea in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                if CODIGO.search(linea):
                    problemas.append(f"{rel}:{n}: código de respondente → {linea.strip()[:80]}")
                if EMAIL.search(linea):
                    problemas.append(f"{rel}:{n}: email → {linea.strip()[:80]}")
    if problemas:
        print("NO SUBIR. Problemas encontrados:")
        print("\n".join("  " + x for x in problemas))
        return 1
    print("OK: ningún código de respondente, email ni archivo de datos en research/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
