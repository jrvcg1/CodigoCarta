import os
import re
import base64
from PIL import Image, ImageDraw, ImageOps

print("[*] Procesando icono de la aplicacion desde dorso.svg...")

svg_path = "cartas_svg/dorso.svg"
extracted_jpg = "c:/Temp/CodigoCarta/dorso_extracted.jpg"

with open(svg_path, "r", encoding="utf-8") as f:
    content = f.read()

m = re.search(r'xlink:href=["\']data:image/jpeg;base64,([^"\']+)["\']', content)
if not m:
    m = re.search(r'data:image/jpeg;base64,([^"\']+)', content)

if m:
    b64_data = m.group(1)
    img_data = base64.b64decode(b64_data)
    with open(extracted_jpg, "wb") as out:
        out.write(img_data)
    print("[OK] Imagen base64 extraida correctamente. Tamano:", len(img_data), "bytes")
else:
    print("[ERROR] No se encontro imagen base64")

# Cargar la imagen del dorso con Pillow
base_img = Image.open(extracted_jpg).convert("RGBA")

# Crear una función para generar un icono redondo/con bordes redondeados tipo app Android
def create_app_icon(size):
    w, h = base_img.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2
    
    cropped = base_img.crop((left, top, right, bottom))
    resized = cropped.resize((size, size), Image.Resampling.LANCZOS)
    
    # Mascara de bordes redondeados
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    corner_radius = int(size * 0.22)
    draw.rounded_rectangle((0, 0, size, size), radius=corner_radius, fill=255)
    
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(resized, (0, 0), mask)
    return output

# Definir tamaños mipmap para Android
icon_sizes = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192
}

base_res_dir = "android_apk_project/app/src/main/res"

for folder_name, size in icon_sizes.items():
    folder_path = os.path.join(base_res_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    icon_img = create_app_icon(size)
    icon_path = os.path.join(folder_path, "ic_launcher.png")
    icon_round_path = os.path.join(folder_path, "ic_launcher_round.png")
    
    icon_img.save(icon_path, "PNG")
    icon_img.save(icon_round_path, "PNG")
    print("[OK] Saved {}/ic_launcher.png ({}x{})".format(folder_name, size, size))

# Guardar también un icono web de alta resolución
web_icon = create_app_icon(512)
web_icon.save("c:/Temp/CodigoCarta/favicon_bicycle.png", "PNG")
print("[OK] Iconos de Android y Web generados exitosamente.")
