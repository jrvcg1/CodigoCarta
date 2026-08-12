import re
import unicodedata

VALUE_PATTERNS = {
    'AS':  'A',
    'DOS': 2,
    'TRE': 3,
    'CUA': 4,
    'CIN': 5,
    'SEI': 6,
    'SIE': 7,
    'OCH': 8,
    'NUE': 9,
    'DIE': 10,
    'ONC': 'J',
    'DOC': 'Q',
    'REI': 'K'
}

SUIT_PATTERNS = {
    'P': 'picas',
    'C': 'corazones',
    'D': 'diamantes',
    'T': 'treboles'
}

VALUE_NAMES = {
    'A': 'As', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
    8: '8', 9: '9', 10: '10', 'J': 'J', 'Q': 'Q', 'K': 'K'
}

PALO_NOMBRES = {
    'picas': 'Picas',
    'corazones': 'Corazones',
    'diamantes': 'Diamantes',
    'treboles': 'Tréboles'
}

def normalizeSpeech(text: str):
    if not text:
        return []
    # 1. Minusculas
    t = text.lower()
    # 2. Normalizar acentos manteniendo letras base
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    # 3. Eliminar puntuacion
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    # 4. Palabras limpias
    return [w for w in t.split() if w]

def getPhoneticInitial(word: str):
    if not word:
        return []
    w = word.lower()
    candidates = []

    # H muda al inicio -> vocal siguiente + H
    if w.startswith('h') and len(w) > 1:
        vowel = w[1]
        if vowel in 'aeiou':
            candidates.append(vowel.upper())
        candidates.append('H')
        return candidates

    c0 = w[0]

    # Vocales
    if c0 in 'aeiou':
        candidates.append(c0.upper())
        return candidates
    if c0 == 'y':
        candidates.append('I')

    # Consonantes y peculiaridades
    if c0 in 'ckq':
        candidates.append('C')
        # Si c va seguida de o (ej: 'cosas'), permitir O como candidata fonetica secundaria
        if len(w) > 1 and w[1] == 'o':
            candidates.append('O')
    elif c0 in 'sz':
        candidates.append('S')
    elif c0 in 'bv':
        candidates.append('B')
    else:
        candidates.append(c0.upper())

    return list(dict.fromkeys(candidates))

def detectCardFromSpeech(text: str):
    words = normalizeSpeech(text)
    if not words:
        return {'detected': False}

    phonetics = [getPhoneticInitial(w) for w in words]
    n = len(words)
    matches = []

    for i in range(n):
        # --- Caso Especial AS (2 palabras + palo) ---
        if i + 1 < n:
            c1_list = phonetics[i]
            c2_list = phonetics[i+1]
            if 'A' in c1_list and 'S' in c2_list:
                # Comprobar si hay palabra de palo inmediatamente posterior
                if i + 2 < n:
                    suit_candidates = phonetics[i+2]
                    for s_code in ['P', 'C', 'D', 'T']:
                        if s_code in suit_candidates:
                            matches.append({
                                'detected': True,
                                'value': 'A',
                                'valueName': 'As',
                                'suit': SUIT_PATTERNS[s_code],
                                'suitCode': s_code,
                                'valuePattern': 'AS',
                                'matchedWords': words[i:i+3],
                                'startIdx': i,
                                'endIdx': i+3,
                                'confidence': 1
                            })

        # --- Patron Estandar de Valor (3 palabras + 1 palo) ---
        if i + 2 < n:
            for c1 in phonetics[i]:
                for c2 in phonetics[i+1]:
                    for c3 in phonetics[i+2]:
                        pat = c1 + c2 + c3
                        if pat in VALUE_PATTERNS:
                            val = VALUE_PATTERNS[pat]
                            val_name = VALUE_NAMES[val]
                            
                            # Comprobar si existe palabra de palo inmediatamente posterior (4a palabra)
                            if i + 3 < n:
                                suit_candidates = phonetics[i+3]
                                for s_code in ['P', 'C', 'D', 'T']:
                                    if s_code in suit_candidates:
                                        matches.append({
                                            'detected': True,
                                            'value': val,
                                            'valueName': val_name,
                                            'suit': SUIT_PATTERNS[s_code],
                                            'suitCode': s_code,
                                            'valuePattern': pat,
                                            'matchedWords': words[i:i+4],
                                            'startIdx': i,
                                            'endIdx': i+4,
                                            'confidence': 1
                                        })

    if not matches:
        return {'detected': False}

    # Seleccionar la coincidencia mas reciente que tenga valor + palo
    matches.sort(key=lambda m: (m['endIdx'], m['startIdx']), reverse=True)
    best = matches[0]
    del best['startIdx']
    del best['endIdx']
    return best

if __name__ == "__main__":
    ejemplos = [
        ("Hombre, no creo probable que sea una respuesta correcta.", "J de Picas"),
        ("De otro sitio perfecto...", "2 de Picas"),
        ("Tiene respuesta evidente...", "Sin carta (falta palo)"),
        ("Tiene respuesta evidente probablemente...", "3 de Picas"),
        ("Cada uno adivina...", "Sin carta (falta palo)"),
        ("Cada instante noto...", "Sin carta (falta palo)"),
        ("Siempre encuentra indicios...", "Sin carta (falta palo)"),
        ("Siempre intenta estar tranquilo...", "7 de Tréboles"),
        ("O como hoy parece...", "8 de Picas"),
        ("Nunca uso explicaciones...", "Sin carta (falta palo)"),
        ("De inmediato encaja...", "Sin carta (falta palo)"),
        ("Dos cosas coinciden...", "Sin carta (falta palo)"),
        ("Realmente es increíble...", "Sin carta (falta palo)"),
        ("Ahora sí parece...", "As de Picas"),
        ("Ha sido perfecto...", "As de Picas"),
    ]

    fallos = 0
    for frase, esperado in ejemplos:
        r = detectCardFromSpeech(frase)
        if r['detected']:
            obtenido = f"{r['valueName']} de {PALO_NOMBRES[r['suit']]}"
        else:
            obtenido = "Sin carta (falta palo)"
        ok = (obtenido == esperado)
        if not ok:
            fallos += 1
        tag = "[OK]" if ok else "[FAIL]"
        print(f"{tag} '{frase}' -> {obtenido} (Esperado: {esperado})")

    print(f"\nResultado de la prueba inicial: {len(ejemplos) - fallos} / {len(ejemplos)} pasados.")
