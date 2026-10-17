# -*- coding: utf-8 -*-
"""Context-free Spanish diacritic restoration.

Only words whose accented form is unambiguous regardless of context are listed.
Context-dependent pairs (que/que, como/como, esta/esta, si/si, cual/cual,
quien/quien, donde/donde, el/el, tu/tu, mi/mi) are deliberately EXCLUDED and
must be resolved by a human pass.
"""
import re

SAFE = {
 "demas": "demás", "detras": "detrás", "estan": "están", "habia": "había",
 "conversacion": "conversación", "preocupacion": "preocupación",
 "observacion": "observación", "exposicion": "exposición",
 "interrupcion": "interrupción", "insatisfaccion": "insatisfacción",
 "implicitas": "implícitas", "incomodo": "incómodo", "logro": "logro",
 "estimulos": "estímulos", "aprendizaje": "aprendizaje", "critica": "crítica",
 "criticas": "críticas", "mediocridad": "mediocridad", "sintomas": "síntomas",
 "cai": "caí", "ordenes": "órdenes",
 # adverbs / connectors
 "mas": "más", "tambien": "también", "despues": "después", "ademas": "además",
 "quizas": "quizás", "asi": "así", "ahi": "ahí", "aqui": "aquí", "alli": "allí",
 "todavia": "todavía",  
 # -cion / -sion nouns (singular only; plurals drop the accent)
 "reaccion": "reacción", "situacion": "situación", "decision": "decisión",
 "informacion": "información", "presion": "presión", "opinion": "opinión",
 "conexion": "conexión", "relacion": "relación", "atencion": "atención",
 "emocion": "emoción", "razon": "razón", "accion": "acción",
 "direccion": "dirección", "tension": "tensión", "expresion": "expresión",
 "posicion": "posición", "intencion": "intención", "satisfaccion": "satisfacción",
 "frustracion": "frustración", "decepcion": "decepción", "sensacion": "sensación",
 "conclusion": "conclusión", "discusion": "discusión", "devolucion": "devolución",
 "solucion": "solución", "correccion": "corrección", "proteccion": "protección",
 "conviccion": "convicción", "explicacion": "explicación", 
 "negociacion": "negociación", "ejecucion": "ejecución", "evaluacion": "evaluación",
  "obligacion": "obligación", "reunion": "reunión",
 "cuestion": "cuestión", "ocasion": "ocasión", "version": "versión",
 # -ia nouns
 "autonomia": "autonomía", "armonia": "armonía", "energia": "energía",
 "dia": "día", "dias": "días", "compania": "compañía", "categoria": "categoría",
 # adjectives / nouns with written accent
 "dificil": "difícil", "facil": "fácil", "util": "útil", "publico": "público",
 "rapido": "rápido", "rapida": "rápida", "logico": "lógico", "logica": "lógica",
   "fisico": "físico",
 "fisica": "física", "unico": "único", "unica": "única", "ultimo": "último",
 "ultima": "última", "proximo": "próximo", "minimo": "mínimo", "maximo": "máximo",
 "metodico": "metódico", "automatico": "automático", "generico": "genérico",
 "animo": "ánimo", "vinculo": "vínculo", "vinculos": "vínculos",
   
 "analisis": "análisis", "exito": "éxito", "interes": "interés",
 "credito": "crédito", "caotico": "caótico", "frio": "frío",
 "solido": "sólido", "solidas": "sólidas", "debil": "débil",
 "desafio": "desafío", "desafios": "desafíos", "traspie": "traspié",
 # verb forms — conditionals / futures / preterites (context-free)
 "podria": "podría", "deberia": "debería", "tendria": "tendría",
 "haria": "haría", "seria": "sería", "queria": "quería", "sabria": "sabría",
 "pasaria": "pasaría", "saldria": "saldría", "estaria": "estaría",
 "dolio": "dolió",  "llego": "llegó", "quedo": "quedó",
 "salio": "salió", "fallo": "falló", "resolvio": "resolvió", "falto": "faltó",
 "senalar": "señalar", "senala": "señala", "senal": "señal",
 "acompana": "acompaña", "acompanaron": "acompañaron", 
 "manana": "mañana",  "duenio": "dueño", "dueno": "dueño",
 "anos": "años", "extranio": "extraño",
 # voseo / 2nd person forms used throughout
 "tenes": "tenés", "podes": "podés", "sabes": "sabés", "queres": "querés",
 "haces": "hacés", "decis": "decís", "preferis": "preferís", "seguis": "seguís",
 "sentis": "sentís", "venis": "venís", "conoces": "conocés", "vivis": "vivís",
 "apoyas": "apoyás", "buscas": "buscás",  "adaptas": "adaptás",
  "valoras": "valorás", "evaluas": "evaluás",
  "priorizas": "priorizás", "registras": "registrás",
 "encajas": "encajás", "pensas": "pensás",  
 "entendes": "entendés", "elegis": "elegís", 
 "trabajas": "trabajás", "manejas": "manejás", "reaccionas": "reaccionás",
 "arreglas": "arreglás", "soltas": "soltás", "aceptas": "aceptás",
 "sostenes": "sostenés", "perdes": "perdés", "recordas": "recordás",
 "imaginas": "imaginás", "describis": "describís", "cambias": "cambiás",
}

# words we deliberately do NOT auto-accent, for the human pass
AMBIGUOUS = ["que", "como", "cual", "quien", "donde", "si", "el", "tu", "mi", "se", "te", "de"]

_pat = re.compile(r"\b(" + "|".join(sorted(SAFE, key=len, reverse=True)) + r")\b")

def restore(text):
    def sub(m):
        w = m.group(1)
        out = SAFE[w]
        return out
    return _pat.sub(sub, text)

def count_ambiguous(text):
    """How many context-dependent tokens remain for the human pass."""
    n = 0
    for w in AMBIGUOUS:
        n += len(re.findall(r"\b" + w + r"\b", text, flags=re.I))
    return n
