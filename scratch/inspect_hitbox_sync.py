import arcade
from arcade.hitbox import RotatableHitBox

sprite = arcade.Sprite()
sprite.center_x = 100
sprite.center_y = 200
sprite.scale = 2.0
sprite.angle = 90

new_hb = RotatableHitBox(points=[(-10, -10), (10, -10), (10, 10), (-10, 10)])
sprite.hit_box = new_hb

print("Adjusted points after setting:", sprite.hit_box.get_adjusted_points())
print("Position of hitbox:", sprite.hit_box.position)
print("Scale of hitbox:", sprite.hit_box.scale)
print("Angle of hitbox:", sprite.hit_box.angle)
