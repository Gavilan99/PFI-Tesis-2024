# research/ — banco de preguntas y piloto de NureonAI

Código con el que se construyó el banco de preguntas y se analizó el piloto de entrenamiento. **No contiene datos de ninguna persona.**

| Carpeta | Contenido |
|---|---|
| `bank/` | El banco: v4.1 *(base)*, v4.1.1 y v4.1.2 *(redacción vigente, la que carga el producto)*, y `bank_aliases.json` *(redacciones anteriores de las opciones reescritas, para leer el export del formulario)* |
| `bank_construction/` | Generadores y chequeos del banco: redacción por conjunto, chequeos de vecindad y solapamiento, palabras vetadas, nivel, tildes, facetas. Se conservan tal como se usaron, como registro de cómo se construyó el banco; esperan la estructura de carpetas original del proyecto |
| `pilot/` | Lectura del formulario *(`parse_form_export.py`, `make_form.gs`)*, métricas de cada corte *(`pilot_metrics.py`, `contrast.py`)*, protocolo de entrenamiento registrado *(`train_pilot.py`)* y análisis exploratorios y del modelo |

## Datos privados

Los scripts de `pilot/` leen y escriben en una **carpeta de datos fuera del repositorio**. Se indica con la variable de entorno `NUREON_DATA`; por defecto es `research/pilot/data/`, que el `.gitignore` bloquea. Ahí van:

- `responses_wide.csv` y `responses_version.csv` *(salida de `parse_form_export.py`)*;
- `Piloto B - Tipificaciones.xlsx` *(etiquetas expertas)*;
- `excluidos.txt` *(códigos que se apartan de los descriptivos y que el entrenamiento reporta con y sin ellos)*;
- `code_fixes.json` *(correcciones de códigos mal escritos en el formulario)*;
- el export del formulario y todas las salidas *(`*_out/`)*.

**Nada de eso se sube.** Antes de cada subida, correr:

```
python research/verificar_privacidad.py
```

Falla si encuentra un código de respondente, un email o un archivo de datos fuera de `data/`.

## Uso

```
set NUREON_DATA=C:\ruta\a\datos            (Windows)
python research/pilot/parse_form_export.py "export.csv"
python research/pilot/pilot_metrics.py %NUREON_DATA%\responses_wide.csv
python research/pilot/train_pilot.py %NUREON_DATA%\responses_wide.csv
```

Requiere Python 3.11 o superior, `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib` y `openpyxl`.

El entrenamiento de los modelos que usa el producto va en `backend/app/ml/training/` *(se sube aparte)*, con la versión de scikit-learn fijada en el backend.
