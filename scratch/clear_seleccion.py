import xml.etree.ElementTree as ET

tmx_path = "assets/maps/mapa.tmx"
tree = ET.parse(tmx_path)
root = tree.getroot()

# Find the Seleccion layer rectangles
boxes = []
seleccion_group = None
for og in root.findall(".//objectgroup[@name='Seleccion']"):
    seleccion_group = og
    for obj in og.findall("object"):
        x = float(obj.get("x", 0))
        y = float(obj.get("y", 0))
        w = float(obj.get("width", 0))
        h = float(obj.get("height", 0))
        boxes.append((x, y, w, h))

if not boxes:
    print("No selection boxes found in 'Seleccion' layer!")
    exit(0)

print(f"Selection boxes found: {boxes}")

# 1. Clear intersecting objects in other objectgroups
removed_objects_count = 0
for og in root.findall(".//objectgroup"):
    og_name = og.get("name")
    if og_name == "Seleccion":
        continue
    
    # We will build a new list of objects that do not intersect
    objects_to_keep = []
    for obj in og.findall("object"):
        ox = float(obj.get("x", 0))
        oy = float(obj.get("y", 0))
        ow = float(obj.get("width", 0))
        oh = float(obj.get("height", 0))
        
        # Calculate center
        cx = ox + ow / 2.0
        cy = oy + oh / 2.0
        
        inside = False
        for bx, by, bw, bh in boxes:
            if bx <= cx <= bx + bw and by <= cy <= by + bh:
                inside = True
                break
        
        if inside:
            print(f"Removing Object: Group={og_name}, ID={obj.get('id')}, Name={obj.get('name','')}")
            removed_objects_count += 1
        else:
            objects_to_keep.append(obj)
            
    # Reconstruct the objectgroup children
    # First, remove all object children
    for obj in og.findall("object"):
        og.remove(obj)
    # Then add the kept ones back
    for obj in objects_to_keep:
        og.append(obj)

# 2. Clear intersecting tiles in all tile layers
for layer in root.findall(".//layer"):
    layer_name = layer.get("name")
    width = int(layer.get("width", 500))
    height = int(layer.get("height", 527))
    data_el = layer.find("data")
    if data_el is not None and data_el.get("encoding") == "csv":
        csv_text = data_el.text.strip()
        tiles = [int(val) for val in csv_text.split(",") if val.strip()]
        
        cleared_tiles_count = 0
        for bx, by, bw, bh in boxes:
            # Get overlapping tile coordinates
            tx_start = int(bx // 32)
            tx_end = int((bx + bw) // 32)
            ty_start = int(by // 32)
            ty_end = int((by + bh) // 32)
            
            for ty in range(ty_start, ty_end + 1):
                for tx in range(tx_start, tx_end + 1):
                    if 0 <= tx < width and 0 <= ty < height:
                        idx = ty * width + tx
                        if idx < len(tiles) and tiles[idx] != 0:
                            tiles[idx] = 0
                            cleared_tiles_count += 1
        
        if cleared_tiles_count > 0:
            print(f"Cleared {cleared_tiles_count} tiles in layer '{layer_name}'")
            # Update the XML text node for data_el with the new CSV
            # Format nicely with commas and keep spacing structure
            # To make it clean, join by commas and add linebreaks/whitespace similar to original if possible.
            # We can format it in rows of width size to keep it clean.
            formatted_rows = []
            for r in range(height):
                row_tiles = tiles[r * width : (r + 1) * width]
                formatted_rows.append(",".join(map(str, row_tiles)))
            
            # The XML parser needs a newline prefix and suffix
            data_el.text = "\n" + ",\n".join(formatted_rows) + "\n"

# 3. Save the modified map back
# We use a custom writer or simple tree.write to avoid messing up the encoding/XML structure.
# But ET.write is standard. Let's write with xml_declaration and utf-8 encoding.
tree.write(tmx_path, encoding="utf-8", xml_declaration=True)
print("Map successfully updated and saved!")
