import sys
from codigo_carta import detectCardFromBinaryComponents, DEFAULT_BINARY_CONFIG

# Mapeo de valores decimales 1..13 a sus combinaciones de palabras binarias
# Bit 8 = "bueno", Bit 4 = "entonces", Bit 2 = "ahora", Bit 1 = "vas"
VALUE_BINARY_PHRASES = {
    "1":  "vas",
    "2":  "ahora",
    "3":  "ahora vas",
    "4":  "entonces",
    "5":  "entonces vas",
    "6":  "entonces ahora",
    "7":  "entonces ahora vas",
    "8":  "bueno",
    "9":  "bueno vas",
    "10": "bueno ahora",
    "11": "bueno ahora vas",
    "12": "bueno entonces",
    "13": "bueno entonces vas"
}

NUM_TO_VAL_MAP = {
    "1": "A", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7",
    "8": "8", "9": "9", "10": "10", "11": "J", "12": "Q", "13": "K"
}

SUIT_WORDS = {
    "corazones": "corazones",
    "diamantes": "diamantes",
    "treboles": "treboles",
    "picas": "picas"
}

def test_52_combinaciones_binarias():
    total = 0
    exitos = 0

    for dec_str, bin_words in VALUE_BINARY_PHRASES.items():
        exp_val = NUM_TO_VAL_MAP[dec_str]
        for suit_id, suit_word in SUIT_WORDS.items():
            total += 1

            # Probar Orden 1: trigger + bits + palo
            frase1 = f"Vale {bin_words} {suit_word} en el escenario."
            res1 = detectCardFromBinaryComponents(frase1, DEFAULT_BINARY_CONFIG)

            # Probar Orden 2: trigger + palo + bits
            frase2 = f"Vale el elemento {suit_word} {bin_words} de la mesa."
            res2 = detectCardFromBinaryComponents(frase2, DEFAULT_BINARY_CONFIG)

            ok1 = (res1.get('detected') is True and 
                   str(res1.get('value')) == exp_val and 
                   res1.get('suit') == suit_id)

            ok2 = (res2.get('detected') is True and 
                   str(res2.get('value')) == exp_val and 
                   res2.get('suit') == suit_id)

            if ok1 and ok2:
                exitos += 1
            else:
                print(f"[ERROR 52 BINARIO] dec={dec_str} ({exp_val}), suit={suit_id} -> r1={res1}, r2={res2}")

    print(f"Prueba de 52 combinaciones binarias (ambos órdenes): {exitos} / {total} pasadas correctamente.")
    assert exitos == total

def test_casos_borde_binarios():
    casos = [
        # Ejemplo 1 del usuario: 8 + 4 + 2 + 1 = 15 -> tope 13 -> K de Corazones
        ("Vale bueno entonces ahora vas corazones", True, "K", "corazones"),

        # Ejemplo 2 del usuario: 8 + 4 = 12 -> Q de Corazones
        ("Vale bueno entonces corazones", True, "Q", "corazones"),

        # Ejemplo 3: 4 + 1 = 5 -> 5 de Picas
        ("Vale entonces vas picas", True, "5", "picas"),

        # Ejemplo 4: 1 = A de Diamantes
        ("Vale vas diamantes", True, "A", "diamantes"),

        # Mayúsculas/minúsculas y tildes
        ("¡¡¡VALE BUENO AHORA CORAZÓN!!!", True, "10", "corazones"),

        # Sin trigger pero con patrones directos
        ("bueno entonces corazones", True, "Q", "corazones"),

        # Sin palo detectado -> detected False
        ("Vale bueno entonces ahora vas", False, None, None),
    ]

    total = len(casos)
    exitos = 0
    for frase, exp_detected, exp_val, exp_suit in casos:
        res = detectCardFromBinaryComponents(frase, DEFAULT_BINARY_CONFIG)
        if exp_detected:
            ok = (res.get('detected') is True and 
                  str(res.get('value')) == exp_val and 
                  res.get('suit') == exp_suit)
        else:
            ok = (res.get('detected') is False)

        if ok:
            exitos += 1
        else:
            print(f"[ERROR BORDE BINARIO] Frase: '{frase}' -> Obtenido: {res}")

    print(f"Prueba de casos borde binarios: {exitos} / {total} pasados correctamente.")
    assert exitos == total

if __name__ == "__main__":
    test_52_combinaciones_binarias()
    test_casos_borde_binarios()
