"""
Pruebas de la API REST de Decodificación de Cartas usando el nuevo motor fonético
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
    # Hombre (O) + no (N) + creo (C) + probable (P) -> J de Picas
    response = client.get("/api/decodificar?frase=Hombre no creo probable")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["valor"] == "J"
    assert data["palo_id"] == "picas"
    assert data["palo"]["simbolo"] == "♠"
    assert data["coletilla"] == "P"
    print("[OK] GET /api/decodificar exito: J de Picas fonetico verificado.")

def test_decodificar_get_error_sin_palo():
    # De otro sitio (DOS sin palo) -> No confirma carta (error)
    response = client.get("/api/decodificar?frase=De otro sitio")
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is False
    assert "error" in data
    print("[OK] GET /api/decodificar sin palabra de palo verificado.")

def test_decodificar_post_fonetico():
    # De (D) + otro (O) + sitio (S) + perfecto (P) -> 2 de Picas
    payload = {
        "frase": "De otro sitio perfecto que va ocurriendo"
    }
    response = client.post("/api/decodificar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["exito"] is True
    assert data["valor"] == "2"
    assert data["palo_id"] == "picas"
    assert data["coletilla"] == "P"
    print("[OK] POST /api/decodificar fonetico verificado.")

def test_obtener_configuracion():
    get_res = client.get("/api/config")
    assert get_res.status_code == 200
    assert "coletillas" in get_res.json()
    print("[OK] GET /api/config verificado.")

def test_endpoints_visuales():
    res_svg = client.get("/api/carta/svg?valor=5&palo_id=treboles&raw=true")
    assert res_svg.status_code == 200
    assert "image/svg+xml" in res_svg.headers["content-type"]
    assert "<svg" in res_svg.text
    print("[OK] GET /api/carta/svg (Imagen SVG de carta) verificado.")

    res_vis = client.get("/visualizar?frase=Hombre no creo probable")
    assert res_vis.status_code == 200
    assert "text/html" in res_vis.headers["content-type"]
    assert "3D" in res_vis.text
    print("[OK] GET /visualizar (Vista HTML de carta) verificado.")

    res_dec = client.get("/decodificador")
    assert res_dec.status_code == 200
    assert "text/html" in res_dec.headers["content-type"]
    print("[OK] GET /decodificador (Aplicacion Web HTML) verificado.")

if __name__ == "__main__":
    test_health()
    test_decodificar_get_exito()
    test_decodificar_get_error_sin_palo()
    test_decodificar_post_fonetico()
    test_obtener_configuracion()
    test_endpoints_visuales()
    print("\n[OK] TODAS LAS PRUEBAS DE LA API REST PASARON CON EXITO.")
