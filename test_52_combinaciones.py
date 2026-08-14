import sys
from codigo_carta import detectCardFromSpeech, detectCardWithKeyword

VALORES_TEST = {
    "A": "antes",
    "2": "ahora",
    "3": "luego",
    "4": "después",
    "5": "nada",
    "6": "poco",
    "7": "mucho",
    "8": "demasiado",
    "9": "todo",
    "10": "mal",
    "J": "regular",
    "Q": "bien",
    "K": "perfecto"
}

PALOS_TEST = {
    "treboles": "cogido",
    "picas": "sacado",
    "diamantes": "elegido",
    "corazones": "tomado"
}

def test_52_combinaciones():
    total = 0
    exitos = 0
    for val, val_word in VALORES_TEST.items():
        for suit_id, suit_word in PALOS_TEST.items():
            total += 1
            # Probar Orden 1: valor + palo
            frase1 = f"Vale, hemos visto que {val_word} está {suit_word} aquí."
            res1 = detectCardWithKeyword(frase1, "vale")
            
            # Probar Orden 2: palo + valor
            frase2 = f"Vale, el elemento {suit_word} era {val_word} en el juego."
            res2 = detectCardWithKeyword(frase2, "vale")
            
            ok1 = (res1.get('detected') is True and 
                   str(res1.get('value')) == val and 
                   res1.get('suit') == suit_id)

            ok2 = (res2.get('detected') is True and 
                   str(res2.get('value')) == val and 
                   res2.get('suit') == suit_id)
            
            if ok1 and ok2:
                exitos += 1
            else:
                print(f"[ERROR 52] val={val}, suit={suit_id} -> r1={res1}, r2={res2}")
                
    print(f"Prueba de 52 combinaciones (ambos órdenes): {exitos} / {total} pasadas correctamente.")
    assert exitos == total

def test_casos_borde():
    casos = [
        # Mayúsculas y minúsculas mixtas
        ("VALE lo que AHORA hemos TOMADO de la mesa", True, "2", "corazones"),
        ("vale, el objeto SACADO ANTES era tuyo", True, "A", "picas"),
        
        # Tildes y puntuación compleja
        ("¡Vale! ¿Se ha ELEGIDO bien el elemento?", True, "Q", "diamantes"),
        ("¡¡¡VALE, NADA ESTÁ COGIDO AÚN!!!", True, "5", "treboles"),
        
        # Frase larga de magia / mentalismo
        ("Hola a todos, bienvenido al show. Vale lo que hemos visto ahora está completamente tomado por la mente del espectador.", True, "2", "corazones"),
        
        # Palabras de palo y valor en orden inverso
        ("Vale, el papel cogido fue perfecto para el experimento.", True, "K", "treboles"),
        
        # Sin palabra clave -> detected False
        ("lo que ahora hemos tomado", False, None, None),
        
        # Con palabra clave pero incompleto
        ("Vale, lo que ahora estamos viendo...", False, None, None),
    ]

    total = len(casos)
    exitos = 0
    for frase, exp_detected, exp_val, exp_suit in casos:
        res = detectCardWithKeyword(frase, "vale")
        if exp_detected:
            ok = (res.get('detected') is True and 
                  str(res.get('value')) == exp_val and 
                  res.get('suit') == exp_suit)
        else:
            ok = (res.get('detected') is False)

        if ok:
            exitos += 1
        else:
            print(f"[ERROR BORDE] Frase: '{frase}' -> Obtenido: {res}")

    print(f"Prueba de casos borde: {exitos} / {total} pasados correctamente.")
    assert exitos == total

if __name__ == "__main__":
    test_52_combinaciones()
    test_casos_borde()
