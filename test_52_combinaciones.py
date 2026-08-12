import sys
from test_fonetico import detectCardFromSpeech, VALUE_PATTERNS, SUIT_PATTERNS, VALUE_NAMES, PALO_NOMBRES

# 1. Matriz de frases de prueba para las 52 combinaciones (13 valores x 4 palos)
VALOR_BASES = {
    'AS': "Ahora sí",
    'DOS': "De otro sitio",
    'TRE': "Tiene respuesta evidente",
    'CUA': "Cada uno adivina",
    'CIN': "Cada instante noto",
    'SEI': "Siempre encuentra indicios",
    'SIE': "Siempre intenta estar",
    'OCH': "O como hoy",
    'NUE': "Nunca uso explicaciones",
    'DIE': "De inmediato encaja",
    'ONC': "Hombre no creo",
    'DOC': "Dos cosas coinciden",
    'REI': "Realmente es increíble",
}

PALO_PALABRAS = {
    'picas': "perfecto",
    'corazones': "correcto",
    'diamantes': "donde",
    'tréboles': "tranquilo"
}

def test_52_combinaciones():
    total = 0
    exitos = 0
    for pat, val in VALUE_PATTERNS.items():
        val_name = VALUE_NAMES[val]
        base_phrase = VALOR_BASES[pat]
        for suit_id, suit_word in PALO_PALABRAS.items():
            total += 1
            frase = f"{base_phrase} {suit_word}."
            res = detectCardFromSpeech(frase)
            
            esperado_val = val
            esperado_suit = suit_id
            
            ok = (res.get('detected') is True and 
                  res.get('value') == esperado_val and 
                  res.get('suit') == esperado_suit)
            
            if ok:
                exitos += 1
            else:
                print(f"[ERROR 52] Frase: '{frase}' -> Obtenido: {res}")
                
    print(f"Prueba de 52 combinaciones: {exitos} / {total} pasadas correctamente.")
    assert exitos == total

def test_casos_borde():
    casos = [
        # Mayúsculas y minúsculas mixtas
        ("HOMBRE NO CREO PROBABLE", True, "J", "picas"),
        ("hombre, NO creo PROBABLEMENTE", True, "J", "picas"),
        
        # Tildes y puntuación compleja
        ("¡Hombre! ¿No creo probable que sea correcto?", True, "J", "picas"),
        ("¡¡¡SIEMPRE INTENTA ESTAR TRANQUILO!!!", True, 7, "tréboles"),
        
        # Frase larga con patrón en el medio de la conversación
        ("Hola a todos, bienvenido al show. Hombre no creo probable que ocurra nada raro hoy.", True, "J", "picas"),
        
        # Palabras anteriores y posteriores al patrón
        ("Palabras de relleno antes del truco de otro sitio perfecto y mas palabras de relleno despues.", True, 2, "picas"),
        
        # Patrón incompleto o sin palo -> Debe retornar detected: False
        ("De otro sitio", False, None, None),
        ("Hombre no creo", False, None, None),
        ("Tiene respuesta evidente", False, None, None),
        
        # Múltiples patrones -> Debe elegir el más reciente completo
        ("De otro sitio perfecto... tiempo despues hombre no creo probable", True, "J", "picas"),
        
        # H muda y variaciones fonéticas
        ("Ha sido perfecto hoy", True, "A", "picas"),
        ("O como hoy parece evidente", True, 8, "picas"),
        
        # Variación de palabras de palo con la misma inicial fonética
        ("Hombre no creo precisamente...", True, "J", "picas"),  # precisamente -> P
        ("Hombre no creo posiblemente...", True, "J", "picas"),   # posiblemente -> P
        ("Hombre no creo cosas...", True, "J", "corazones"),     # cosas -> C
        ("Hombre no creo dado...", True, "J", "diamantes"),       # dado -> D
        ("Hombre no creo todo...", True, "J", "tréboles"),        # todo -> T
    ]

    total = len(casos)
    exitos = 0
    for frase, exp_detected, exp_val, exp_suit in casos:
        res = detectCardFromSpeech(frase)
        if exp_detected:
            ok = (res.get('detected') is True and 
                  res.get('value') == exp_val and 
                  res.get('suit') == exp_suit)
        else:
            ok = (res.get('detected') is False)

        if ok:
            exitos += 1
        else:
            print(f"[ERROR CASO BORDE] Frase: '{frase}' -> Obtenido: {res}")

    print(f"Prueba de Casos Borde: {exitos} / {total} pasadas correctamente.")
    assert exitos == total

if __name__ == "__main__":
    test_52_combinaciones()
    test_casos_borde()
    print("\n[OK] TODOS LOS TESTS OBLIGATORIOS PASARON CON EXITO (52 combinaciones + casos borde).")
