import xml.etree.ElementTree as ET

tree = ET.parse("assets/maps/mapa.tmx")
root = tree.getroot()

# Find the Seleccion layer rectangles
boxes = []
for og in root.findall(".//objectgroup[@name='Seleccion']"):
    for obj in og.findall("object"):
        x = float(obj.get("x", 0))
        y = float(obj.get("y", 0))
        w = float(obj.get("width", 0))
        h = float(obj.get("height", 0))
        boxes.append((x, y, w, h))

print(f"Selection boxes: {boxes}")

# Check intersecting objects in other objectgroups
for og in root.findall(".//objectgroup"):
    og_name = og.get("name")
    if og_name == "Seleccion":
        continue
    for obj in og.findall("object"):
        ox = float(obj.get("x", 0))
        oy = float(obj.get("y", 0))
        oid = obj.get("id")
        oname = obj.get("name", "")
        # Check if inside any box
        for bx, by, bw, bh in boxes:
            if bx <= ox <= bx + bw and by <= oy <= by + bh:
                print(f"Intersects Object: Group={og_name}, ID={oid}, Name={oname}, x={ox}, y={oy}")

# Check intersecting tiles in tile layers
# Each tile layer has width=500, height=527
# Let's see if any layer has non-zero tiles in these boxes.
# Since tiles are in a 1D CSV list of width*height, we can parse them.
for layer in root.findall(".//layer"):
    layer_name = layer.get("name")
    width = int(layer.get("width", 500))
    height = int(layer.get("height", 527))
    data_el = layer.find("data")
    if data_el is not None and data_el.get("encoding") == "csv":
        csv_text = data_el.text.strip()
        tiles = [int(val) for val in csv_text.split(",") if val.strip()]
        
        # Check coordinates
        intersect_count = 0
        for bx, by, bw, bh in boxes:
            # Convert box pixels to tile indices
            tx_start = int(bx // 32)
            tx_end = int((bx + bw) // 32)
            ty_start = int(by // 32)
            ty_end = int((by + bh) // 32)
            
            for ty in range(ty_start, ty_end + 1):
                for tx in range(tx_start, tx_end + 1):
                    if 0 <= tx < width and 0 <= ty < height:
                        idx = ty * width + tx
                        if idx < len(tiles) and tiles[idx] != 0:
                            intersect_count += 1
        if intersect_count > 0:
            print(f"Intersects Tiles in Layer {layer_name}: {intersect_count} non-zero tiles")
