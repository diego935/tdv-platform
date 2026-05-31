import arcade
import inspect

try:
    print("=== Sprite.position setter source ===")
    print(inspect.getsource(arcade.Sprite.position.fset))
except Exception as e:
    print("Failed to get position setter source:", e)

try:
    print("=== Sprite.scale setter source ===")
    print(inspect.getsource(arcade.Sprite.scale.fset))
except Exception as e:
    print("Failed to get scale setter source:", e)
    
try:
    print("=== Sprite.angle setter source ===")
    print(inspect.getsource(arcade.Sprite.angle.fset))
except Exception as e:
    print("Failed to get angle setter source:", e)
