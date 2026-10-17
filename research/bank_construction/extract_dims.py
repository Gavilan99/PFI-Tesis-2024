# -*- coding: utf-8 -*-
"""Extrae las columnas dimensionales de los specs Likert (Afordancia, Posición,
Origen, Estado, Vínculo, Asimetría, Momento, Tarea relacional) a dims.json.
Sólo dos de los cuatro specs Likert las tienen; la cobertura se informa."""
import io, json, os, re, sys
VAULT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SPECS = [("Spec de Ítems Likert — Armónico (v2, post-auditoría).md", "alik"),
         ("Spec de Ítems Likert — Relaciones Objetales (v2, post-auditoría).md", "rlik"),
         ("Spec de Ítems Likert — Horneviano (v1, reescrito).md", "hlik")]
WANT = ["Afordancia","Posición","Origen","Estado","Vínculo","Asimetría","Momento","Tarea relacional"]
def clean(c): return re.sub(r"[*`\[\]]","",c).strip()
dims={}
for fn,tag in SPECS:
    p=os.path.join(VAULT,fn)
    if not os.path.exists(p): print("FALTA:",fn); continue
    got=0; lines=io.open(p,encoding="utf-8").read().splitlines(); hdr=None; idx={}
    for ln in lines:
        if not ln.strip().startswith("|"): hdr=None; continue
        cells=[clean(c) for c in ln.strip().strip("|").split("|")]
        if set("".join(cells))<=set("-: "): continue
        if hdr is None:
            hdr=cells; idx={w:hdr.index(w) for w in WANT if w in hdr}; continue
        m=re.match(r"\*{0,2}(\d+)",cells[0])
        if not m or not idx: continue
        key=f"{tag} {int(m.group(1)):02d}"
        d=dims.setdefault(key,{})
        for w,i in idx.items():
            if i<len(cells) and cells[i]: d[w]=cells[i]
        got+=1
    print(f"  {os.path.basename(fn)[:56]:56} {got:3d} filas · columnas: {sorted(idx)}")
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"dims.json"),"w",encoding="utf-8").write(
    json.dumps(dims,ensure_ascii=False,indent=1,sort_keys=True))
aff={k:v["Afordancia"] for k,v in dims.items() if v.get("Afordancia")}
io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"afordancia.json"),"w",encoding="utf-8").write(
    json.dumps(aff,ensure_ascii=False,indent=1,sort_keys=True))
print(f"\n  dims: {len(dims)} ítems · afordancia: {len(aff)}")
