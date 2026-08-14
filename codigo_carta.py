"""
CÓDIGO VERBAL PARA MENTALISMO — Baraja de póker (52 cartas)
=====================================================================
Motor de detección por palabras clave de Valor y Palo:
- PALABRA CLAVE DE ACTIVACIÓN: "vale" (o la configurada)
- VALORES (1 a 13):
  1=antes, 2=ahora, 3=luego, 4=después, 5=nada, 6=poco, 7=mucho,
  8=demasiado, 9=todo, 10=mal, 11=regular (J), 12=bien (Q), 13=perfecto (K)
- PALOS:
  treboles=cogido, picas=sacado, diamantes=elegido, corazones=tomado
"""

import re
import unicodedata

RANGOS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

PALOS = {
    "treboles":  {"simbolo": "♣", "nombre": "Tréboles"},
    "corazones": {"simbolo": "♥", "nombre": "Corazones"},
    "diamantes": {"simbolo": "♦", "nombre": "Diamantes"},
    "picas":     {"simbolo": "♠", "nombre": "Picas"},
}

VALOR_PALABRAS = {
    "antes":     {"valor": "A",  "nombre": "As",       "num": 1},
    "ante":      {"valor": "A",  "nombre": "As",       "num": 1},
    "1":         {"valor": "A",  "nombre": "As",       "num": 1},
    "uno":       {"valor": "A",  "nombre": "As",       "num": 1},
    "ahora":     {"valor": "2",  "nombre": "2",        "num": 2},
    "2":         {"valor": "2",  "nombre": "2",        "num": 2},
    "dos":       {"valor": "2",  "nombre": "2",        "num": 2},
    "luego":     {"valor": "3",  "nombre": "3",        "num": 3},
    "3":         {"valor": "3",  "nombre": "3",        "num": 3},
    "tres":      {"valor": "3",  "nombre": "3",        "num": 3},
    "despues":   {"valor": "4",  "nombre": "4",        "num": 4},
    "despue":    {"valor": "4",  "nombre": "4",        "num": 4},
    "4":         {"valor": "4",  "nombre": "4",        "num": 4},
    "cuatro":    {"valor": "4",  "nombre": "4",        "num": 4},
    "nada":      {"valor": "5",  "nombre": "5",        "num": 5},
    "5":         {"valor": "5",  "nombre": "5",        "num": 5},
    "cinco":     {"valor": "5",  "nombre": "5",        "num": 5},
    "poco":      {"valor": "6",  "nombre": "6",        "num": 6},
    "poca":      {"valor": "6",  "nombre": "6",        "num": 6},
    "6":         {"valor": "6",  "nombre": "6",        "num": 6},
    "seis":      {"valor": "6",  "nombre": "6",        "num": 6},
    "mucho":     {"valor": "7",  "nombre": "7",        "num": 7},
    "mucha":     {"valor": "7",  "nombre": "7",        "num": 7},
    "7":         {"valor": "7",  "nombre": "7",        "num": 7},
    "siete":     {"valor": "7",  "nombre": "7",        "num": 7},
    "demasiado": {"valor": "8",  "nombre": "8",        "num": 8},
    "demasiada": {"valor": "8",  "nombre": "8",        "num": 8},
    "8":         {"valor": "8",  "nombre": "8",        "num": 8},
    "ocho":      {"valor": "8",  "nombre": "8",        "num": 8},
    "todo":      {"valor": "9",  "nombre": "9",        "num": 9},
    "toda":      {"valor": "9",  "nombre": "9",        "num": 9},
    "9":         {"valor": "9",  "nombre": "9",        "num": 9},
    "nueve":     {"valor": "9",  "nombre": "9",        "num": 9},
    "mal":       {"valor": "10", "nombre": "10",       "num": 10},
    "mar":       {"valor": "10", "nombre": "10",       "num": 10},
    "mas":       {"valor": "10", "nombre": "10",       "num": 10},
    "malo":      {"valor": "10", "nombre": "10",       "num": 10},
    "mala":      {"valor": "10", "nombre": "10",       "num": 10},
    "10":        {"valor": "10", "nombre": "10",       "num": 10},
    "diez":      {"valor": "10", "nombre": "10",       "num": 10},
    "regular":   {"valor": "J",  "nombre": "J",        "num": 11},
    "11":        {"valor": "J",  "nombre": "J",        "num": 11},
    "once":      {"valor": "J",  "nombre": "J",        "num": 11},
    "jota":      {"valor": "J",  "nombre": "J",        "num": 11},
    "bien":      {"valor": "Q",  "nombre": "Q",        "num": 12},
    "12":        {"valor": "Q",  "nombre": "Q",        "num": 12},
    "doce":      {"valor": "Q",  "nombre": "Q",        "num": 12},
    "reina":     {"valor": "Q",  "nombre": "Q",        "num": 12},
    "dama":      {"valor": "Q",  "nombre": "Q",        "num": 12},
    "perfecto":  {"valor": "K",  "nombre": "K",        "num": 13},
    "perfecta":  {"valor": "K",  "nombre": "K",        "num": 13},
    "13":        {"valor": "K",  "nombre": "K",        "num": 13},
    "trece":     {"valor": "K",  "nombre": "K",        "num": 13},
    "rey":       {"valor": "K",  "nombre": "K",        "num": 13},
}

PALO_PALABRAS = {
    "cogido":   "treboles",
    "cogida":   "treboles",
    "cogidos":  "treboles",
    "cogidas":  "treboles",
    "trebol":   "treboles",
    "treboles": "treboles",
    "sacado":   "picas",
    "sacada":   "picas",
    "sacados":  "picas",
    "sacadas":  "picas",
    "pica":     "picas",
    "picas":    "picas",
    "elegido":  "diamantes",
    "elegida":  "diamantes",
    "elegidos": "diamantes",
    "elegidas": "diamantes",
    "diamante": "diamantes",
    "diamantes":"diamantes",
    "tomado":   "corazones",
    "tomada":   "corazones",
    "tomados":  "corazones",
    "tomadas":  "corazones",
    "corazon":  "corazones",
    "corazones":"corazones",
}

VALUE_NAMES = {
    "A": "As", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10", "J": "J", "Q": "Q", "K": "K"
}


def normalizeSpeech(text: str) -> list:
    """Normaliza el texto quitando acentos y signos de puntuación."""
    if not text:
        return []
    t = text.lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return [w for w in t.split() if w]


def detectCardFromSpeech(text: str) -> dict:
    """
    Escanea las palabras de la frase para identificar la palabra de valor
    y la palabra de palo, independientemente del orden en que aparezcan.
    """
    words = normalizeSpeech(text)
    if not words:
        return {"detected": False}

    detected_val = None
    detected_palo = None
    val_word = None
    palo_word = None
    matched_words = []

    for w in words:
        # Verificar si es palabra de valor
        if not detected_val and w in VALOR_PALABRAS:
            detected_val = VALOR_PALABRAS[w]
            val_word = w
            matched_words.append(w)
        # Verificar si es palabra de palo
        elif not detected_palo and w in PALO_PALABRAS:
            detected_palo = PALO_PALABRAS[w]
            palo_word = w
            matched_words.append(w)

    if detected_val and detected_palo:
        return {
            "detected": True,
            "value": detected_val["valor"],
            "valueName": detected_val["nombre"],
            "suit": detected_palo,
            "suitCode": palo_word.upper(),
            "valuePattern": val_word.upper(),
            "matchedWords": matched_words,
            "confidence": 1
        }

    return {"detected": False}


def analizar_frase(frase: str, coletillas: dict = None) -> dict:
    """Compatibilidad con la API REST."""
    res = detectCardFromSpeech(frase)
    if not res.get("detected"):
        return {"error": "no se reconoció ninguna combinación válida de palabra de valor + palabra de palo"}

    palo_id = res["suit"]
    valor_str = str(res["value"])
    return {
        "valor": valor_str,
        "palo_id": palo_id,
        "palo": PALOS[palo_id],
        "n_palabras": len(res["matchedWords"]),
        "coletilla": res["suitCode"],
        "matchedWords": res["matchedWords"],
        "valuePattern": res["valuePattern"]
    }


def texto_resultado(frase: str) -> str:
    r = analizar_frase(frase)
    if "error" in r:
        return f"⚠ {r['error']}"
    return (f"{r['valor']} de {r['palo']['nombre']} {r['palo']['simbolo']}  "
            f"(Palabras: {r['valuePattern']} + {r['coletilla']})")


def detectCardWithKeyword(text: str, keyword: str = "vale") -> dict:
    """
    Busca la palabra clave (ej. 'vale') dentro del texto hablado.
    Si la encuentra, analiza las palabras posteriores para detectar valor y palo.
    """
    if not text or not keyword:
        return {"keywordFound": False, "detected": False}

    words = normalizeSpeech(text)
    kw_words = normalizeSpeech(keyword)
    kw = kw_words[0] if kw_words else "vale"

    # Buscar la última aparición de la palabra clave
    kw_idx = -1
    for idx, w in enumerate(words):
        if w == kw:
            kw_idx = idx

    if kw_idx == -1:
        return {"keywordFound": False, "detected": False, "keyword": kw}

    # Palabras después de la palabra clave
    after_words = words[kw_idx + 1:]
    after_text = " ".join(after_words)

    card_res = detectCardFromSpeech(after_text)
    if not card_res.get("detected"):
        # Intentar también con todo el texto posterior desde la palabra clave
        card_res = detectCardFromSpeech(" ".join(words[kw_idx:]))

    card_res["keywordFound"] = True
    card_res["keyword"] = kw
    card_res["afterWords"] = after_words
    card_res["fullText"] = text
    return card_res
