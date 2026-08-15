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
    html_vis = res_vis.text
    assert "setInterval" not in html_vis, "Error: Se detectó setInterval en el HTML de /visualizar"
    assert "handleCardFlip" in html_vis
    assert "cardScene.addEventListener('dblclick', handleCardFlip)" in html_vis
    print("[OK] GET /visualizar (Vista HTML sin polling y con doble clic) verificado.")

    res_dec = client.get("/decodificador")
    assert res_dec.status_code == 200
    assert "text/html" in res_dec.headers["content-type"]
    print("[OK] GET /decodificador (Aplicación Web HTML) verificado.")

    res_voz = client.get("/probar_voz")
    assert res_voz.status_code == 200
    assert "text/html" in res_voz.headers["content-type"]
    assert "setInterval(sincronizarCartaQR, 400)" not in res_voz.text
    assert "btnQREscucharUI" in res_voz.text
    assert "QR ESCUCHAR" in res_voz.text
    print("[OK] GET /probar_voz (Prueba de Voz con botones QR Visualizar y QR Escuchar) verificado.")

    res_esc = client.get("/escuchar")
    assert res_esc.status_code == 200
    assert "text/html" in res_esc.headers["content-type"]
    html_esc = res_esc.text
    assert "setInterval" not in html_esc, "Error: Se detectó setInterval en el HTML de /escuchar"
    assert "ACTIVATION_WORD" in html_esc
    assert "LISTO" in html_esc
    assert "speechSynthesis" in html_esc
    print("[OK] GET /escuchar (Vista HTML de revelación por audio sin polling) verificado.")

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

def test_redis_y_errores():
    import os
    from unittest.mock import patch, MagicMock

    # Test 1: Verificar que sin REDIS_URL devuelve el estado actual local
    res_actual = client.get("/api/carta_actual")
    assert res_actual.status_code == 200
    assert "valor" in res_actual.json()
    print("[OK] GET /api/carta_actual sin REDIS_URL recupera el estado de desarrollo local.")

    # Test 2: Simular error de conexión a Redis y verificar fallback transparente a CARTA_ACTUAL (HTTP 200)
    with patch.dict(os.environ, {"REDIS_URL": "redis://fake_invalid_host:6379"}):
        with patch("app.upstash_redis_get", return_value=None):
            res_fb = client.get("/api/carta_actual")
            assert res_fb.status_code == 200
            assert "valor" in res_fb.json()
            print("[OK] GET /api/carta_actual con Redis no disponible realiza fallback transparente sin romper el servicio (HTTP 200).")

    # Test 3: Simular Redis funcional y verificar lectura/escritura de clave 'codigo-carta:current-card'
    mock_json = '{"valor": "K", "palo_id": "picas", "palo_nombre": "Picas", "simbolo": "♠"}'
    with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
        with patch("app.upstash_redis_get", return_value=mock_json):
            res_mock = client.get("/api/carta_actual")
            assert res_mock.status_code == 200
            data_mock = res_mock.json()
            assert data_mock["valor"] == "K"
            assert data_mock["palo_id"] == "picas"
            print("[OK] GET /api/carta_actual recupera correctamente el estado desde la clave Redis 'codigo-carta:current-card'.")

if __name__ == "__main__":
    test_health()
    test_decodificar_get_exito()
    test_decodificar_get_error_sin_palo()
    test_decodificar_post_kw()
    test_obtener_configuracion()
    test_endpoints_visuales()
    test_decodificar_palabra_clave()
    test_redis_y_errores()
    print("\n[OK] TODAS LAS PRUEBAS DE LA API REST Y REDIS PASARON CON ÉXITO.")

