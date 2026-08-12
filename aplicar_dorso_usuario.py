import base64
import os
import shutil

src_img = r"C:\Users\ruedaj\.gemini\antigravity\brain\be490b89-877b-439b-965f-8efa18afffb8\.user_uploaded\media_1786463729243.jpg"
dest_dir = r"c:\Temp\CodigoCarta\cartas_svg"
dest_jpg = os.path.join(dest_dir, "dorso.jpg")
dest_svg = os.path.join(dest_dir, "dorso.svg")

# 1. Copiar la imagen JPG exacta subida por el usuario
shutil.copy(src_img, dest_jpg)
print("1. Copiada la imagen exacta a:", dest_jpg)

# 2. Convertir la imagen a Base64 e incrustarla en el SVG para compatibilidad total
with open(dest_jpg, "rb") as f:
    img_bytes = f.read()

base64_str = base64.b64encode(img_bytes).decode("utf-8")

svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="223.22835" height="311.81104" viewBox="0 0 223.22835 311.81104">
  <clipPath id="card-clip">
    <rect width="223.22835" height="311.81104" rx="14" ry="14" />
  </clipPath>
  <g clip-path="url(#card-clip)">
    <image width="223.22835" height="311.81104" xlink:href="data:image/jpeg;base64,{base64_str}" preserveAspectRatio="none" />
  </g>
</svg>"""

with open(dest_svg, "w", encoding="utf-8") as f:
    f.write(svg_content)

print("2. SVG generado incrustando la imagen exacta enviada por el usuario en:", dest_svg)
