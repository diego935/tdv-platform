from PIL import Image
import os
import glob
def redimensionar_manteniendo_ratio(input_path, output_path, max_size=1024):
    """Redimensiona manteniendo aspect ratio, guardando en output_path."""
    img = Image.open(input_path)
    
    w, h = img.size
    if w <= max_size and h <= max_size:
        print(f"  ⏭️  Saltando {input_path} (ya es {w}x{h})")
        return
    
    # Calcular nueva尺寸 manteniendo aspect ratio
    if w > h:
        new_w = max_size
        new_h = int(h * (max_size / w))
    else:
        new_h = max_size
        new_w = int(w * (max_size / h))
    
    # Redimensionar
    img_redim = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    img_redim.save(output_path, optimize=True)
    print(f"  ✅ {input_path} ({w}x{h}) → {output_path} ({new_w}x{new_h})")
def procesar_carpeta(carpeta, max_size=128, prefijo="_reescalado"):
    """Procesa todos los PNG de una carpeta."""
    for root, dirs, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".png"):
                input_path = os.path.join(root, f)
                
                # Generar nombre de salida: imagen_reescalada.png
                nombre_base, ext = os.path.splitext(f)
                output_name = f"{nombre_base}{prefijo}{ext}"
                output_path = os.path.join(root, output_name)
                
                # Solo si no existe ya
                if not os.path.exists(output_path):
                    redimensionar_manteniendo_ratio(input_path, output_path, max_size)
# Ejecutar
carpetas = [
    "assets/Jugador", """
    "assets/items", 
    "assets/tilesets",
    "assets/npcs",
    "assets/fondos"""""
]
for carpeta in carpetas:
    if os.path.exists(carpeta):
        print(f"\n📁 Procesando {carpeta}...")
        procesar_carpeta(carpeta, max_size=512)
