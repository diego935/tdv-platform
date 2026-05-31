import arcade

print("Arcade version:", arcade.__version__)
if hasattr(arcade, 'hitbox'):
    print("arcade.hitbox members:", dir(arcade.hitbox))
    # Let's inspect some of the classes inside arcade.hitbox
    for name in ['HitBox', 'RotatableHitBox', 'BoundingBox', 'create_hit_box']:
        if hasattr(arcade.hitbox, name):
            print(f"arcade.hitbox.{name}:", getattr(arcade.hitbox, name))
            
# Let's inspect the sprite properties
sprite = arcade.Sprite()
print("sprite.hit_box properties:", type(sprite.hit_box))
if hasattr(sprite.hit_box, 'points'):
    print("sprite.hit_box.points before:", sprite.hit_box.points)
    try:
        # Can we modify points in-place?
        sprite.hit_box.points = [(-10, -10), (10, -10), (10, 10), (-10, 10)]
        print("In-place points assignment succeeded! type:", type(sprite.hit_box))
        print("New points:", sprite.hit_box.points)
        print("Adjusted points:", sprite.hit_box.get_adjusted_points())
    except Exception as e:
        print("In-place points assignment failed:", e)
