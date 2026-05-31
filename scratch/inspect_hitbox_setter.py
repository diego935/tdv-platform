import arcade
import inspect

sprite = arcade.Sprite()
print("Sprite class type(sprite.hit_box):", type(sprite.hit_box))

# Let's inspect the hit_box property/descriptor on Sprite class
sprite_class_attr = getattr(arcade.Sprite, 'hit_box', None)
if sprite_class_attr:
    print("Sprite.hit_box attribute type:", type(sprite_class_attr))
    print("Is it a property?", isinstance(sprite_class_attr, property))
    if isinstance(sprite_class_attr, property):
        print("Does it have a setter?", sprite_class_attr.fset is not None)
else:
    print("Sprite.hit_box is not a property on the class.")

# Let's inspect create_rotatable or other ways to instantiate a new hit_box
print("Let's try: from arcade.hitbox import RotatableHitBox")
try:
    from arcade.hitbox import RotatableHitBox
    new_hb = RotatableHitBox(points=[(-10, -10), (10, -10), (10, 10), (-10, 10)])
    print("Created new RotatableHitBox!", new_hb)
    print("Adjusted points:", new_hb.get_adjusted_points())
    sprite.hit_box = new_hb
    print("Successfully set sprite.hit_box to new RotatableHitBox! Type:", type(sprite.hit_box))
except Exception as e:
    print("Failed to create/assign RotatableHitBox:", e)
