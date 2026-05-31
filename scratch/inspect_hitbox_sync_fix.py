import arcade
from arcade.hitbox import RotatableHitBox

sprite = arcade.Sprite()
sprite.center_x = 100
sprite.center_y = 200
sprite.scale = 2.0
sprite.angle = 90

new_hb = RotatableHitBox(points=[(-10, -10), (10, -10), (10, 10), (-10, 10)])
sprite.hit_box = new_hb

# Manually synchronize initial attributes
new_hb.position = sprite.position
new_hb.scale = sprite.scale
new_hb.angle = sprite.angle

print("Adjusted points after manual sync:", sprite.hit_box.get_adjusted_points())

# Now test if a new update synchronizes automatically
sprite.center_x = 500
print("Adjusted points after moving center_x:", sprite.hit_box.get_adjusted_points())
