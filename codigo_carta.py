"""
CÓDIGO VERBAL FONÉTICO PARA MENTALISMO — Baraja de póker (52 cartas)
=====================================================================
Motor de detección fonética basado en patrones de iniciales habladas consecutivas:
- PALABRA 1 + PALABRA 2 + PALABRA 3 = VALOR (Patrones: AS, DOS, TRE, CUA, CIN, SEI, SIE, OCH, NUE, DIE, ONC, DOC, REI)
- PALABRA 4 = PALO (P = Picas, C = Corazones, D = Diamantes, T = Tréboles)
"""

import re
import random
import unicodedata

RANGOS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

PALOS = {
    "treboles":  {"simbolo": "♣", "nombre": "Tréboles"},
    "corazones": {"simbolo": "♥", "nombre": "Corazones"},
    "diamantes": {"simbolo": "♦", "nombre": "Diamantes"},
    "picas":     {"simbolo": "♠", "nombre": "Picas"},
}

VALUE_PATTERNS = {
    "AS":  "A",
    "DOS": 2,
    "TRE": 3,
    "CUA": 4,
    "CIN": 5,
    "SEI": 6,
    "SIE": 7,
    "OCH": 8,
    "NUE": 9,
    "DIE": 10,
    "ONC": "J",
    "DOC": "Q",
    "REI": "K"
}

SUIT_PATTERNS = {
    "P": "picas",
    "C": "corazones",
    "D": "diamantes",
    "T": "tréboles"
}

VALUE_NAMES = {
    "A": "As", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
    8: "8", 9: "9", 10: "10", "J": "J", "Q": "Q", "K": "K"
}

COLETILLAS = {
    "diamantes": ["D"],
    "corazones": ["C"],
    "picas":     ["P"],
    "treboles":  ["T"],
}


def normalizeSpeech(text: str) -> list:
    """Normaliza el texto manteniendo palabras consecutivas limpias."""
    if not text:
        return []
    t = text.lower()
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return [w for w in t.split() if w]


def getPhoneticInitial(word: str) -> list:
    """
    Retorna los símbolos de iniciales fonéticas candidatas para una palabra en español,
    gestionando H muda, vocales acentuadas y peculiaridades del habla.
    """
    if not word:
        return []
    w = word.lower()
    candidates = []

    # H muda al inicio -> vocal siguiente + H (ej: 'hombre' -> O y H, 'hoy' -> O y H)
    if w.startswith("h") and len(w) > 1:
        vowel = w[1]
        if vowel in "aeiou":
            candidates.append(vowel.upper())
        candidates.append("H")
        return candidates

    c0 = w[0]

    # Vocales
    if c0 in "aeiou":
        candidates.append(c0.upper())
        return candidates
    if c0 == "y":
        candidates.append("I")

    # Consonantes y peculiaridades
    if c0 in "ckq":
        candidates.append("C")
        if len(w) > 1 and w[1] == "o":
            candidates.append("O")
    elif c0 in "sz":
        candidates.append("S")
    elif c0 in "bv":
        candidates.append("B")
    else:
        candidates.append(c0.upper())

    return list(dict.fromkeys(candidates))


def detectCardFromSpeech(text: str) -> dict:
    """
    Función principal de detección fonética:
    Busca patrones fonéticos consecutivos (3 palabras de valor + 1 palabra de palo).
    """
    words = normalizeSpeech(text)
    if not words:
        return {"detected": False}

    phonetics = [getPhoneticInitial(w) for w in words]
    n = len(words)
    matches = []

    for i in range(n):
        # --- Caso Especial AS (2 palabras + palo) ---
        if i + 1 < n:
            c1_list = phonetics[i]
            c2_list = phonetics[i+1]
            if "A" in c1_list and "S" in c2_list:
                if i + 2 < n:
                    suit_candidates = phonetics[i+2]
                    for s_code in ["P", "C", "D", "T"]:
                        if s_code in suit_candidates:
                            matches.append({
                                "detected": True,
                                "value": "A",
                                "valueName": "As",
                                "suit": SUIT_PATTERNS[s_code],
                                "suitCode": s_code,
                                "valuePattern": "AS",
                                "matchedWords": words[i:i+3],
                                "startIdx": i,
                                "endIdx": i+3,
                                "confidence": 1
                            })

        # --- Patrón Estándar de Valor (3 palabras + 1 palabra de palo) ---
        if i + 2 < n:
            for c1 in phonetics[i]:
                for c2 in phonetics[i+1]:
                    for c3 in phonetics[i+2]:
                        pat = c1 + c2 + c3
                        if pat in VALUE_PATTERNS:
                            val = VALUE_PATTERNS[pat]
                            val_name = VALUE_NAMES[val]
                            
                            if i + 3 < n:
                                suit_candidates = phonetics[i+3]
                                for s_code in ["P", "C", "D", "T"]:
                                    if s_code in suit_candidates:
                                        matches.append({
                                            "detected": True,
                                            "value": str(val),
                                            "valueName": str(val_name),
                                            "suit": SUIT_PATTERNS[s_code],
                                            "suitCode": s_code,
                                            "valuePattern": pat,
                                            "matchedWords": words[i:i+4],
                                            "startIdx": i,
                                            "endIdx": i+4,
                                            "confidence": 1
                                        })

    if not matches:
        return {"detected": False}

    # Preferir la coincidencia más reciente con valor + palo
    matches.sort(key=lambda m: (m["endIdx"], m["startIdx"]), reverse=True)
    best = matches[0]
    del best["startIdx"]
    del best["endIdx"]
    return best


def analizar_frase(frase: str, coletillas: dict = None) -> dict:
    """Mantiene compatibilidad con la estructura de respuesta de la aplicación existente."""
    res = detectCardFromSpeech(frase)
    if not res.get("detected"):
        return {"error": "no se reconoció ningún patrón fonético válido de valor + palo"}

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
            f"(Patrón {r['valuePattern']} + {r['coletilla']})")


def detectCardWithKeyword(text: str, keyword: str = "vale") -> dict:
    """
    Busca la palabra clave (ej. 'vale') dentro del texto hablado.
    Si la encuentra, analiza el texto posterior para detectar la carta.
    """
    if not text or not keyword:
        return {"keywordFound": False, "detected": False}

    words = normalizeSpeech(text)
    kw_words = normalizeSpeech(keyword)

    if not kw_words:
        kw = "vale"
    else:
        kw = kw_words[0]

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

