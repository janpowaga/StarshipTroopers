import pandas as pd
import pygame
import pygame.math as pgmath
import random
import sys
import math

# Define constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 64

SAND_IMAGE = "images/textures/sand.png"
STONE_IMAGE = "images/textures/stone.png"
CAVE_IMAGE = "images/textures/cave.png"

CAMERA_SPEED = 2
ENEMY_SPEED = CAMERA_SPEED / 1.6
ENEMY_DAMAGE = 5
MOUSE_THRESHOLD = 2 * TILE_SIZE

ENEMY_SPAWN_DISTANCE = 100
ENEMY_SPAWN_DISTANCE_MIN = 0
ENEMY_SPAWN_DISTANCE_MAX = 10

RIPPER_SPAWN_RATE = 20
ARACHNID_SPAWN_RATE = RIPPER_SPAWN_RATE * 3
RHINO_SPAWN_RATE = ARACHNID_SPAWN_RATE * 3

SHOOTING_SPEED_SPAWN_RATE = 4200
GRENADE_SPAWN_RATE = 3600
FIRE_SPAWN_RATE = 6900
HP_SPAWN_RATE = 6600

FPS = 60


class Player(pygame.sprite.Sprite):
    def __init__(self, map_width, map_height):
        super().__init__()

        player_run_r_1 = pygame.image.load('images/player/run/player_run_r_1.png').convert_alpha()
        player_run_r_2 = pygame.image.load('images/player/run/player_run_r_2.png').convert_alpha()
        player_run_r_3 = pygame.image.load('images/player/run/player_run_r_3.png').convert_alpha()
        player_run_r_4 = pygame.image.load('images/player/run/player_run_r_4.png').convert_alpha()
        player_run_r_5 = pygame.image.load('images/player/run/player_run_r_5.png').convert_alpha()
        player_run_r_6 = pygame.image.load('images/player/run/player_run_r_6.png').convert_alpha()
        self.player_run_r = [player_run_r_1, player_run_r_2, player_run_r_3, player_run_r_4, player_run_r_5, player_run_r_6]

        player_run_l_1 = pygame.image.load('images/player/run/player_run_l_1.png').convert_alpha()
        player_run_l_2 = pygame.image.load('images/player/run/player_run_l_2.png').convert_alpha()
        player_run_l_3 = pygame.image.load('images/player/run/player_run_l_3.png').convert_alpha()
        player_run_l_4 = pygame.image.load('images/player/run/player_run_l_4.png').convert_alpha()
        player_run_l_5 = pygame.image.load('images/player/run/player_run_l_5.png').convert_alpha()
        player_run_l_6 = pygame.image.load('images/player/run/player_run_l_6.png').convert_alpha()
        self.player_run_l = [player_run_l_1, player_run_l_2, player_run_l_3, player_run_l_4, player_run_l_5, player_run_l_6]

        self.player_index = 0

        self.image = player_run_r_1
        self.rect = self.image.get_rect()
        self.rect.center = (map_width // 2, map_height // 2)

        self.health = 100
        self.shoot_rate = 30
        self.grenades = 0
        self.ring_of_fire = False
        self.ring_of_fire_rate = 360
        self.original_pos = pgmath.Vector2(self.rect.topleft)

        self.hurt_sound = pygame.mixer.Sound('sounds/hurt.wav')
        self.hurt_sound.set_volume(0.4)
        self.dead_sound = pygame.mixer.Sound('sounds/dead.wav')
        self.dead_sound.set_volume(0.65)
        self.dead_sound_flag = True
        self.shooting_sound = pygame.mixer.Sound('sounds/shot.mp3')
        self.shooting_sound.set_volume(0.4)

    def calculate_move_vector(self, mouse_pos):
        center = pgmath.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        mouse_vector = pgmath.Vector2(mouse_pos)
        move_vector = mouse_vector - center
        move_distance = move_vector.length()

        if move_vector != [0, 0]:
            if move_distance < MOUSE_THRESHOLD:
                move_scale = move_distance / MOUSE_THRESHOLD
                move_vector.normalize_ip()
                move_vector *= CAMERA_SPEED * move_scale
            else:
                move_vector.normalize_ip()
                move_vector *= CAMERA_SPEED

            move_vector_x = pgmath.Vector2(move_vector.x, 0)
            move_vector_y = pgmath.Vector2(0, move_vector.y)

        else:
            move_vector_x = pgmath.Vector2(0, 0)
            move_vector_y = pgmath.Vector2(0, 0)

        return move_vector_x, move_vector_y

    def check_collision(self, move_vector_x, move_vector_y, tiles):
        future_position_x = pgmath.Vector2(self.rect.topleft) + move_vector_x
        future_position_y = pgmath.Vector2(self.rect.topleft) + move_vector_y
        future_rect_x = self.image.get_rect(topleft=future_position_x)
        future_rect_y = self.image.get_rect(topleft=future_position_y)

        collision_normals = []
        for tile in tiles:
            if tile.image in [stone_image, cave_image]:
                if future_rect_x.colliderect(tile.rect):
                    normal_x = pgmath.Vector2(-move_vector_x.x, 0)
                    if normal_x.length_squared() > 0:
                        collision_normals.append(normal_x.normalize())
                if future_rect_y.colliderect(tile.rect):
                    normal_y = pgmath.Vector2(0, -move_vector_y.y)
                    if normal_y.length_squared() > 0:
                        collision_normals.append(normal_y.normalize())

        return collision_normals

    def find_closest_enemy_in_camera(self, enemies, camera):
        visible_enemies = []
        for enemy in enemies:
            screen_pos = enemy.original_pos - camera.offset
            if 0 <= screen_pos.x <= SCREEN_WIDTH and 0 <= screen_pos.y <= SCREEN_HEIGHT:
                visible_enemies.append(enemy)

        if not visible_enemies:
            return None

        closest_enemy = min(visible_enemies, key=lambda enemy: (self.original_pos - enemy.original_pos).length())
        return closest_enemy

    def shoot_bullet(self, bullets, camera, enemies):
        closest_enemy = self.find_closest_enemy_in_camera(enemies, camera)
        if closest_enemy is not None:
            shoot_direction = (closest_enemy.get_colliderect_center() - pgmath.Vector2(self.rect.center)).normalize()
            bullet = Bullet(self.rect.centerx + camera.offset.x, self.rect.centery + camera.offset.y, shoot_direction)
            bullets.add(bullet)

            self.shooting_sound.play()

    def draw_health_bar(self, surface, camera):
        health_bar_width = int(20 * (self.health / 100))
        health_bar_height = 5
        health_bar_color = (255, 0, 0)

        health_bar_position = self.original_pos - camera.offset + pgmath.Vector2(0, self.rect.height + 2)
        health_bar_rect = pygame.Rect(health_bar_position.x, health_bar_position.y, health_bar_width, health_bar_height)

        pygame.draw.rect(surface, health_bar_color, health_bar_rect)

    def animation_state(self):
        self.player_index += 0.1

        if self.player_index >= len(self.player_run_r):
            self.player_index = 0

        move_vector_x = self.calculate_move_vector(pygame.mouse.get_pos())[0]
        if move_vector_x[0] < 0:
            self.image = self.player_run_l[int(self.player_index)]
        else:
            self.image = self.player_run_r[int(self.player_index)]

    def update(self):
        self.animation_state()

        # Update player position based on mouse position
        mouse_pos = pygame.mouse.get_pos()
        move_vector_x, move_vector_y = player.calculate_move_vector(mouse_pos)

        collision_normals = player.check_collision(move_vector_x, move_vector_y, tiles)

        for normal in collision_normals:
            move_vector_x -= normal * move_vector_x.dot(normal)
            move_vector_y -= normal * move_vector_y.dot(normal)

        move_vector = move_vector_x + move_vector_y

        # Update the original position of the player
        player.original_pos += move_vector

        # Update the camera
        camera.update(move_vector)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, target, enemy_type, speed, health, damage):
        super().__init__()

        ripper_r_1 = pygame.image.load('images/enemy/ripper/ripper_r_1.png').convert_alpha()
        ripper_r_2 = pygame.image.load('images/enemy/ripper/ripper_r_2.png').convert_alpha()
        self.ripper_r = [ripper_r_1, ripper_r_2]
        ripper_l_1 = pygame.image.load('images/enemy/ripper/ripper_l_1.png').convert_alpha()
        ripper_l_2 = pygame.image.load('images/enemy/ripper/ripper_l_2.png').convert_alpha()
        self.ripper_l = [ripper_l_1, ripper_l_2]

        arachnid_r_1 = pygame.image.load('images/enemy/arachnid/arachnid_r_1.png').convert_alpha()
        arachnid_r_2 = pygame.image.load('images/enemy/arachnid/arachnid_r_2.png').convert_alpha()
        self.arachnid_r = [arachnid_r_1, arachnid_r_2]
        arachnid_l_1 = pygame.image.load('images/enemy/arachnid/arachnid_l_1.png').convert_alpha()
        arachnid_l_2 = pygame.image.load('images/enemy/arachnid/arachnid_l_2.png').convert_alpha()
        self.arachnid_l = [arachnid_l_1, arachnid_l_2]

        rhino_r_1 = pygame.image.load('images/enemy/rhino/rhino_r_1.png').convert_alpha()
        rhino_r_2 = pygame.image.load('images/enemy/rhino/rhino_r_2.png').convert_alpha()
        rhino_r_3 = pygame.image.load('images/enemy/rhino/rhino_r_3.png').convert_alpha()
        self.rhino_r = [rhino_r_1, rhino_r_2, rhino_r_3]
        rhino_l_1 = pygame.image.load('images/enemy/rhino/rhino_l_1.png').convert_alpha()
        rhino_l_2 = pygame.image.load('images/enemy/rhino/rhino_l_2.png').convert_alpha()
        rhino_l_3 = pygame.image.load('images/enemy/rhino/rhino_l_3.png').convert_alpha()
        self.rhino_l = [rhino_l_1, rhino_l_2, rhino_l_3]

        self.enemy_index = 0
        self.enemy_type = enemy_type

        self.image = arachnid_r_1
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.colliderect = self.rect
        self.original_pos = pgmath.Vector2(x, y)
        self.target = target
        self.frame_count = 0
        self.health = health
        self.damage = damage
        self.speed = speed
        self.frames_since_last_damage = 0

        self.get_hit_sound = pygame.mixer.Sound('sounds/bug_shot.wav')
        self.get_hit_sound.set_volume(0.4)

    def take_damage(self, damage):
        self.get_hit_sound.play()
        self.health -= damage

    def animation_state(self):
        move_vector = pgmath.Vector2(player.original_pos) - pgmath.Vector2(self.original_pos)

        if self.enemy_type == 'ripper':
            self.enemy_index += 0.1

            if self.enemy_index >= len(self.ripper_l):
                self.enemy_index = 0
            if move_vector.x < 0:
                self.image = self.ripper_l[int(self.enemy_index)]
            else:
                self.image = self.ripper_r[int(self.enemy_index)]

        if self.enemy_type == 'arachnid':
            self.enemy_index += 0.1

            if self.enemy_index >= len(self.arachnid_l):
                self.enemy_index = 0
            if move_vector.x < 0:
                self.image = self.arachnid_l[int(self.enemy_index)]
            else:
                self.image = self.arachnid_r[int(self.enemy_index)]

        if self.enemy_type == 'rhino':
            self.enemy_index += 0.05

            if self.enemy_index >= len(self.rhino_l):
                self.enemy_index = 0
            if move_vector.x < 0:
                self.image = self.rhino_l[int(self.enemy_index)]
            else:
                self.image = self.rhino_r[int(self.enemy_index)]

    def get_colliderect_center(self):
        return pgmath.Vector2(self.colliderect.center)

    def update(self, player, camera, enemies, tiles):
        self.animation_state()

        # Ensure enemies won't collide with each other
        move_vector = pgmath.Vector2(player.original_pos) - pgmath.Vector2(self.original_pos)
        move_vector.normalize_ip()
        move_vector *= self.speed

        for enemy in enemies:
            if enemy != self:
                distance_to_enemy = pgmath.Vector2(enemy.original_pos) - pgmath.Vector2(self.original_pos)
                if 0 < distance_to_enemy.length() < (self.colliderect.width + 2):
                    move_vector -= distance_to_enemy.normalize() * (ENEMY_SPEED / 2)

        move_vector_x = pgmath.Vector2(move_vector.x, 0)
        move_vector_y = pgmath.Vector2(0, move_vector.y)
        move_vector = move_vector_x + move_vector_y

        self.original_pos += move_vector
        self.rect.topleft = self.original_pos - camera.offset

        # Create collision rectangles
        if self.enemy_type == 'ripper':
            self.colliderect = pygame.rect.Rect((0, 0), (14, 14))
            self.colliderect.midtop = self.rect.midtop

        if self.enemy_type == 'arachnid':
            self.colliderect = pygame.rect.Rect((0, 0), (50, 50))
            self.colliderect.center = self.rect.center

        if self.enemy_type == 'rhino':
            self.colliderect = pygame.rect.Rect((0, 0), (165, 50))
            self.colliderect.center = self.rect.center

        # Dealing damage to player
        if self.colliderect.colliderect(player.rect):
            if player.health > 0 and self.frames_since_last_damage >= 60:
                player.health -= self.damage
                player.hurt_sound.play()
                self.frames_since_last_damage = 0
            else:
                self.frames_since_last_damage += 1


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((3, 3))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.original_pos = pgmath.Vector2(x, y)
        self.direction = direction
        self.speed = 10

    def update(self, camera):
        self.original_pos += self.direction * self.speed
        self.rect.center = self.original_pos - camera.offset


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, damage_radius, damage_amount):
        super().__init__()

        grenade_1 = pygame.image.load('images/power_ups/grenade/grenade_exp_1.png').convert_alpha()
        grenade_2 = pygame.image.load('images/power_ups/grenade/grenade_exp_2.png').convert_alpha()
        grenade_3 = pygame.image.load('images/power_ups/grenade/grenade_exp_3.png').convert_alpha()
        grenade_4 = pygame.image.load('images/power_ups/grenade/grenade_exp_4.png').convert_alpha()
        grenade_5 = pygame.image.load('images/power_ups/grenade/grenade_exp_5.png').convert_alpha()
        self.grenade_exp = [grenade_1, grenade_2, grenade_3, grenade_4, grenade_5]

        self.grenade_index = 0

        self.image = grenade_1
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.original_pos = pgmath.Vector2(x, y)
        self.damage_radius = damage_radius
        self.damage_amount = damage_amount

    def throw_grenade(sprite_group, damage_amount):
        grenade_x = random.randint(int(camera.offset.x), int(camera.offset.x + SCREEN_WIDTH - TILE_SIZE))
        grenade_y = random.randint(int(camera.offset.y), int(camera.offset.y + SCREEN_HEIGHT - TILE_SIZE))
        grenade = Grenade(grenade_x, grenade_y, TILE_SIZE * 2, damage_amount)
        sprite_group.add(grenade)

        explosion_sound = pygame.mixer.Sound('sounds/explosion.wav')
        explosion_sound.set_volume(0.5)
        explosion_sound.play()

    def explode(sprite_group, enemies):
        for grenade in sprite_group:
            sprite_group.remove(grenade)
            for enemy in enemies:
                grenade_area = pygame.Rect(grenade.rect.x, grenade.rect.y, grenade.damage_radius, grenade.damage_radius)
                if grenade_area.colliderect(enemy.rect):
                    enemy.take_damage(grenade.damage_amount)
                    if enemy.health <= 0:
                        enemies.remove(enemy)

    def animation_state(self):
        self.grenade_index += 0.1
        if self.grenade_index >= len(self.grenade_exp):
            self.grenade_index = 0
        self.image = self.grenade_exp[int(self.grenade_index)]

    def update(self):
        self.animation_state()


class RingOfFire(pygame.sprite.Sprite):
    def __init__(self, damage_amount):
        super().__init__()

        ring_of_fire_1 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_1.png').convert_alpha()
        ring_of_fire_2 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_2.png').convert_alpha()
        ring_of_fire_3 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_3.png').convert_alpha()
        ring_of_fire_4 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_4.png').convert_alpha()
        ring_of_fire_5 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_5.png').convert_alpha()
        ring_of_fire_6 = pygame.image.load('images/power_ups/ring_of_fire/ring_of_fire_6.png').convert_alpha()
        self.ring_of_fire = [ring_of_fire_1, ring_of_fire_2, ring_of_fire_3, ring_of_fire_4, ring_of_fire_5, ring_of_fire_6]

        self.fire_index = 0

        self.image = ring_of_fire_1
        self.rect = self.image.get_rect()
        self.rect.center = (400, 300)
        self.original_pos = pgmath.Vector2(300, 400)
        self.damage_amount = damage_amount

    def set_off(sprite_group, damage_amount):
        explosion_sound = pygame.mixer.Sound('sounds/explosion.wav')
        explosion_sound.set_volume(0.5)
        explosion_sound.play()

        fire = RingOfFire(damage_amount)
        sprite_group.add(fire)

    def explode(sprite_group, enemies):
        for fire in sprite_group:
            sprite_group.remove(fire)
            for enemy in enemies:
                fire_area = pygame.Rect(fire.rect.x, fire.rect.y, 124, 124)
                if fire_area.colliderect(enemy.rect):
                    enemy.take_damage(fire.damage_amount)
                    if enemy.health <= 0:
                        enemies.remove(enemy)

    def animation_state(self):
        self.fire_index += 0.1
        if self.fire_index >= len(self.ring_of_fire):
            self.fire_index = 0
        self.image = self.ring_of_fire[int(self.fire_index)]

    def update(self):
        self.animation_state()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_up_type, active):
        super().__init__()
        grenade_1 = pygame.image.load('images/power_ups/grenade/grenade_1.png').convert_alpha()
        grenade_2 = pygame.image.load('images/power_ups/grenade/grenade_2.png').convert_alpha()
        grenade_3 = pygame.image.load('images/power_ups/grenade/grenade_3.png').convert_alpha()
        grenade_4 = pygame.image.load('images/power_ups/grenade/grenade_4.png').convert_alpha()
        grenade_5 = pygame.image.load('images/power_ups/grenade/grenade_5.png').convert_alpha()
        self.grenade = [grenade_1, grenade_2, grenade_3, grenade_4, grenade_5]

        fire_1 = pygame.image.load('images/power_ups/ring_of_fire/fire_1.png').convert_alpha()
        fire_2 = pygame.image.load('images/power_ups/ring_of_fire/fire_2.png').convert_alpha()
        fire_3 = pygame.image.load('images/power_ups/ring_of_fire/fire_3.png').convert_alpha()
        fire_4 = pygame.image.load('images/power_ups/ring_of_fire/fire_4.png').convert_alpha()
        fire_5 = pygame.image.load('images/power_ups/ring_of_fire/fire_5.png').convert_alpha()
        self.fire = [fire_1, fire_2, fire_3, fire_4, fire_5]

        shooting_speed_1 = pygame.image.load('images/power_ups/shooting_speed/shooting_speed_1.png').convert_alpha()
        shooting_speed_2 = pygame.image.load('images/power_ups/shooting_speed/shooting_speed_2.png').convert_alpha()
        shooting_speed_3 = pygame.image.load('images/power_ups/shooting_speed/shooting_speed_3.png').convert_alpha()
        shooting_speed_4 = pygame.image.load('images/power_ups/shooting_speed/shooting_speed_4.png').convert_alpha()
        shooting_speed_5 = pygame.image.load('images/power_ups/shooting_speed/shooting_speed_5.png').convert_alpha()
        self.shooting_speed = [shooting_speed_1, shooting_speed_2, shooting_speed_3, shooting_speed_4, shooting_speed_5]

        hp_1 = pygame.image.load('images/power_ups/hp/hp_1.png').convert_alpha()
        hp_2 = pygame.image.load('images/power_ups/hp/hp_2.png').convert_alpha()
        hp_3 = pygame.image.load('images/power_ups/hp/hp_3.png').convert_alpha()
        hp_4 = pygame.image.load('images/power_ups/hp/hp_4.png').convert_alpha()
        hp_5 = pygame.image.load('images/power_ups/hp/hp_5.png').convert_alpha()
        self.hp = [hp_1, hp_2, hp_3, hp_4, hp_5]

        self.power_up_index = 0
        self.power_up_type = power_up_type
        self.active = active

        self.image = grenade_1
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.original_pos = pgmath.Vector2(x, y)

        self.power_up_sound = pygame.mixer.Sound('sounds/power_up.wav')
        self.power_up_sound.set_volume(0.1)

    def animation_state(self):
        self.power_up_index += 0.1

        if self.power_up_type == 'grenade':
            if self.power_up_index >= len(self.grenade):
                self.power_up_index = 0
            self.image = self.grenade[int(self.power_up_index)]

        if self.power_up_type == 'fire':
            if self.power_up_index >= len(self.fire):
                self.power_up_index = 0
            self.image = self.fire[int(self.power_up_index)]

        if self.power_up_type == 'shooting_speed':
            if self.power_up_index >= len(self.shooting_speed):
                self.power_up_index = 0
            self.image = self.shooting_speed[int(self.power_up_index)]

        if self.power_up_type == 'hp':
            if self.power_up_index >= len(self.hp):
                self.power_up_index = 0
            self.image = self.hp[int(self.power_up_index)]

    def player_collision(self):
        global RIPPER_SPAWN_RATE

        for power_up in power_ups:
            if self.rect.colliderect(player.rect):
                # Play sound
                self.power_up_sound.play()

                if self.active and self.power_up_type == 'grenade':
                    player.grenades += 1
                    self.active = False

                if self.active and self.power_up_type == 'fire':
                    player.ring_of_fire = True
                    player.ring_of_fire_rate -= 60
                    self.active = False

                if self.active and self.power_up_type == 'shooting_speed':
                    player.shoot_rate /= 2
                    RIPPER_SPAWN_RATE *= 1.5
                    self.active = False

                if self.active and self.power_up_type == 'hp':
                    player.health += 50
                    if player.health >= 100:
                        player.health = 100
                    self.active = False

    def update(self):
        self.animation_state()
        self.player_collision()

        if self.active == 0:
            power_ups.remove(power_up)


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, x, y):
        super().__init__()
        self.image = tile_type
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.original_pos = pgmath.Vector2(x, y)


class Camera:
    def __init__(self):
        self.offset = pgmath.Vector2(0, 0)

    def apply(self, target):
        target.rect.topleft = target.original_pos - self.offset
        return target  # Return the modified target object

    def update(self, move_vector):
        self.offset += move_vector



def create_level(level_map, tile_images):
    tiles = pygame.sprite.Group()
    for row, row_str in enumerate(level_map):
        for col, tile_char in enumerate(row_str):
            tile_image = tile_images.get(tile_char)
            if tile_image:
                tile = Tile(tile_image, col * TILE_SIZE, row * TILE_SIZE)
                tiles.add(tile)
    return tiles


def get_visible_tiles(tiles, camera):
    visible_tiles = []
    for tile in tiles:
        screen_pos = tile.original_pos - camera.offset
        if -TILE_SIZE <= screen_pos.x <= SCREEN_WIDTH + TILE_SIZE and -TILE_SIZE <= screen_pos.y <= SCREEN_HEIGHT + TILE_SIZE:
            visible_tiles.append(tile)
    return visible_tiles


def spawn_enemy(camera, enemies, enemy_type):
    while True:
        # Choose a random side of the viewport (0 = left, 1 = right, 2 = top, 3 = bottom)
        side = random.randint(0, 3)
        offset = 10

        if side == 0:  # Left edge
            x = camera.offset.x - TILE_SIZE - offset
            y = random.randint(int(camera.offset.y), int(camera.offset.y + SCREEN_HEIGHT - TILE_SIZE))
        elif side == 1:  # Right edge
            x = camera.offset.x + SCREEN_WIDTH + offset
            y = random.randint(int(camera.offset.y), int(camera.offset.y + SCREEN_HEIGHT - TILE_SIZE))
        elif side == 2:  # Top edge
            x = random.randint(int(camera.offset.x), int(camera.offset.x + SCREEN_WIDTH - TILE_SIZE))
            y = camera.offset.y - TILE_SIZE - offset
        else:  # Bottom edge
            x = random.randint(int(camera.offset.x), int(camera.offset.x + SCREEN_WIDTH - TILE_SIZE))
            y = camera.offset.y + SCREEN_HEIGHT + offset

        if enemy_type == 'ripper':
            enemy = Enemy(x, y, player, 'ripper', ENEMY_SPEED, 10, ENEMY_DAMAGE)

        if enemy_type == 'arachnid':
            enemy = Enemy(x, y, player, 'arachnid', ENEMY_SPEED / 2, 20, ENEMY_DAMAGE * 2)

        if enemy_type == 'rhino':
            enemy = Enemy(x, y, player, 'rhino', (ENEMY_SPEED / 2) / 2, 40, (ENEMY_DAMAGE * 2) * 2)

        enemies.add(enemy)
        break


def spawn_power_up(camera, power_ups, power_up_type):
    while True:
        x = random.randint(int(camera.offset.x + TILE_SIZE), int(camera.offset.x + SCREEN_WIDTH - TILE_SIZE))
        y = random.randint(int(camera.offset.y + TILE_SIZE), int(camera.offset.y + SCREEN_HEIGHT - TILE_SIZE))

        if power_up_type == 'grenade':
            power_up = PowerUp(x, y, 'grenade', True)

        if power_up_type == 'fire':
            power_up = PowerUp(x, y, 'fire', True)

        if power_up_type == 'shooting_speed':
            power_up = PowerUp(x, y, 'shooting_speed', True)

        if power_up_type == 'hp':
            power_up = PowerUp(x, y, 'hp', True)

        power_ups.add(power_up)
        break


def render_timer():
    global timeout, evac_time

    minutes = 9 - minutes_count
    seconds = 59 - seconds_count

    if minutes == 0 and seconds == 0:
        minutes = 0
        seconds = 0
        timeout = True

    if seconds == -1:
        seconds = 59

    time_str = '{:02d}:{:02d}'.format(minutes, seconds)
    if minutes < 2:
        evac_time = True
        timer_text = font.render(time_str, False, (255, 0, 0))
        timer_text_rect = timer_text.get_rect(midtop=(SCREEN_WIDTH // 2, 40))

        if seconds % 2 == 0 and seconds > 50:
            screen.blit(return_to_evac, return_to_evac_rect)
    else:
        timer_text = font.render(time_str, False, (0, 0, 0))
        timer_text_rect = timer_text.get_rect(midtop=(SCREEN_WIDTH // 2, 40))
    screen.blit(timer_text, timer_text_rect)


def render_power_up_ui():
    # Create UI for power-ups.
    shooting_speed_text = font.render('Shooting Speed: {}RPM'.format(int(60 / player.shoot_rate * 60)), False, (0, 0, 0))
    shooting_speed_text_rect = shooting_speed_text.get_rect(topleft=(30, 530))
    screen.blit(shooting_speed_text, shooting_speed_text_rect)

    if player.grenades > 0:
        grenades_text = font.render('Grenades: {} per 5s'.format(player.grenades), False, (0, 0, 0))
        grenades_text_rect = grenades_text.get_rect(topleft=(30, 550))
        screen.blit(grenades_text, grenades_text_rect)

    if player.ring_of_fire:
        fire_text = font.render('Ring of Fire: {}s'.format(int(player.ring_of_fire_rate / 60)), False, (0, 0, 0))
        fire_text_rect = fire_text.get_rect(topleft=(30, 570))
        screen.blit(fire_text, fire_text_rect)


def draw_overlay(surface, camera, map_width_tiles, map_height_tiles, tile_size):
    center_x = (86 * tile_size)
    center_y = (80 * tile_size)
    overlay_width = 30 * tile_size
    overlay_height = 29 * tile_size
    overlay_rect = pygame.Rect(center_x, center_y, overlay_width, overlay_height)

    # Create a temporary object with the required attributes for the Camera's apply method
    object = lambda: None
    object.rect = overlay_rect
    object.original_pos = pgmath.Vector2(overlay_rect.topleft)

    camera_rect = camera.apply(object).rect
    if camera_rect.colliderect(surface.get_rect()):
        # Draw semi-transparent red overlay
        overlay_surface = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
        overlay_surface.fill((0, 255, 0, 80))
        surface.blit(overlay_surface, camera_rect.topleft)
    else:
        # # Draw red arrow pointing to the overlay's center
        screen_center_x, screen_center_y = surface.get_rect().center
        direction = pgmath.Vector2(center_x, center_y) - pgmath.Vector2(camera.offset.x + screen_center_x, camera.offset.y + screen_center_y)
        angle = math.degrees(math.atan2(direction.y, direction.x))
        draw_arrow(screen, angle, 10, 10)

    return overlay_rect


def draw_arrow(surface, angle, x_offset, y_offset):
    arrow_image = pygame.image.load('images/arrow_red.png').convert_alpha()
    arrow_rotated = pygame.transform.rotate(arrow_image, -angle)
    arrow_rect = arrow_rotated.get_rect()

    # Place the arrow in the top right corner of the screen
    arrow_rect.topright = (SCREEN_WIDTH - x_offset, y_offset)

    surface.blit(arrow_rotated, arrow_rect)


def reset_game():
    global player, players, camera, enemies, bullets, grenades, fires, power_ups, frame_count, seconds_count, minutes_count, timeout, evac_time

    # Reset player
    player = Player(map_width, map_height)
    players = pygame.sprite.Group()
    players.add(player)

    # Reset camera
    camera = Camera()
    camera.offset = pgmath.Vector2(player.rect.centerx - SCREEN_WIDTH // 2, player.rect.centery - SCREEN_HEIGHT // 2)

    # Reset enemy, bullet, and grenade groups
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    grenades = pygame.sprite.Group()
    fires = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()

    # Reset counters and timers
    frame_count = 0
    seconds_count = -1
    minutes_count = 0
    timeout = False
    evac_time = False


# Initialize pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Starship Trooper")

# Set up the font
font = pygame.font.Font('font/Goldman.ttf', 21)
ui_font = pygame.font.Font('font/Goldman.ttf', 15)
you_died_font = pygame.font.Font('font/Goldman.ttf', 100)


# Load start menu images
start_menu_bg = pygame.image.load('images/main_screen.png').convert_alpha()
start_menu_bg_rect = start_menu_bg.get_rect(topleft=(0, 0))

start_button = pygame.image.load('images/start.png').convert_alpha()
start_button_rect = start_button.get_rect(midtop=(SCREEN_WIDTH // 2, 420))

credits_button = pygame.image.load('images/credits.png').convert_alpha()
credits_button_rect = credits_button.get_rect(midtop=(SCREEN_WIDTH // 2, 500))

exit_button = pygame.image.load('images/exit.png').convert_alpha()
exit_button_rect = exit_button.get_rect(midtop=(SCREEN_WIDTH // 2, 550))

# Load credits images
credits_text_bw = font.render('ART: Bartosz Wyszkowski', False, (255, 255, 255))
credits_text_bw_rect = credits_text_bw.get_rect(midbottom=(SCREEN_WIDTH // 2, 300))

credits_text_jp = font.render('CODE: Jan Powaga', False, (255, 255, 255))
credits_text_jp_rect = credits_text_bw.get_rect(midbottom=(SCREEN_WIDTH // 2, 350))

hackathon_text = font.render('Created as an entry for Pygames Hackathon 2023', False, (255, 255, 255))
hackathon_text_rect = hackathon_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 500))

return_text = font.render('PRESS ESC TO RETURN TO MAIN MENU', False, (255, 255, 255))
return_text_rect = return_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 550))

# Load intro images
intro_bg = pygame.image.load('images/intro.png').convert_alpha()
intro_bg_rect = intro_bg.get_rect(topleft=(0, 0))

story = pygame.image.load('images/story.png').convert_alpha()
story_rect = story.get_rect(midtop=(SCREEN_WIDTH // 2, 600))

intro_text = font.render('PRESS ANY KEY TO START', False, (255, 255, 255))
intro_text_rect = intro_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 550))

# Load game over images
game_over_text = you_died_font.render('YOU DIED', False, '#4F0001')
game_over_text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

play_again_text = font.render('PRESS SPACE TO TRY AGAIN', False, (255, 255, 255))
play_again_text_rect = play_again_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 500))

runaway_text = font.render('PRESS ESC TO RUN AWAY LIKE A COWARD', False, (255, 255, 255))
runaway_text_rect = runaway_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 550))

# Load outro images
outro_bg = pygame.image.load('images/outro.png').convert_alpha()
outro_bg_rect = outro_bg.get_rect(topleft=(0, 0))

evac = pygame.image.load('images/evac.png').convert_alpha()
evac_rect = evac.get_rect(midtop=(SCREEN_WIDTH // 2, 600))

outro_text = font.render('YOU CAN REST NOW, SOLDIER. PRESS ANY KEY.', False, (255, 255, 255))
outro_text_rect = outro_text.get_rect(midbottom=(SCREEN_WIDTH // 2, 550))

# Other assets

return_to_evac = font.render('RETURN TO EVAC ZONE', False, (255, 0, 0))
return_to_evac_rect = return_to_evac.get_rect(midtop=(SCREEN_WIDTH // 2, 75))

# Load audio assets
bg_music = pygame.mixer.Sound('sounds/desert_drums.mp3')
bg_music.set_volume(0)
bg_music.play(loops=-1)

main_menu_music = pygame.mixer.Sound('sounds/main_theme.mp3')
main_menu_music.set_volume(0.5)
main_menu_music.play(loops=-1)

menu_click = pygame.mixer.Sound('sounds/menu_click.wav')
menu_click.set_volume(0.5)

# Set up the clock
clock = pygame.time.Clock()

# Load tile images
sand_image = pygame.image.load(SAND_IMAGE).convert_alpha()
stone_image = pygame.image.load(STONE_IMAGE).convert_alpha()
cave_image = pygame.image.load(CAVE_IMAGE).convert_alpha()

# Create a dictionary to map characters to images
tile_images = {
    'G': sand_image,
    'B': stone_image,
    'W': cave_image,
}

# Define your level_map
level_map = pd.read_csv('level_map/level_map.csv').values.tolist()

# Calculate map dimensions
map_width = len(level_map[0]) * TILE_SIZE
map_height = len(level_map) * TILE_SIZE

# Create the level and add it to a sprite group
tiles = create_level(level_map, tile_images)

# Create player instance and add it to a sprite group
player = Player(map_width, map_height)
players = pygame.sprite.Group()
players.add(player)

# Create a camera instance
camera = Camera()

# Center the camera on the player
camera.offset = pgmath.Vector2(player.rect.centerx - SCREEN_WIDTH // 2, player.rect.centery - SCREEN_HEIGHT // 2)

# Create enemies group
enemies = pygame.sprite.Group()

# Create bullets group
bullets = pygame.sprite.Group()

# Create grenades group
grenades = pygame.sprite.Group()

# Create fires group
fires = pygame.sprite.Group()

# Create power_ups group
power_ups = pygame.sprite.Group()

# Main game loop
running = True
game_state = 'start_menu'

frame_count = 0
seconds_count = -1
minutes_count = 0
timeout = False
evac_time = False
grenade_timer = 0
fire_timer = 0

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        if game_state == 'start_menu' and event.type == pygame.MOUSEBUTTONDOWN:
            # Play sound
            menu_click.play()

            if start_button_rect.collidepoint(event.pos):
                game_state = 'intro'

            if credits_button_rect.collidepoint(event.pos):
                game_state = 'credits'

            if exit_button_rect.collidepoint(event.pos):
                running = False
                sys.exit()

        if game_state == 'credits' and event.type == pygame.KEYDOWN:
            # Play sound
            menu_click.play()

            if event.key == pygame.K_ESCAPE:
                game_state = 'start_menu'

        if game_state == 'intro' and event.type == pygame.KEYDOWN:
            # Play sound
            menu_click.play()
            main_menu_music.set_volume(0)
            bg_music.set_volume(0.5)

            game_state = 'game'
            frame_count = 0

        if game_state == 'game_over' and event.type == pygame.KEYDOWN:
            # Play sound
            menu_click.play()

            if event.key == pygame.K_SPACE:
                # Return to default values
                reset_game()
                game_state = 'game'

                main_menu_music.set_volume(0)
                bg_music.set_volume(0.5)

            if event.key == pygame.K_ESCAPE:
                # Return to default values
                reset_game()
                game_state = 'start_menu'

        if game_state == 'evac' and event.type == pygame.KEYDOWN:
            # Play sound
            menu_click.play()

            # Return to default values
            reset_game()
            game_state = 'start_menu'

    # Fix FPS at 60
    clock.tick(FPS)

    # Start menu
    if game_state == 'start_menu':
        bg_music.set_volume(0)
        screen.blit(start_menu_bg, start_menu_bg_rect)
        screen.blit(start_button, start_button_rect)
        screen.blit(credits_button, credits_button_rect)
        screen.blit(exit_button, exit_button_rect)

    # Credits
    if game_state == 'credits':
        screen.blit(intro_bg, intro_bg_rect)
        screen.blit(credits_text_bw, credits_text_bw_rect)
        screen.blit(credits_text_jp, credits_text_jp_rect)
        screen.blit(hackathon_text, hackathon_text_rect)
        screen.blit(return_text, return_text_rect)

    # Intro
    if game_state == 'intro':
        screen.blit(intro_bg, intro_bg_rect)
        screen.blit(story, story_rect)
        if frame_count % 2 == 0:
            story_rect.y -= 1

        if story_rect.y < -50:
            screen.blit(intro_text, intro_text_rect)

    # Game over
    if game_state == 'game_over':
        main_menu_music.set_volume(0.5)
        bg_music.set_volume(0)

        screen.blit(intro_bg, intro_bg_rect)
        screen.blit(game_over_text, game_over_text_rect)
        screen.blit(play_again_text, play_again_text_rect)
        screen.blit(runaway_text, runaway_text_rect)

    # Outro
    if game_state == 'evac':
        main_menu_music.set_volume(0.5)
        bg_music.set_volume(0)

        screen.blit(outro_bg, outro_bg_rect)
        screen.blit(evac, evac_rect)
        if frame_count % 2 == 0:
            evac_rect.y -= 1

        if evac_rect.y < -50:
            screen.blit(outro_text, outro_text_rect)

    # Game
    if game_state == 'game':
        if frame_count % 60 == 0:
            seconds_count += 1
            if seconds_count == 60:
                seconds_count = 0
                minutes_count += 1

        # Background music
        bg_music.set_volume(0.5)

        # Spawn enemies
        if frame_count % RIPPER_SPAWN_RATE == 0:
            spawn_enemy(camera, enemies, "ripper")

        if minutes_count >= 3 and frame_count % ARACHNID_SPAWN_RATE == 0:
            spawn_enemy(camera, enemies, "arachnid")

        if minutes_count >= 6 and frame_count % RHINO_SPAWN_RATE == 0:
            spawn_enemy(camera, enemies, "rhino")

        # Spawn power-ups
        if minutes_count >= 1 and frame_count % GRENADE_SPAWN_RATE == 0:
            spawn_power_up(camera, power_ups, "grenade")

        if minutes_count >= 1 and frame_count % SHOOTING_SPEED_SPAWN_RATE == 0:
            spawn_power_up(camera, power_ups, "shooting_speed")

        if minutes_count >= 5 and frame_count % HP_SPAWN_RATE == 0:
            spawn_power_up(camera, power_ups, "hp")

        if minutes_count >= 6 and frame_count % FIRE_SPAWN_RATE == 0:
            spawn_power_up(camera, power_ups, "fire")

        # Update enemies
        for enemy in enemies:
            enemy.update(player, camera, enemies, tiles)
            enemy.frames_since_last_damage += 1

        # Update player
        player.update()

        # Apply the camera offset to all tiles and sprites
        for tile in tiles:
            camera.apply(tile)

        for sprite in players:
            camera.apply(sprite)

        for grenade in grenades:
            camera.apply(grenade)
            grenade.update()

        for fire in fires:
            fire.update()

        for power_up in power_ups:
            camera.apply(power_up)
            power_up.update()

        # Automatically shoot at the closest enemy every 20 frames
        if frame_count % player.shoot_rate == 0:
            player.shoot_bullet(bullets, camera, enemies)

        # Update bullets
        for bullet in bullets:
            bullet.update(camera)
            for enemy in enemies:
                if bullet.rect.colliderect(enemy.colliderect):
                    enemy.take_damage(5)
                    if enemy.health <= 0:
                        enemies.remove(enemy)
                    bullets.remove(bullet)
                    break

        # Drop grenades after 3 minutes (180 seconds) of gameplay and explode every 5 seconds (300 frames)
        if minutes_count * 60 + seconds_count >= 10:
            if player.grenades > 0:
                if frame_count % 300 == 0:
                    grenade_timer = 50
                    for grenade in range(player.grenades):
                        Grenade.throw_grenade(grenades, 10)

                if grenade_timer > 0:
                    grenade_timer -= 1

                # Remove grenade and deal damage to enemies in the area after 300 frames
                if grenade_timer == 0:
                    Grenade.explode(grenades, enemies)

        # Set off ring of fire after 5 minutes (300 seconds) of gameplay and explode every 5 seconds (300 frames)
        if minutes_count * 60 + seconds_count >= 10:
            if player.ring_of_fire:
                if frame_count % player.ring_of_fire_rate == 0:
                    fire_timer = 50
                    RingOfFire.set_off(fires, 20)

                if fire_timer > 0:
                    fire_timer -= 1

                # Remove grenade and deal damage to enemies in the area after 300 frames
                if fire_timer == 0:
                    RingOfFire.explode(fires, enemies)

        # Fill the screen black
        screen.fill((0, 0, 0))

        # Get visible tiles
        visible_tiles = get_visible_tiles(tiles, camera)

        # Draw visible tiles
        for tile in visible_tiles:
            screen.blit(tile.image, tile.rect)

        # Draw evacuation zone
        if evac_time:
            overlay = draw_overlay(screen, camera, 180, 180, TILE_SIZE)

        # Draw enemies
        enemies.draw(screen)

        # Draw power-ups
        power_ups.draw(screen)

        # Draw player
        players.draw(screen)

        # Draw the player's health bar
        player.draw_health_bar(screen, camera)

        # Draw bullets
        bullets.draw(screen)

        # Draw grenades on the screen
        grenades.draw(screen)

        # Draw fires on the screen
        fires.draw(screen)

        # Render timer and power-ups UI
        render_timer()
        render_power_up_ui()

        # Conditions for game over
        if player.health <= 0 and player.dead_sound_flag:
            game_state = 'game_over'
            player.dead_sound.play()
            player.dead_sound_flag = False

        if timeout and player.rect.colliderect(overlay):
            game_state = 'evac'

        elif timeout:
            game_state = 'game_over'

    # Increment the frame count
    frame_count += 1

    # Update the display
    pygame.display.flip()

# Clean up
pygame.quit()

