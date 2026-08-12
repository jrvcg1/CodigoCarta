"""
Generador del Dorso Azul Estilo Bicycle Rider Back en SVG
=========================================================
Crea un archivo SVG de alta precisión para el reverso azul clásico de la baraja Bicycle Rider Back.
"""

svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="223.22835" height="311.81104" viewBox="0 0 223.22835 311.81104">
  <defs>
    <!-- Patrón de Malla de Fondo Bicycle -->
    <pattern id="rider-mesh" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="8" height="8" fill="#0c326b"/>
      <path d="M 0 0 L 8 8 M 8 0 L 0 8" stroke="#184a8e" stroke-width="0.8" opacity="0.6"/>
      <circle cx="4" cy="4" r="0.8" fill="#ffffff" opacity="0.4"/>
    </pattern>

    <!-- Filigrana de Esquina Roseta Bicycle -->
    <g id="rosette">
      <circle cx="0" cy="0" r="14" fill="none" stroke="#ffffff" stroke-width="1.2"/>
      <circle cx="0" cy="0" r="10" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-dasharray="1.5,1.5"/>
      <circle cx="0" cy="0" r="6" fill="none" stroke="#ffffff" stroke-width="0.8"/>
      <circle cx="0" cy="0" r="3" fill="#ffffff"/>
      <path d="M-14 0 L14 0 M0 -14 L0 14 M-10 -10 L10 10 M-10 10 L10 -10" stroke="#ffffff" stroke-width="0.6" opacity="0.85"/>
    </g>

    <!-- Ángel / Cupido de Rider Back en Bicicleta -->
    <g id="cupid-rider">
      <!-- Cabeza y aureola -->
      <circle cx="0" cy="-10" r="3.5" fill="#ffffff"/>
      <ellipse cx="0" cy="-13" rx="4.5" ry="1.5" fill="none" stroke="#ffffff" stroke-width="0.8"/>
      <!-- Torso -->
      <path d="M-3 -6 Q0 -2 3 -6 L2 4 L-2 4 Z" fill="#ffffff"/>
      <!-- Alas desplegadas -->
      <path d="M-2 -5 C-10 -15, -16 -4, -6 1 C-4 -3, -2 -4, 0 -4 Z" fill="#ffffff"/>
      <path d="M2 -5 C10 -15, 16 -4, 6 1 C4 -3, 2 -4, 0 -4 Z" fill="#ffffff"/>
      <!-- Ruedas de bicicleta con radios -->
      <g transform="translate(-7, 10)">
        <circle cx="0" cy="0" r="6" fill="none" stroke="#ffffff" stroke-width="1"/>
        <path d="M-6 0 L6 0 M0 -6 L0 6 M-4 -4 L4 4 M-4 4 L4 -4" stroke="#ffffff" stroke-width="0.5"/>
      </g>
      <g transform="translate(7, 10)">
        <circle cx="0" cy="0" r="6" fill="none" stroke="#ffffff" stroke-width="1"/>
        <path d="M-6 0 L6 0 M0 -6 L0 6 M-4 -4 L4 4 M-4 4 L4 -4" stroke="#ffffff" stroke-width="0.5"/>
      </g>
      <!-- Cuadro de la bicicleta -->
      <path d="M-7 10 L0 2 L7 10 M0 2 L0 -2 M-3 4 L3 4" stroke="#ffffff" stroke-width="1.2" fill="none"/>
    </g>

    <!-- Medallón Central Doble Bicycle Rider Back -->
    <g id="rider-center">
      <ellipse cx="111.614" cy="155.905" rx="38" ry="54" fill="#0c326b" stroke="#ffffff" stroke-width="2"/>
      <ellipse cx="111.614" cy="155.905" rx="34" ry="50" fill="none" stroke="#ffffff" stroke-dasharray="2,2" stroke-width="1"/>
      <ellipse cx="111.614" cy="155.905" rx="26" ry="38" fill="#072147" stroke="#ffffff" stroke-width="1"/>
      
      <!-- Cupido Superior -->
      <g transform="translate(111.614, 134) scale(1.15)">
        <use href="#cupid-rider"/>
      </g>

      <!-- Cupido Inferior Simétrico (Giro 180º) -->
      <g transform="translate(111.614, 177.81) scale(1.15) rotate(180)">
        <use href="#cupid-rider"/>
      </g>
      
      <!-- Adorno de trébol / corazón en el centro exacto -->
      <circle cx="111.614" cy="155.905" r="5" fill="#ffffff"/>
      <path d="M111.614 149 L114.614 153.5 L108.614 153.5 Z M111.614 162.8 L114.614 158.3 L108.614 158.3 Z" fill="#ffffff"/>
    </g>
  </defs>

  <!-- Fondo Blanco con Bordes Redondeados Clásicos de Baraja Bicycle -->
  <rect width="223.22835" height="311.81104" rx="14" ry="14" fill="#ffffff"/>

  <!-- Campo Azul Principal de la Baraja -->
  <rect x="9" y="9" width="205.22835" height="293.81104" rx="8" ry="8" fill="#0c326b"/>

  <!-- Patrón de Malla Fina de Fondo -->
  <rect x="9" y="9" width="205.22835" height="293.81104" rx="8" ry="8" fill="url(#rider-mesh)"/>

  <!-- Marco Blanco Exterior de Doble Línea -->
  <rect x="13" y="13" width="197.22835" height="285.81104" rx="6" ry="6" fill="none" stroke="#ffffff" stroke-width="2"/>
  <rect x="17" y="17" width="189.22835" height="277.81104" rx="4" ry="4" fill="none" stroke="#ffffff" stroke-width="1" stroke-dasharray="3,2"/>

  <!-- Rosetas de las 4 Esquinas -->
  <g transform="translate(34, 34)"><use href="#rosette"/></g>
  <g transform="translate(189.228, 34)"><use href="#rosette"/></g>
  <g transform="translate(34, 277.811)"><use href="#rosette"/></g>
  <g transform="translate(189.228, 277.811)"><use href="#rosette"/></g>

  <!-- Volutas y Filigranas de Adorno Superior e Inferior -->
  <path d="M40 22 C70 42, 100 16, 111.614 26 C123.228 16, 153.228 42, 183.228 22" fill="none" stroke="#ffffff" stroke-width="1.2"/>
  <path d="M40 289.811 C70 269.811, 100 295.811, 111.614 285.811 C123.228 295.811, 153.228 269.811, 183.228 289.811" fill="none" stroke="#ffffff" stroke-width="1.2"/>

  <!-- Filigranas de los Bordes Laterales Izquierdo y Derecho -->
  <path d="M22 50 C45 80, 15 110, 30 155.905 C15 200, 45 230, 22 260" fill="none" stroke="#ffffff" stroke-width="1.2" opacity="0.85"/>
  <path d="M201.228 50 C178.228 80, 208.228 110, 193.228 155.905 C208.228 200, 178.228 230, 201.228 260" fill="none" stroke="#ffffff" stroke-width="1.2" opacity="0.85"/>

  <!-- Medallón Central Completo Rider Back -->
  <use href="#rider-center"/>
</svg>
"""

with open('cartas_svg/dorso.svg', 'w', encoding='utf-8') as f:
    f.write(svg_content.strip())

print("Dorso azul estilo Bicycle Rider Back SVG generado y guardado en cartas_svg/dorso.svg")
