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
    COLETILLAS,
    PALOS,
    RANGOS
)

app = FastAPI(
    title="API REST — Código Verbal Mentalismo",
    description="Servicio web para decodificar cartas de póker a partir de frases verbales y gestionar la configuración de coletillas por palo.",
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

# Configuración global en memoria de coletillas activas (inicializada desde codigo_carta.py)
CONFIG_COLETILLAS: Dict[str, List[str]] = {
    palo_id: list(expresiones) for palo_id, expresiones in COLETILLAS.items()
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


# Estado en memoria de la carta activa en el servidor (por defecto As de Corazones)
CARTA_ACTUAL = {
    "valor": "A",
    "palo_id": "corazones",
    "palo_nombre": "Corazones",
    "simbolo": "♥",
    "frase": "Ahora sí correcto",
    "coletilla": "C",
    "n_palabras": 3,
    "version": 1
}


def actualizar_estado_carta(res: dict, frase: str):
    """Actualiza silenciosamente la carta activa en el servidor sin recargar la web."""
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
                "n_palabras": res.get("n_palabras", len(res.get("matchedWords", []))),
                "version": CARTA_ACTUAL.get("version", 0) + 1
            }


@app.get(
    "/api/carta_actual",
    summary="Obtener la carta activa almacenada en el servidor",
    tags=["Mentalismo"]
)
def obtener_carta_actual():
    """Retorna la última carta decodificada en el servidor."""
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
    res = analizar_frase(frase, coletillas=CONFIG_COLETILLAS)
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
    coletillas_a_usar = body.coletillas if body.coletillas is not None else CONFIG_COLETILLAS
    res = analizar_frase(body.frase, coletillas=coletillas_a_usar)

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
    response_model=RespuestaConfiguracion,
    summary="Obtener configuración de coletillas y palos",
    tags=["Configuración de Palos"]
)
def obtener_configuracion():
    """Retorna la lista actual de palabras/coletillas configuradas para cada palo."""
    palos_formatted = {palo_id: PaloInfo(**data) for palo_id, data in PALOS.items()}
    return RespuestaConfiguracion(
        coletillas=CONFIG_COLETILLAS,
        palos_disponibles=palos_formatted
    )


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
        frase = "Ahora sí correcto"
        res = analizar_frase(frase, coletillas=CONFIG_COLETILLAS)

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

            /* Indicador Secreto del Mago Mimetizado con el Marco Cromado */
            .secret-peek {{
                position: absolute;
                bottom: 30px;
                left: 25px;
                font-family: 'Cinzel', monospace, sans-serif;
                font-size: 7.5px;
                font-weight: 400;
                color: rgba(168, 143, 88, 0.45);
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
                letter-spacing: 1px;
                pointer-events: none;
                user-select: none;
                -webkit-user-select: none;
                z-index: 99999;
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

            <!-- Indicador Secreto del Mago en Primer Plano dentro del Escenario -->
            <div class="secret-peek" id="secretPeek">{card_valor}{simbolo}</div>
        </div>

        <script>
            let currentVersion = -1;
            const cardScene = document.getElementById('cardScene');
            const imgFront = document.getElementById('imgFront');
            const secretPeek = document.getElementById('secretPeek');

            function toggleCard() {{
                cardScene.classList.toggle('volteada');
            }}

            cardScene.addEventListener('click', toggleCard);

            // Polling silencioso en segundo plano sin recargar ni girar la carta automáticamente
            async function consultarEstadoSilencioso() {{
                try {{
                    const res = await fetch('/api/carta_actual');
                    if (res.ok) {{
                        const data = await res.json();
                        if (data.version && data.version !== currentVersion) {{
                            currentVersion = data.version;
                            // Actualizar la carta de frente y el indicador sutil del mago en silencio
                            imgFront.src = `/cartas_svg/${{data.valor}}_${{data.palo_id}}.svg`;
                            secretPeek.textContent = `${{data.valor}}${{data.simbolo}}`;
                        }}
                    }}
                }} catch (err) {{
                    console.log('Sync err:', err);
                }}
            }}

            setInterval(consultarEstadoSilencioso, 1000);
            consultarEstadoSilencioso();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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

