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
        CARTA_ACTUAL = {
            "valor": res["valor"],
            "palo_id": res["palo_id"],
            "palo_nombre": res["palo"]["nombre"],
            "simbolo": res["palo"]["simbolo"],
            "frase": frase,
            "coletilla": res.get("coletilla", ""),
            "n_palabras": res.get("n_palabras", 0),
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
        <title>Pantalla de Mentalismo — Carta Interactiva</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Rye&family=Cinzel+Decorative:wght@700;900&family=Cinzel:wght@600;700;900&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap');

            :root {{
                --bg-deep: #050308;
                --maroon-dark: #2a080d;
                --maroon: #4a0d17;
                --gold-bright: #fbe394;
                --gold: #d4af37;
                --gold-dark: #8c6d17;
                --gold-shadow: rgba(212, 175, 55, 0.25);
                --text-ivory: #f7f1e3;
                --text-muted: #b8a6c9;
                --border-filigree: rgba(212, 175, 55, 0.4);
            }}
            * {{ box-sizing: border-box; }}
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                min-height: 100vh;
                background-color: var(--bg-deep);
                color: var(--text-ivory);
                font-family: 'Playfair Display', serif;
                overflow-x: hidden;
            }}

            /* --- Animación de Entrada Teatral --- */
            @keyframes stageEntrance {{
                0% {{ opacity: 0; transform: scale(0.98); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}
            @keyframes floatEmbers {{
                0% {{ transform: translateY(0) rotate(0deg); opacity: 0; }}
                50% {{ opacity: 0.6; }}
                100% {{ transform: translateY(-80px) rotate(45deg); opacity: 0; }}
            }}
            @keyframes bulbFlicker {{
                0%, 100% {{ opacity: 1; box-shadow: 0 0 10px #ffb300, 0 0 20px #ff8f00; }}
                92% {{ opacity: 1; }}
                93% {{ opacity: 0.4; box-shadow: 0 0 2px #ff8f00; }}
                94% {{ opacity: 1; }}
            }}

            .stage-wrapper {{
                min-height: 100vh;
                position: relative;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 30px 20px;
                animation: stageEntrance 1.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                background: 
                    radial-gradient(ellipse at 50% 45%, rgba(212, 175, 55, 0.12) 0%, rgba(74, 13, 23, 0.35) 45%, rgba(5, 3, 8, 0.95) 85%),
                    linear-gradient(to bottom, rgba(5, 3, 8, 0.6), rgba(5, 3, 8, 0.9));
            }}

            /* Cortinas de Terciopelo Rojo Oscuro en los Laterales */
            .curtains-left, .curtains-right {{
                position: fixed;
                top: 0;
                bottom: 0;
                width: min(150px, 15vw);
                pointer-events: none;
                z-index: 2;
            }}
            .curtains-left {{
                left: 0;
                background: linear-gradient(to right, #38070e 0%, #1f0307 70%, transparent 100%);
                border-right: 1px solid rgba(212, 175, 55, 0.15);
            }}
            .curtains-right {{
                right: 0;
                background: linear-gradient(to left, #38070e 0%, #1f0307 70%, transparent 100%);
                border-left: 1px solid rgba(212, 175, 55, 0.15);
            }}

            /* Marco Ornamental Vaudeville / Gran Circo */
            .theater-poster {{
                width: 100%;
                max-width: 900px;
                position: relative;
                border: 2px solid var(--gold);
                outline: 1px solid var(--gold-dark);
                outline-offset: 4px;
                border-radius: 12px;
                background: rgba(10, 6, 18, 0.88);
                backdrop-filter: blur(8px);
                padding: 36px 24px;
                box-shadow: 0 0 80px rgba(0,0,0,0.95), inset 0 0 50px rgba(0,0,0,0.8), 0 0 30px var(--gold-shadow);
                display: flex;
                flex-direction: column;
                align-items: center;
                z-index: 5;
            }}

            /* Esquinas Ornamentales Victorianas en SVG */
            .corner-filigree {{
                position: absolute;
                width: 32px;
                height: 32px;
                color: var(--gold);
                opacity: 0.85;
                pointer-events: none;
            }}
            .corner-tl {{ top: 8px; left: 8px; }}
            .corner-tr {{ top: 8px; right: 8px; transform: scaleX(-1); }}
            .corner-bl {{ bottom: 8px; left: 8px; transform: scaleY(-1); }}
            .corner-br {{ bottom: 8px; right: 8px; transform: scale(-1); }}

            /* Ojo del Oráculo Superior */
            .oracle-eye {{
                font-size: 24px;
                color: var(--gold);
                margin-bottom: 6px;
                text-shadow: 0 0 15px var(--gold);
                opacity: 0.9;
            }}

            /* Marquesina con Bombillas (El Gran Oráculo) */
            .marquee-box {{
                position: relative;
                border: 3px double var(--gold);
                border-radius: 50px;
                padding: 16px 38px;
                background: linear-gradient(180deg, #24070d 0%, #120306 100%);
                box-shadow: inset 0 0 20px rgba(0,0,0,0.9), 0 5px 25px rgba(0,0,0,0.8);
                margin-bottom: 20px;
                text-align: center;
            }}
            .marquee-bulbs {{
                position: absolute;
                inset: -7px;
                border-radius: 54px;
                pointer-events: none;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 10px;
            }}
            .bulb {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #fff4cc;
                box-shadow: 0 0 8px #ffb300, 0 0 16px #ff8f00;
                animation: bulbFlicker 4s infinite;
            }}
            .bulb:nth-child(2n) {{ animation-delay: 0.7s; }}
            .bulb:nth-child(3n) {{ animation-delay: 1.5s; }}

            .title-main {{
                font-family: 'Cinzel Decorative', 'Rye', serif;
                font-size: clamp(24px, 5vw, 40px);
                font-weight: 900;
                letter-spacing: 3px;
                margin: 0;
                background: linear-gradient(180deg, var(--gold-bright) 0%, var(--gold) 60%, var(--gold-dark) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-transform: uppercase;
                text-shadow: 0 3px 12px rgba(0,0,0,0.9);
            }}
            .title-sub {{
                font-family: 'Cinzel', serif;
                font-size: 11px;
                letter-spacing: 3px;
                color: var(--gold-bright);
                margin-top: 6px;
                text-transform: uppercase;
                opacity: 0.9;
            }}

            /* Mensaje del Misterio con Manos Apuntando */
            .mystery-header {{
                text-align: center;
                margin-bottom: 22px;
            }}
            .mystery-title {{
                font-family: 'Cinzel', serif;
                font-size: clamp(14px, 3vw, 19px);
                font-weight: 700;
                color: var(--gold-bright);
                letter-spacing: 2px;
                text-transform: uppercase;
                margin: 0 0 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}
            .mystery-title span {{ color: var(--gold); font-size: 16px; }}
            .mystery-instruction {{
                font-family: 'Playfair Display', serif;
                font-style: italic;
                font-size: 13px;
                color: var(--text-muted);
                letter-spacing: 1px;
                margin: 0;
            }}
            .mystery-instruction span {{ color: var(--gold); margin: 0 6px; }}

            /* Layout Escénico con Carteles Laterales en Desktop */
            .stage-layout {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 30px;
                width: 100%;
                margin: 10px 0 20px;
            }}

            .side-panel {{
                width: 170px;
                border: 1px solid var(--border-filigree);
                border-radius: 8px;
                background: rgba(18, 9, 24, 0.6);
                padding: 16px 12px;
                text-align: center;
                font-family: 'Cinzel', serif;
                color: var(--gold-bright);
                box-shadow: inset 0 0 15px rgba(0,0,0,0.8);
            }}
            .side-panel h4 {{
                font-size: 11px;
                letter-spacing: 2px;
                margin: 0 0 10px;
                color: var(--gold);
                border-bottom: 1px stroke var(--gold-dark);
                padding-bottom: 4px;
            }}
            .side-panel p {{
                font-size: 10px;
                line-height: 1.6;
                letter-spacing: 1.5px;
                color: var(--text-muted);
                margin: 0;
                text-transform: uppercase;
            }}
            .side-icon {{
                font-size: 20px;
                margin-top: 10px;
                opacity: 0.8;
                color: var(--gold);
            }}

            /* Halo de Luz Teatral detrás de la Carta */
            .spotlight-halo {{
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .spotlight-halo::before {{
                content: "";
                position: absolute;
                width: 280px;
                height: 360px;
                background: radial-gradient(circle, rgba(212,175,55,0.22) 0%, rgba(74,13,23,0.15) 50%, transparent 75%);
                border-radius: 50%;
                pointer-events: none;
                z-index: 0;
            }}

            /* --- Animación 3D de Volteo de Carta (CARTA INTOCABLE) --- */
            .card-scene {{
                perspective: 1200px;
                -webkit-perspective: 1200px;
                width: 224px;
                height: 314px;
                position: relative;
                z-index: 1;
                cursor: pointer;
                user-select: none;
                -webkit-user-select: none;
            }}
            .card-object {{
                width: 100%;
                height: 100%;
                position: relative;
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
            .card-face {{
                position: absolute;
                inset: 0;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid rgba(212,175,55,0.4);
                box-shadow: 0 15px 45px rgba(0,0,0,0.9);
            }}
            .card-front {{
                background: #ffffff;
                -webkit-transform: rotateY(180deg);
                transform: rotateY(180deg);
            }}
            .card-back {{
                background: #ffffff;
                -webkit-transform: rotateY(0deg);
                transform: rotateY(0deg);
            }}
            .card-face img {{
                width: 100%;
                height: 100%;
                object-fit: fill;
                display: block;
                pointer-events: none;
            }}

            /* Texto Inferior Teatral */
            .truth-footer {{
                text-align: center;
                margin-top: 15px;
            }}
            .truth-question {{
                font-family: 'Cinzel Decorative', 'Cinzel', serif;
                font-size: clamp(14px, 3vw, 18px);
                color: var(--gold-bright);
                letter-spacing: 2px;
                margin: 0 0 6px;
                text-transform: uppercase;
            }}
            .truth-destiny {{
                font-family: 'Playfair Display', serif;
                font-style: italic;
                font-size: 13px;
                color: var(--text-muted);
                margin: 0;
            }}

            /* Indicador Secreto Discreto solo para el Mago en Esquina */
            .secret-peek {{
                position: fixed;
                bottom: 10px;
                right: 14px;
                font-family: monospace;
                font-size: 11px;
                color: rgba(212, 175, 55, 0.18);
                letter-spacing: 1px;
                user-select: none;
                pointer-events: none;
                z-index: 99;
            }}

            /* Adaptación Responsiva para Móviles */
            @media (max-width: 768px) {{
                .side-panel {{ display: none; }}
                .curtains-left, .curtains-right {{ width: 25px; }}
                .theater-poster {{ padding: 24px 14px; }}
                .marquee-box {{ padding: 12px 24px; }}
            }}
        </style>
    </head>
    <body>
        <div class="curtains-left"></div>
        <div class="curtains-right"></div>

        <div class="stage-wrapper">
            <div class="theater-poster">
                <!-- Esquinas Filigrana Victoriana -->
                <svg class="corner-filigree corner-tl" viewBox="0 0 24 24" fill="currentColor"><path d="M2 2h6v2H4v4H2V2zm0 14h2v4h4v2H2v-6zM20 2h-6v2h4v4h2V2zm0 14h-2v4h-4v2h6v-6z"/></svg>
                <svg class="corner-filigree corner-tr" viewBox="0 0 24 24" fill="currentColor"><path d="M2 2h6v2H4v4H2V2zm0 14h2v4h4v2H2v-6zM20 2h-6v2h4v4h2V2zm0 14h-2v4h-4v2h6v-6z"/></svg>
                <svg class="corner-filigree corner-bl" viewBox="0 0 24 24" fill="currentColor"><path d="M2 2h6v2H4v4H2V2zm0 14h2v4h4v2H2v-6zM20 2h-6v2h4v4h2V2zm0 14h-2v4h-4v2h6v-6z"/></svg>
                <svg class="corner-filigree corner-br" viewBox="0 0 24 24" fill="currentColor"><path d="M2 2h6v2H4v4H2V2zm0 14h2v4h4v2H2v-6zM20 2h-6v2h4v4h2V2zm0 14h-2v4h-4v2h6v-6z"/></svg>

                <div class="oracle-eye">👁</div>

                <!-- Marquesina con Bombillas Iluminadas -->
                <div class="marquee-box">
                    <div class="marquee-bulbs">
                        <div class="bulb"></div><div class="bulb"></div><div class="bulb"></div>
                        <div class="bulb"></div><div class="bulb"></div><div class="bulb"></div>
                    </div>
                    <h1 class="title-main">EL GRAN ORÁCULO</h1>
                    <div class="title-sub">UNA EXPERIENCIA DE MENTALISMO EN DIRECTO</div>
                </div>

                <!-- Mensaje Principal -->
                <div class="mystery-header">
                    <div class="mystery-title">
                        <span>✦</span> EL MISTERIO ESTÁ A PUNTO DE SER REVELADO <span>✦</span>
                    </div>
                    <div class="mystery-instruction">
                        <span>⤗</span> Toca la carta y descubre lo que el destino ha ocultado <span>⤝</span>
                    </div>
                </div>

                <!-- Disposición Escénica Teatral -->
                <div class="stage-layout">
                    <!-- Cartel Lateral Izquierdo (Desktop) -->
                    <div class="side-panel">
                        <h4>MENTALISTA</h4>
                        <p>Lectura<br>de la Mente<br>—<br>Destino<br>y Suerte</p>
                        <div class="side-icon">🧠</div>
                    </div>

                    <!-- Foco Teatral y Carta (CARTA INTOCABLE) -->
                    <div class="spotlight-halo">
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

                    <!-- Cartel Lateral Derecho (Desktop) -->
                    <div class="side-panel">
                        <h4>EL IMPOSIBLE</h4>
                        <p>No existe<br>para quien<br>—<br>realmente<br>cree</p>
                        <div class="side-icon">🔮</div>
                    </div>
                </div>

                <!-- Mensaje Inferior Teatral -->
                <div class="truth-footer">
                    <div class="truth-question">¿TE ATREVES A DESCUBRIR LA VERDAD?</div>
                    <div class="truth-destiny">El destino ya ha elegido.</div>
                </div>
            </div>
        </div>

        <!-- Indicador Secreto Discreto solo visible para el Mago -->
        <div class="secret-peek" id="secretPeek">{card_valor}{simbolo}</div>

        <script>
            let currentVersion = -1;
            const cardScene = document.getElementById('cardScene');
            const imgFront = document.getElementById('imgFront');
            const secretPeek = document.getElementById('secretPeek');

            function toggleCard() {{
                cardScene.classList.toggle('volteada');
            }}

            cardScene.addEventListener('click', toggleCard);

            // Polling silencioso en segundo plano sin recargar la pantalla
            async function consultarEstadoSilencioso() {{
                try {{
                    const res = await fetch('/api/carta_actual');
                    if (res.ok) {{
                        const data = await res.json();
                        if (data.version && data.version !== currentVersion) {{
                            currentVersion = data.version;
                            // Actualizar la carta de frente y el indicador sutil del mago
                            imgFront.src = `/cartas_svg/${{data.valor}}_${{data.palo_id}}.svg`;
                            secretPeek.textContent = `${{data.valor}}${{data.simbolo}}`;
                            
                            if (cardScene.classList.contains('volteada')) {{
                                cardScene.classList.remove('volteada');
                            }}
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


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)

