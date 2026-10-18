#!/usr/bin/env python3
"""
Write SYNTHETIC model artifacts for development and tests: the real training on fake respondents.

    python scripts/make_dev_artifacts.py --out C:\\tmp\\nureon-artifacts

Runs Tobi's training (`app.ml.training.train`) over the real bank
(`research/bank/NureonAI Prototype v4.1.2.csv`) with synthetic respondents (scripts/synthetic_pilot.py),
few trees and one repetition. The output has exactly the shape of the real artifacts (cut_040/,
cut_090/, cut_145/, manifest.json, precision_by_items.json), so the cut plan and the `trained`
classifier load it as they would the real one.

What comes out is not a model of anyone: its `model_version` starts with `synthetic-`, and the app
refuses to start in production with it. The real artifacts arrive after the pilot cut of 18/10 and
never enter the repository; neither does this output (never write it to app/ml/artifacts/ unless you
know it stays local).
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run as a file from backend/

from app.ml.training import train as training  # noqa: E402
from app.ml.training.bank import load_bank  # noqa: E402
from scripts._db import utf8_output  # noqa: E402
from scripts.synthetic_pilot import write_people  # noqa: E402

BANK_CSV = Path(__file__).resolve().parents[2] / "research" / "bank" / "NureonAI Prototype v4.1.2.csv"
SYNTHETIC_PREFIX = "synthetic-"
RESPONDENTS = 90
TREES = 25


def make(out: Path, *, bank: Path = BANK_CSV, respondents: int = RESPONDENTS, trees: int = TREES,
         quiet: bool = False) -> str:
    """Train on synthetic respondents into `out` and mark the result synthetic. Returns its version."""
    items = load_bank(bank)
    original_trees = training.N_TREES
    training.N_TREES = trees
    try:
        with tempfile.TemporaryDirectory(prefix="nureon-synthetic-pilot-") as tmp:
            responses, labels = write_people(Path(tmp), items, n=respondents)
            argv = ["--bank", str(bank), "--responses", str(responses), "--labels", str(labels),
                    "--out", str(out), "--reps", "1"]
            if quiet:
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    code = training.main(argv)
            else:
                code = training.main(argv)
    finally:
        training.N_TREES = original_trees
    if code != 0:
        raise RuntimeError(f"the training exited with {code}")

    version = None
    for name in ("manifest.json", "precision_by_items.json"):
        path = out / name
        data = json.loads(path.read_text(encoding="utf-8"))
        version = (SYNTHETIC_PREFIX + data["model_version"])[:64]
        data["model_version"] = version
        data["synthetic"] = "Artefacto sintético para desarrollo y tests: respondentes inventados. No es un modelo."
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera artefactos sintéticos de los modelos por cortes.")
    parser.add_argument("--out", required=True, help="Carpeta de salida (se crea si no existe).")
    parser.add_argument("--respondents", type=int, default=RESPONDENTS)
    parser.add_argument("--trees", type=int, default=TREES)
    args = parser.parse_args(argv)
    utf8_output()
    out = Path(args.out)
    if out.resolve() == (Path(__file__).resolve().parents[1] / "app" / "ml" / "artifacts").resolve():
        print("Aviso: escribís artefactos SINTÉTICOS en app/ml/artifacts/. No los subas ni los uses en "
              "una imagen: en producción la app no arranca con ellos.", file=sys.stderr)
    version = make(out, respondents=args.respondents, trees=args.trees)
    print(f"\nArtefactos SINTÉTICOS en {out} · model_version {version}")
    print("No son un modelo: respondentes inventados. En producción la app se niega a arrancar con ellos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
