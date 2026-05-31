import arcade

print("Arcade version:", arcade.__version__)

sprite = arcade.Sprite()
print("Type of hit_box:", type(sprite.hit_box))
print("Dir of hit_box:", dir(sprite.hit_box))

try:
    print("Trying to assign list of points to hit_box...")
    sprite.hit_box = [(-10, -10), (10, -10), (10, 10), (-10, 10)]
    print("Assignment succeeded! New hit_box type:", type(sprite.hit_box))
except Exception as e:
    print("Assignment failed:", e)

try:
    print("Trying set_hit_box method...")
    if hasattr(sprite, 'set_hit_box'):
        sprite.set_hit_box([(-20, -20), (20, -20), (20, 20), (-20, 20)])
        print("set_hit_box succeeded! type:", type(sprite.hit_box))
    else:
        print("set_hit_box method does not exist.")
except Exception as e:
    print("set_hit_box failed:", e)
