"""
CÓDIGO VERBAL PARA MENTALISMO — Motor por Componentes Binarios (52 cartas)
=====================================================================
Motor de detección por componentes independientes (Bits 8, 4, 2, 1 + Palos):
- Trigger (Palabra Activadora)
- Bit 8 (+8)
- Bit 4 (+4)
- Bit 2 (+2)
- Bit 1 (+1)
- Palos Independientes: corazones, diamantes, treboles, picas
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

VALOR_PALABRAS = {}
PALO_PALABRAS = {}

NUM_TO_VAL_MAP = {
    "1": "A", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10", "11": "J", "12": "Q", "13": "K"
}

VALUE_NAMES = {
    "A": "As", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10", "J": "J", "Q": "Q", "K": "K"
}

DEFAULT_BINARY_CONFIG = {
    "trigger": "vale",
    "bit8": "bueno, vale bueno, demasiado, mal",
    "bit4": "entonces, despues, nada",
    "bit2": "ahora, luego, mucho",
    "bit1": "vas, ante, uno, antes",
    "corazones": "corazones, corazon, tomado",
    "diamantes": "diamantes, diamante, elegido",
    "treboles": "treboles, trebol, cogido",
    "picas": "picas, pica, sacado"
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


def parse_patterns(raw_val) -> list:
    """Convierte una cadena o lista de expresiones separadas por comas a una lista normalizada."""
    if not raw_val:
        return []
    if isinstance(raw_val, list):
        items = raw_val
    else:
        items = str(raw_val).split(",")
    result = []
    for item in items:
        cleaned = " ".join(normalizeSpeech(str(item)))
        if cleaned:
            result.append(cleaned)
    return result


def contains_pattern(text_str: str, expressions: list) -> bool:
    """Comprueba si alguna de las expresiones está presente en la transcripción."""
    if not text_str or not expressions:
        return False
    norm_text = " " + " ".join(normalizeSpeech(text_str)) + " "
    for expr in expressions:
        norm_expr = " " + expr + " "
        if norm_expr in norm_text:
            return True
    return False


def detectCardFromBinaryComponents(text: str, config: dict = None) -> dict:
    """
    Decodifica una carta escaneando la transcripción hablada tras la palabra activadora (trigger)
    e identificando independientemente los bits (Bit 8, Bit 4, Bit 2, Bit 1) y el palo.
    """
    if not text:
        return {"detected": False}

    cfg = config if (config and isinstance(config, dict)) else DEFAULT_BINARY_CONFIG

    trigger_exprs = parse_patterns(cfg.get("trigger") or "vale")
    words = normalizeSpeech(text)
    full_norm_text = " ".join(words)

    if not trigger_exprs:
        trigger_exprs = ["vale"]

    kw_found = False
    kw_matched = trigger_exprs[0]
    after_text = full_norm_text

    for trig in trigger_exprs:
        if trig in full_norm_text:
            kw_found = True
            kw_matched = trig
            idx = full_norm_text.find(trig)
            after_text = full_norm_text[idx + len(trig):].strip()
            break

    target_text = after_text if kw_found else full_norm_text

    bit8_patterns = parse_patterns(cfg.get("bit8"))
    bit4_patterns = parse_patterns(cfg.get("bit4"))
    bit2_patterns = parse_patterns(cfg.get("bit2"))
    bit1_patterns = parse_patterns(cfg.get("bit1"))

    has_b8 = contains_pattern(target_text, bit8_patterns)
    has_b4 = contains_pattern(target_text, bit4_patterns)
    has_b2 = contains_pattern(target_text, bit2_patterns)
    has_b1 = contains_pattern(target_text, bit1_patterns)

    decimal_val = (8 if has_b8 else 0) + (4 if has_b4 else 0) + (2 if has_b2 else 0) + (1 if has_b1 else 0)

    detected_suit = None
    suit_code = None

    for suit_key in ["corazones", "diamantes", "treboles", "picas"]:
        suit_exprs = parse_patterns(cfg.get(suit_key))
        if contains_pattern(target_text, suit_exprs):
            detected_suit = suit_key
            suit_code = suit_key.upper()
            break

    if 1 <= decimal_val <= 13 and detected_suit:
        rank_code = NUM_TO_VAL_MAP[str(decimal_val)]
        val_name = VALUE_NAMES[rank_code]
        bits_str = f"B8:{int(has_b8)} B4:{int(has_b4)} B2:{int(has_b2)} B1:{int(has_b1)}"
        return {
            "detected": True,
            "keywordFound": kw_found,
            "keyword": kw_matched,
            "value": rank_code,
            "decimalValue": decimal_val,
            "valueName": val_name,
            "suit": detected_suit,
            "suitCode": suit_code,
            "valuePattern": bits_str,
            "matchedWords": [bits_str, suit_code],
            "afterWords": normalizeSpeech(after_text),
            "fullText": text
        }

    return {
        "detected": False,
        "keywordFound": kw_found,
        "keyword": kw_matched,
        "decimalValue": decimal_val,
        "afterWords": normalizeSpeech(after_text),
        "fullText": text
    }


def detectCardWithKeyword(text: str, keyword: str = "vale", config: dict = None) -> dict:
    """Compatibilidad directa para invocación con o sin configuración."""
    return detectCardFromBinaryComponents(text, config)


def analizar_frase(frase: str, config: dict = None) -> dict:
    """Compatibilidad con la API REST."""
    res = detectCardFromBinaryComponents(frase, config)
    if not res.get("detected"):
        return {"error": "no se reconoció ninguna combinación válida de carta por suma de bits y palo."}

    palo_id = res["suit"]
    valor_str = str(res["value"])
    return {
        "valor": valor_str,
        "palo_id": palo_id,
        "palo": PALOS[palo_id],
        "n_palabras": len(res.get("matchedWords", [])),
        "coletilla": res.get("suitCode", ""),
        "matchedWords": res.get("matchedWords", []),
        "valuePattern": res.get("valuePattern", "")
    }


def validate_binary_config(config: dict) -> dict:
    """Valida que la configuración contenga los campos requeridos en formato de texto o lista."""
    if not config or not isinstance(config, dict):
        return {"valid": False, "error": "La configuración debe ser un objeto JSON válido."}
    return {"valid": True}
