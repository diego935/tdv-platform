import arcade
import inspect

# Get source of the hit_box property getter/setter in Sprite class
try:
    print("=== hit_box getter source ===")
    print(inspect.getsource(arcade.Sprite.hit_box.fget))
except Exception as e:
    print("Failed to get getter source:", e)

try:
    print("=== hit_box setter source ===")
    print(inspect.getsource(arcade.Sprite.hit_box.fset))
except Exception as e:
    print("Failed to get setter source:", e)
