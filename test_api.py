"""
Pruebas de la API REST de Decodificación de Cartas usando el nuevo motor de palabras clave directas
"""

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("[OK] GET /health funcionando correctamente.")

def test_decodificar_get_exito():
    # regular (J) + sacado (picas) -> J de Picas
    response = client.get("/api/decodificar?frase=Hablando del elemento regular que fue sacado")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["valor"] == "J"
    assert data["palo_id"] == "picas"
    assert data["palo"]["simbolo"] == "♠"
    print("[OK] GET /api/decodificar exito: J de Picas verificado.")

def test_decodificar_get_error_sin_palo():
    # ahora (2 sin palabra de palo) -> No confirma carta (error)
    response = client.get("/api/decodificar?frase=Hola ahora estamos viendo")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is False
    assert "error" in data
    print("[OK] GET /api/decodificar sin palabra de palo verificado.")

def test_decodificar_post_kw():
    # ahora (2) + sacado (picas) -> 2 de Picas
    payload = {
        "frase": "Viendo que ahora fue sacado de la baraja"
    }
    response = client.post("/api/decodificar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["valor"] == "2"
    assert data["palo_id"] == "picas"
    print("[OK] POST /api/decodificar verificado.")

def test_obtener_configuracion():
    get_res = client.get("/api/config")
    assert get_res.status_code == 200
    print("[OK] GET /api/config verificado.")

def test_endpoints_visuales():
    res_svg = client.get("/api/carta/svg?valor=5&palo_id=treboles&raw=true")
    assert res_svg.status_code == 200
    assert "image/svg+xml" in res_svg.headers["content-type"]
    print("[OK] GET /api/carta/svg (Imagen SVG de carta) verificado.")

    res_vis = client.get("/visualizar")
    assert res_vis.status_code == 200
    assert "text/html" in res_vis.headers["content-type"]
    print("[OK] GET /visualizar (Vista HTML de carta) verificado.")

    res_dec = client.get("/decodificador")
    assert res_dec.status_code == 200
    assert "text/html" in res_dec.headers["content-type"]
    print("[OK] GET /decodificador (Aplicación Web HTML) verificado.")

    res_voz = client.get("/probar_voz")
    assert res_voz.status_code == 200
    assert "text/html" in res_voz.headers["content-type"]
    print("[OK] GET /probar_voz (Prueba de Voz con Palabra Clave HTML) verificado.")

def test_decodificar_palabra_clave():
    # Palabra clave: "vale" -> ahora (2) + tomado (corazones) = 2 de Corazones (2♥)
    payload = {
        "texto": "estaba hablando normal y dije vale ahora hemos tomado el elemento",
        "palabra_clave": "vale"
    }
    response = client.post("/api/decodificar_palabra_clave", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["keywordFound"] is True
    assert data["keyword"] == "vale"
    assert data["valor"] == "2"
    assert data["palo_id"] == "corazones"
    assert data["palo"]["simbolo"] == "♥"
    print("[OK] POST /api/decodificar_palabra_clave (palabra clave 'vale' -> 2 de Corazones) verificado.")

if __name__ == "__main__":
    test_health()
    test_decodificar_get_exito()
    test_decodificar_get_error_sin_palo()
    test_decodificar_post_kw()
    test_obtener_configuracion()
    test_endpoints_visuales()
    test_decodificar_palabra_clave()
    print("\n[OK] TODAS LAS PRUEBAS DE LA API REST PASARON CON ÉXITO.")
