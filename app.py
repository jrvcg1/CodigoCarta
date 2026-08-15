"""
Servicio Web API REST para Decodificación de Cartas (Código Verbal)
====================================================================
API desarrollada con FastAPI que permite decodificar cartas de póker a partir de frases habladas
y configurar dinámicamente las palabras / coletillas asociadas a cada palo.
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from codigo_carta import (
    analizar_frase,
    VALOR_PALABRAS,
    PALO_PALABRAS,
    PALOS,
    RANGOS
)

app = FastAPI(
    title="API REST — Código Verbal Mentalismo",
    description="Servicio web para decodificar cartas de póker a partir de frases verbales.",
    version="1.0.0",
)

# Habilitar CORS para consumo desde aplicaciones frontend / decodificador.html
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PALABRAS = {
    "valores": VALOR_PALABRAS,
    "palos": PALO_PALABRAS
}

# Montar carpeta de cartas SVG realistas como estáticos
import os
from fastapi.staticfiles import StaticFiles
cartas_dir = os.path.join(os.path.dirname(__file__), "cartas_svg")
if os.path.exists(cartas_dir):
    app.mount("/cartas_svg", StaticFiles(directory=cartas_dir), name="cartas_svg")


# -------------------------------------------------------------------
# Modelos Pydantic para Request / Response
# -------------------------------------------------------------------

class PaloInfo(BaseModel):
    simbolo: str = Field(..., example="♣")
    nombre: str = Field(..., example="Tréboles")

class ResultadoDecodificación(BaseModel):
    exito: bool = Field(..., example=True)
    frase: str = Field(..., example="Yo creo que todo va bien")
    valor: Optional[str] = Field(None, example="5")
    palo_id: Optional[str] = Field(None, example="treboles")
    palo: Optional[PaloInfo] = None
    n_palabras: Optional[int] = Field(None, example=5)
    coletilla: Optional[str] = Field(None, example="bien")
    error: Optional[str] = None

class PeticionPostDecodificar(BaseModel):
    frase: str = Field(..., example="Yo creo que todo va bien", description="Frase hablada a decodificar")
    coletillas: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Coletillas personalizadas opcionales para esta petición específica",
        example={
            "diamantes": ["vale"],
            "corazones": ["genial"],
            "picas": ["perfecto"],
            "treboles": ["bien"]
        }
    )

class ConfiguracionColetillas(BaseModel):
    diamantes: Optional[List[str]] = Field(None, example=["vale", "ok"])
    corazones: Optional[List[str]] = Field(None, example=["genial", "fantástico"])
    picas: Optional[List[str]] = Field(None, example=["perfecto", "excelente"])
    treboles: Optional[List[str]] = Field(None, example=["bien", "correcto"])

class PeticionDecodificacionPalabraClave(BaseModel):
    texto: str = Field(..., description="Texto reconocido por voz", example="estaba hablando y dije vale de otro sitio cabría esperar")
    palabra_clave: str = Field("vale", description="Palabra clave activadora (ej. 'vale')", example="vale")
    valor: Optional[str] = Field(None, description="Valor explícito detectado por el cliente", example="9")
    palo_id: Optional[str] = Field(None, description="Palo ID explícito detectado por el cliente", example="corazones")

class RespuestaConfiguracion(BaseModel):
    coletillas: Dict[str, List[str]]
    palos_disponibles: Dict[str, PaloInfo]


# -------------------------------------------------------------------
# Endpoints de la API REST
# -------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def inicio():
    """Redirige automáticamente a la documentación interactiva Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Estado"])
def health_check():
    """Comprobación de estado del servicio."""
    return {"status": "ok", "service": "API REST Código Verbal"}


# Historial de logs en tiempo real para monitoreo durante pruebas
EVENT_LOGS = []

class LogPayload(BaseModel):
    event: str
    details: Optional[dict] = None

@app.post("/api/log_event", tags=["Monitoreo"])
def registrar_evento_log(payload: LogPayload):
    """Registra eventos de voz y decodificación para monitoreo en vivo."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {
        "time": timestamp,
        "event": payload.event,
        "details": payload.details or {}
    }
    EVENT_LOGS.append(entry)
    if len(EVENT_LOGS) > 200:
        EVENT_LOGS.pop(0)

    try:
        with open("live_events.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {payload.event}: {payload.details}\n")
    except Exception:
        pass

    return {"status": "ok", "total_logs": len(EVENT_LOGS)}


@app.get("/api/redis_status", tags=["Estado"])
def check_redis_status():
    """Diagnóstico del estado de conexión a Redis en Vercel."""
    has_redis_url = bool(os.environ.get("REDIS_URL"))
    has_rest_url = bool(os.environ.get("UPSTASH_REDIS_REST_URL"))
    has_rest_token = bool(os.environ.get("UPSTASH_REDIS_REST_TOKEN"))
    redis_url_effective = get_redis_url()
    
    redis_val = upstash_redis_get(REDIS_KEY_CURRENT_CARD)
    
    return {
        "has_redis_url": has_redis_url,
        "has_rest_url": has_rest_url,
        "has_rest_token": has_rest_token,
        "redis_configured": bool(redis_url_effective),
        "redis_value_read": redis_val,
        "memory_value": CARTA_ACTUAL
    }


@app.get("/api/logs", tags=["Monitoreo"])
def obtener_logs(limit: int = 50):
    """Retorna los últimos eventos registrados para monitoreo."""
    return {"logs": EVENT_LOGS[-limit:]}


import json
import datetime

REDIS_KEY_CURRENT_CARD = "codigo-carta:current-card"

def get_redis_url():
    url = os.environ.get("REDIS_URL")
    if url:
        return url
    rest_url = os.environ.get("UPSTASH_REDIS_REST_URL")
    rest_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if rest_url and rest_token:
        # Extraer host desde la URL de REST (ej: https://champion-buzzard-90975.upstash.io)
        host = rest_url.replace("https://", "").replace("http://", "").strip("/")
        return f"rediss://default:{rest_token}@{host}:6379"
    return None

def get_redis_client():
    redis_url = get_redis_url()
    if not redis_url:
        return None
def upstash_redis_get(key: str) -> Optional[str]:
    rest_url = os.environ.get("UPSTASH_REDIS_REST_URL")
    rest_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    redis_url = os.environ.get("REDIS_URL")

    if not (rest_url and rest_token) and redis_url and "rediss://default:" in redis_url:
        try:
            parts = redis_url.replace("rediss://default:", "").split("@")
            rest_token = parts[0]
            host_port = parts[1].split(":")[0]
            rest_url = f"https://{host_port}"
        except Exception:
            pass

    if rest_url and rest_token:
        try:
            import urllib.request
            url = f"{rest_url.rstrip('/')}/"
            payload = json.dumps(["GET", key]).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {rest_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    return data.get("result")
        except Exception as e:
            print(f"[UPSTASH REST GET ERROR] {e}")

    try:
        import redis
        url = redis_url or get_redis_url()
        if url:
            r = redis.from_url(url, decode_responses=True, socket_timeout=3.0)
            return r.get(key)
    except Exception as e:
        print(f"[REDIS GET ERROR] {e}")

    return None


def upstash_redis_set(key: str, value_str: str) -> bool:
    rest_url = os.environ.get("UPSTASH_REDIS_REST_URL")
    rest_token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    redis_url = os.environ.get("REDIS_URL")

    if not (rest_url and rest_token) and redis_url and "rediss://default:" in redis_url:
        try:
            parts = redis_url.replace("rediss://default:", "").split("@")
            rest_token = parts[0]
            host_port = parts[1].split(":")[0]
            rest_url = f"https://{host_port}"
        except Exception:
            pass

    if rest_url and rest_token:
        try:
            import urllib.request
            url = f"{rest_url.rstrip('/')}/"
            payload = json.dumps(["SET", key, value_str]).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {rest_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    return True
        except Exception as e:
            print(f"[UPSTASH REST SET ERROR] {e}")

    try:
        import redis
        url = redis_url or get_redis_url()
        if url:
            r = redis.from_url(url, decode_responses=True, socket_timeout=3.0)
            r.set(key, value_str)
            return True
    except Exception as e:
        print(f"[REDIS SET ERROR] {e}")

    return False


# Estado en memoria de la carta activa en el servidor (por defecto As de Corazones)
CARTA_ACTUAL = {
    "valor": "A",
    "palo_id": "corazones",
    "palo_nombre": "Corazones",
    "simbolo": "♥",
    "frase": "Ahora sí correcto",
    "coletilla": "C",
    "n_palabras": 3,
    "version": 1,
    "updated_at": datetime.datetime.now().isoformat()
}


def actualizar_estado_carta(res: dict, frase: str):
    """Actualiza la carta activa en la memoria local y en la clave de Redis 'codigo-carta:current-card'."""
    if "error" not in res:
        global CARTA_ACTUAL
        val = res.get("valor") or res.get("value")
        suit_id = res.get("palo_id") or res.get("suit")
        palo_info = res.get("palo") if isinstance(res.get("palo"), dict) else PALOS.get(suit_id, {})

        if val and suit_id:
            CARTA_ACTUAL = {
                "valor": str(val),
                "palo_id": suit_id,
                "palo_nombre": palo_info.get("nombre", suit_id),
                "simbolo": palo_info.get("simbolo", ""),
                "frase": frase,
                "coletilla": res.get("coletilla", res.get("suitCode", "")),
                "n_palabras": res.get("n_palabras", 2),
                "version": CARTA_ACTUAL.get("version", 1) + 1,
                "updated_at": datetime.datetime.now().isoformat()
            }
            # Persistencia en Redis (clave 'codigo-carta:current-card')
            val_json = json.dumps(CARTA_ACTUAL, ensure_ascii=False)
            upstash_redis_set(REDIS_KEY_CURRENT_CARD, val_json)


@app.get(
    "/api/carta_actual",
    summary="Obtener la carta activa almacenada en Redis o servidor",
    tags=["Mentalismo"]
)
def obtener_carta_actual():
    """Retorna la última carta decodificada almacenada en Redis o en memoria."""
    try:
        data_str = upstash_redis_get(REDIS_KEY_CURRENT_CARD)
        if data_str:
            return json.loads(data_str)
    except Exception as e:
        print(f"[CARTA ACTUAL ERROR] {e}")

    return CARTA_ACTUAL


@app.get(
    "/api/decodificar",
    response_model=ResultadoDecodificación,
    summary="Decodificar carta a partir de una frase (GET)",
    tags=["Decodificación"]
)
def decodificar_get(
    frase: str = Query(
        ...,
        description="Frase completa codificada (ej: 'Yo creo que todo va bien')",
        example="Yo creo que todo va bien"
    )
):
    """
    Interpreta una frase completa para determinar la carta de póker codificada (Valor + Palo).
    Actualiza silenciosamente el estado del servidor para la pantalla en directo.
    """
    res = analizar_frase(frase)
    if "error" in res:
        return ResultadoDecodificación(
            exito=False,
            frase=frase,
            error=res["error"]
        )

    actualizar_estado_carta(res, frase)

    return ResultadoDecodificación(
        exito=True,
        frase=frase,
        valor=res["valor"],
        palo_id=res["palo_id"],
        palo=PaloInfo(**res["palo"]),
        n_palabras=res["n_palabras"],
        coletilla=res["coletilla"]
    )


@app.post(
    "/api/decodificar",
    response_model=ResultadoDecodificación,
    summary="Decodificar carta a partir de una frase (POST)",
    tags=["Decodificación"]
)
def decodificar_post(body: PeticionPostDecodificar):
    """
    Interpreta una frase enviada por JSON POST.
    Actualiza silenciosamente el estado del servidor sin refrescar ninguna pantalla.
    """
    res = analizar_frase(body.frase)

    if "error" in res:
        return ResultadoDecodificación(
            exito=False,
            frase=body.frase,
            error=res["error"]
        )

    actualizar_estado_carta(res, body.frase)

    return ResultadoDecodificación(
        exito=True,
        frase=body.frase,
        valor=res["valor"],
        palo_id=res["palo_id"],
        palo=PaloInfo(**res["palo"]),
        n_palabras=res["n_palabras"],
        coletilla=res["coletilla"]
    )


@app.post(
    "/api/decodificar_palabra_clave",
    summary="Decodificar carta a partir de una palabra clave hablada (ej. 'vale')",
    tags=["Decodificación Fonética"]
)
def decodificar_palabra_clave(body: PeticionDecodificacionPalabraClave):
    """
    Busca la palabra clave (ej. 'vale') dentro del texto hablado y analiza
    las palabras subsecuentes para detectar la carta.
    Si se detecta una carta, actualiza el estado CARTA_ACTUAL para /visualizar.
    """
    from codigo_carta import detectCardWithKeyword
    res = detectCardWithKeyword(body.texto, body.palabra_clave)

    if res.get("detected"):
        actualizar_estado_carta(res, body.texto)
        return {
            "exito": True,
            "keywordFound": True,
            "keyword": res.get("keyword"),
            "fullText": body.texto,
            "afterWords": res.get("afterWords"),
            "matchedWords": res.get("matchedWords"),
            "valor": res.get("value"),
            "palo_id": res.get("suit"),
            "palo": PALOS[res.get("suit")],
            "coletilla": res.get("suitCode"),
            "valuePattern": res.get("valuePattern")
        }

    return {
        "exito": False,
        "keywordFound": res.get("keywordFound", False),
        "keyword": res.get("keyword", body.palabra_clave),
        "fullText": body.texto,
        "afterWords": res.get("afterWords", []),
        "error": "No se detectó ninguna carta válida tras la palabra clave"
    }


@app.get(
    "/api/config",
    summary="Obtener configuración de palabras clave y palos",
    tags=["Configuración"]
)
def obtener_configuracion():
    """Retorna las palabras clave configuradas para valores y palos."""
    palos_formatted = {palo_id: PaloInfo(**data) for palo_id, data in PALOS.items()}
    return {
        "palabras": CONFIG_PALABRAS,
        "palos_disponibles": palos_formatted
    }


@app.put(
    "/api/config",
    response_model=RespuestaConfiguracion,
    summary="Actualizar coletillas por palo",
    tags=["Configuración de Palos"]
)
def actualizar_configuracion(nueva_config: ConfiguracionColetillas):
    """
    Actualiza la lista de palabras/coletillas asociadas a uno o varios palos.
    Las palabras no deben estar vacías.
    """
    datos = nueva_config.dict(exclude_unset=True)

    for palo_id, lista_palabras in datos.items():
        if lista_palabras is not None:
            limpias = [p.strip().lower() for p in lista_palabras if p and p.strip()]
            if not limpias:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La lista de coletillas para '{palo_id}' no puede estar vacía."
                )
            CONFIG_COLETILLAS[palo_id] = limpias

    palos_formatted = {palo_id: PaloInfo(**data) for palo_id, data in PALOS.items()}
    return RespuestaConfiguracion(
        coletillas=CONFIG_COLETILLAS,
        palos_disponibles=palos_formatted
    )


from fastapi import Request

@app.get(
    "/api/carta/svg",
    summary="Obtener imagen SVG vectorial de una carta o frase",
    tags=["Visualización"]
)
def obtener_carta_svg(
    request: Request,
    frase: Optional[str] = Query(None, description="Frase codificada (opcional)"),
    valor: Optional[str] = Query(None, description="Valor explicito (A, 2..10, J, Q, K)"),
    palo_id: Optional[str] = Query(None, description="Palo id (diamantes, corazones, picas, treboles)"),
    raw: Optional[bool] = Query(False, description="Si es True, devuelve la imagen SVG pura sin redirección web")
):
    """
    Retorna la experiencia web interactiva 3D con volteo (frente/dorso).
    Si se requiere la imagen SVG cruda (por ejemplo para <img src="...">), pasar `raw=true`.
    """
    if not raw:
        if frase:
            from urllib.parse import quote
            return RedirectResponse(url=f"/visualizar?frase={quote(frase)}")
        elif valor and palo_id:
            return RedirectResponse(url=f"/visualizar?valor={valor}&palo_id={palo_id}")
        return RedirectResponse(url="/visualizar")

    card_valor = "A"
    card_palo_id = "picas"

    if frase:
        res = analizar_frase(frase, coletillas=CONFIG_COLETILLAS)
        if "error" not in res:
            card_valor = res["valor"]
            card_palo_id = res["palo_id"]
    else:
        if valor: card_valor = valor.upper()
        if palo_id and palo_id in PALOS: card_palo_id = palo_id

    filename = f"{card_valor}_{card_palo_id}.svg"
    filepath = os.path.join(os.path.dirname(__file__), "cartas_svg", filename)

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            svg_content = f.read()
        return Response(content=svg_content, media_type="image/svg+xml")

    # Fallback si no existiera el archivo
    palo_info = PALOS.get(card_palo_id, PALOS["picas"])
    simbolo = palo_info["simbolo"]
    color = "#c14b4b" if card_palo_id in ["corazones", "diamantes"] else "#1e1e24"

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="240" height="340" viewBox="0 0 240 340">
  <rect x="5" y="5" width="230" height="330" rx="16" ry="16" fill="#fdfbf7" stroke="#d0c7b7" stroke-width="3" />
  <text x="22" y="42" font-family="'Courier New', monospace" font-weight="bold" font-size="28" fill="{color}">{card_valor}</text>
  <text x="22" y="68" font-family="sans-serif" font-size="24" fill="{color}">{simbolo}</text>
  <text x="120" y="180" font-family="sans-serif" font-size="80" text-anchor="middle" dominant-baseline="middle" fill="{color}">{simbolo}</text>
</svg>"""

    return Response(content=svg_content, media_type="image/svg+xml")


@app.get(
    "/visualizar",
    response_class=HTMLResponse,
    summary="Visualizar carta interactiva en HTML con volteo 3D",
    tags=["Visualización"]
)
def visualizar_carta(
    frase: Optional[str] = Query(None, description="Frase hablada a interpretar"),
    valor: Optional[str] = Query(None, description="Valor explicito de la carta"),
    palo_id: Optional[str] = Query(None, description="Palo de la carta")
):
    """
    Página HTML interactiva que muestra la carta de póker con animación 3D.
    Por defecto muestra el As de Corazones (A♥).
    """
    if frase:
        res = analizar_frase(frase, coletillas=CONFIG_COLETILLAS)
    elif valor and palo_id:
        res = {
            "valor": valor.upper(),
            "palo_id": palo_id,
            "palo": PALOS.get(palo_id, PALOS["corazones"]),
            "n_palabras": 3,
            "coletilla": "C"
        }
    else:
        # Carta por defecto: As de Corazones (A♥)
        frase = "antes tomado"
        res = analizar_frase(frase)

    # Si hay error en la frase dada, recurrir a la carta activa actual o As de Corazones
    if "error" in res:
        res = {
            "valor": CARTA_ACTUAL["valor"],
            "palo_id": CARTA_ACTUAL["palo_id"],
            "palo": PALOS.get(CARTA_ACTUAL["palo_id"], PALOS["corazones"]),
            "n_palabras": CARTA_ACTUAL.get("n_palabras", 3),
            "coletilla": CARTA_ACTUAL.get("coletilla", "C")
        }

    card_valor = res["valor"]
    palo_nombre = res["palo"]["nombre"]
    simbolo = res["palo"]["simbolo"]
    card_palo_id = res["palo_id"]
    coletilla = res.get("coletilla", "")

    frase_mostrar = frase if frase else f"Carta {card_valor} de {palo_nombre}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pantalla de Mentalismo</title>
        <style>
            * {{ box-sizing: border-box; }}
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background-color: #050308;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                user-select: none;
                -webkit-user-select: none;
            }}

            /* Contenedor del Cartel que escala manteniendo la proporción nativa del Póster (2:3) */
            .poster-container {{
                position: relative;
                width: min(96vw, 620px);
                height: min(96vh, 930px);
                aspect-ratio: 2 / 3;
                background: url('/cartas_svg/fondo_oraculo.jpg') no-repeat center center;
                background-size: 100% 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                box-shadow: 0 0 50px rgba(0,0,0,0.95);
            }}

            /* --- CONTENEDOR PRINCIPAL DE LA CARTA (PROPORCIÓN PÓKER REAL 63.5 / 88.9) --- */
            .card-scene {{
                perspective: 1200px;
                -webkit-perspective: 1200px;
                width: 52%;
                aspect-ratio: 63.5 / 88.9;
                margin-top: 8%;
                position: relative;
                cursor: pointer;
                z-index: 10;
                user-select: none;
                -webkit-user-select: none;
            }}

            /* Objeto 3D que gira (frente y dorso comparten el mismo tamaño exacto) */
            .card-object {{
                position: relative;
                width: 100%;
                height: 100%;
                -webkit-transform-style: preserve-3d;
                transform-style: preserve-3d;
                transition: transform 0.8s cubic-bezier(0.3, 1, 0.3, 1);
                -webkit-transition: -webkit-transform 0.8s cubic-bezier(0.3, 1, 0.3, 1);
            }}

            .card-scene:hover .card-object {{
                box-shadow: 0 0 35px rgba(212,175,55,0.45);
            }}

            .card-scene.volteada .card-object {{
                -webkit-transform: rotateY(180deg);
                transform: rotateY(180deg);
            }}

            /* Caras de la carta (Frente y Dorso exactamente iguales) */
            .card-face {{
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                border-radius: 4%;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.85);
            }}

            /* Cara frontal (blanco para las cartas SVG) */
            .card-front {{
                background: #ffffff;
                border: 1px solid rgba(212,175,55,0.45);
                -webkit-transform: rotateY(180deg);
                transform: rotateY(180deg);
            }}

            /* Cara posterior (dorso transparente sin recuadro blanco) */
            .card-back {{
                background: transparent;
                border: none;
                -webkit-transform: rotateY(0deg);
                transform: rotateY(0deg);
            }}

            /* Imágenes SVG dentro de cada cara (object-fit: contain) */
            .card-face img {{
                width: 100%;
                height: 100%;
                object-fit: contain;
                display: block;
                pointer-events: none;
            }}

            /* Cartel de error para Redis / HTTP 503 */
            .error-toast {{
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(220, 53, 69, 0.92);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-family: sans-serif;
                font-size: 14px;
                font-weight: bold;
                opacity: 0;
                transition: opacity 0.3s;
                pointer-events: none;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .error-toast.show {{
                opacity: 1;
            }}

        </style>
    </head>
    <body>
        <div class="poster-container">
            <!-- Objeto de Carta Interactiva 3D encajado en el marco del cartel -->
            <div class="card-scene" id="cardScene">
                <div class="card-object">
                    <!-- Frente de la Carta (SVG) -->
                    <div class="card-face card-front">
                        <img id="imgFront" src="/cartas_svg/{card_valor}_{card_palo_id}.svg" alt="Frente de la carta" />
                    </div>
                    <!-- Dorso de la Carta Bicycle Azul -->
                    <div class="card-face card-back">
                        <img src="/cartas_svg/dorso.svg" alt="Dorso de la Carta" />
                    </div>
                </div>
            </div>
        </div>

        <div id="errorToast" class="error-toast"></div>

        <script>
            const cardScene = document.getElementById('cardScene');
            const imgFront = document.getElementById('imgFront');
            const errorToast = document.getElementById('errorToast');
            let isFetching = false;

            function showErrorToast(msg) {{
                if (!errorToast) return;
                errorToast.textContent = msg;
                errorToast.classList.add('show');
                setTimeout(() => {{ errorToast.classList.remove('show'); }}, 3500);
            }}

            async function handleCardFlip(e) {{
                if (e) e.stopPropagation();

                // Si la carta está en el dorso (sin voltear), al hacer clic/doble clic realizamos UNA ÚNICA consulta a Redis
                if (!cardScene.classList.contains('volteada')) {{
                    if (isFetching) return;
                    isFetching = true;

                    try {{
                        const res = await fetch('/api/carta_actual?t=' + Date.now());
                        if (res.ok) {{
                            const data = await res.json();
                            if (data.valor && data.palo_id) {{
                                const newSrc = `/cartas_svg/${{data.valor}}_${{data.palo_id}}.svg`;
                                const tempImg = new Image();
                                tempImg.onload = () => {{
                                    imgFront.src = newSrc;
                                    cardScene.classList.add('volteada');
                                    isFetching = false;
                                }};
                                tempImg.onerror = () => {{
                                    imgFront.src = newSrc;
                                    cardScene.classList.add('volteada');
                                    isFetching = false;
                                }};
                                tempImg.src = newSrc;
                                return;
                            }}
                        }} else if (res.status === 503) {{
                            showErrorToast('Error HTTP 503: Servicio Redis no disponible');
                        }} else {{
                            showErrorToast('Error HTTP ' + res.status + ' al consultar la carta');
                        }}
                    }} catch (err) {{
                        console.error('Error de red al consultar carta:', err);
                        showErrorToast('Error de conexión con el servidor');
                    }}
                    isFetching = false;
                }} else {{
                    // Si ya está volteada mostrando el frente, la devolvemos al dorso sin hacer llamadas a Redis
                    cardScene.classList.remove('volteada');
                }}
            }}

            // Manejador de evento por doble clic y clic para voltear con consulta única a Redis
            cardScene.addEventListener('dblclick', handleCardFlip);
            cardScene.addEventListener('click', handleCardFlip);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


ACTIVATION_WORD = os.environ.get("ACTIVATION_WORD", "LISTO")


@app.get("/escuchar", response_class=HTMLResponse, summary="Página de Revelación por Audio", tags=["Visualización"])
def escuchar_web():
    """Servicio de la interfaz de revelación por audio (escuchar.html)."""
    html_path = os.path.join(os.path.dirname(__file__), "escuchar.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            content = content.replace("{{ ACTIVATION_WORD }}", ACTIVATION_WORD)
            return HTMLResponse(content=content)
    return HTMLResponse(content="Archivo escuchar.html no encontrado.", status_code=404)


@app.get("/decodificador", response_class=HTMLResponse, summary="Aplicación Web Decodificador con Micrófono", tags=["Visualización"])
def decodificador_web():
    """Servicio de la interfaz gráfica interactiva decodificador.html."""
    html_path = os.path.join(os.path.dirname(__file__), "decodificador.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Archivo decodificador.html no encontrado.", status_code=404)


@app.get("/probar_voz", response_class=HTMLResponse, summary="Prueba de Reconocimiento de Voz con Palabra Clave", tags=["Visualización"])
def probar_voz_web():
    """Servicio de la interfaz gráfica de pruebas de voz con palabra clave (probar_voz.html)."""
    html_path = os.path.join(os.path.dirname(__file__), "probar_voz.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    # Si no existe probar_voz.html, devolver decodificador.html
    html_path_fallback = os.path.join(os.path.dirname(__file__), "decodificador.html")
    if os.path.exists(html_path_fallback):
        with open(html_path_fallback, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="Archivo de interfaz no encontrado.", status_code=404)


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

