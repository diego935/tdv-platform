import xml.etree.ElementTree as ET

tree = ET.parse("assets/maps/mapa.tmx")
root = tree.getroot()

for og in root.findall(".//objectgroup"):
    og_name = og.get("name")
    print(f"--- ObjectGroup: {og_name} ---")
    for obj in og.findall("object"):
        x = obj.get("x")
        y = obj.get("y")
        oid = obj.get("id")
        oname = obj.get("name", "")
        print(f"  ID={oid}, Name={oname}, x={x}, y={y}")
