import pygame

# 床の情報
FLOOR_Y = 200  # 画面下から少し上に床を設置（SCALEをかけない値に修正）
FLOOR_HEIGHT = 16  # 床の厚み（SCALEをかけない値に修正）
import sys
import os

# 初代スーパーマリオの解像度
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240

# 倍率
SCALE = 2

# マリオのパラメータ
MARIO_WALK_MAX_SPEED = 2.2 * SCALE
MARIO_DASH_MAX_SPEED = 4.0 * SCALE
MARIO_ACCEL = 0.15 * SCALE
MARIO_DECEL = 0.18 * SCALE
MARIO_AIR_ACCEL = 0.08 * SCALE
MARIO_AIR_DECEL = 0.10 * SCALE

JUMP_POWER = 5.2 * SCALE
GRAVITY = 0.5 * SCALE
JUMP_HOLD_TIME = 12

# クリボーのパラメータ
KURIBO_WALK_SPEED = 1.0 * SCALE
KURIBO_GRAVITY = GRAVITY

def load_and_scale(path):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (img.get_width() * SCALE, img.get_height() * SCALE))

class Mario(pygame.sprite.Sprite):
    def __init__(self, images, pos, floor_rect):
        super().__init__()
        self.images = images  # dict: stand, walk(list), jump, death
        self.image = self.images['stand']
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.walk_frame = 0
        self.walk_timer = 0
        self.MARIO_WALK_ANIM_INTERVAL = 6
        self.jumping = False
        self.jump_hold_count = 0
        self.dead = False
        self.death_timer = 0
        self.MARIO_DEATH_JUMP_VY = -8.0 * SCALE
        self.MARIO_DEATH_GRAVITY = 0.35 * SCALE
        self.MARIO_DEATH_DURATION = 120
        self.floor_rect = floor_rect

    def update(self, keys):
        if not self.dead:
            dash = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            max_speed = MARIO_DASH_MAX_SPEED if dash else MARIO_WALK_MAX_SPEED
            accel = MARIO_ACCEL if self.on_ground else MARIO_AIR_ACCEL
            decel = MARIO_DECEL if self.on_ground else MARIO_AIR_DECEL

            move_left = keys[pygame.K_LEFT]
            move_right = keys[pygame.K_RIGHT]

            if move_left and not move_right:
                if self.vx > -max_speed:
                    self.vx -= accel
                    if self.vx < -max_speed:
                        self.vx = -max_speed
                self.facing_right = False
            elif move_right and not move_left:
                if self.vx < max_speed:
                    self.vx += accel
                    if self.vx > max_speed:
                        self.vx = max_speed
                self.facing_right = True
            else:
                if self.vx > 0:
                    self.vx -= decel
                    if self.vx < 0:
                        self.vx = 0
                elif self.vx < 0:
                    self.vx += decel
                    if self.vx > 0:
                        self.vx = 0

            # ジャンプ処理
            if keys[pygame.K_SPACE]:
                if self.on_ground and not self.jumping:
                    self.vy = -JUMP_POWER
                    self.jumping = True
                    self.jump_hold_count = 0
                    self.on_ground = False
                elif self.jumping and self.jump_hold_count < JUMP_HOLD_TIME:
                    self.vy -= 0.35 * SCALE
                    self.jump_hold_count += 1
            else:
                self.jumping = False

            self.rect.x += int(self.vx)
            self.vy += GRAVITY
            self.rect.y += int(self.vy)

            # 床との接地判定
            if self.rect.colliderect(self.floor_rect):
                if self.vy >= 0 and self.rect.bottom - self.floor_rect.top < 32 * SCALE:
                    self.rect.bottom = self.floor_rect.top
                    self.vy = 0
                    self.on_ground = True
                    self.jumping = False
                    self.jump_hold_count = 0
                else:
                    self.on_ground = False
            else:
                self.on_ground = False

            # 画面外に出ないように
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = 0
            if self.rect.right > SCREEN_WIDTH * SCALE:
                self.rect.right = SCREEN_WIDTH * SCALE
                self.vx = 0

            # アニメーション
            if abs(self.vx) > 0.5 and self.on_ground:
                self.walk_timer += 1
                if self.walk_timer >= self.MARIO_WALK_ANIM_INTERVAL:
                    self.walk_frame = (self.walk_frame + 1) % len(self.images['walk'])
                    self.walk_timer = 0
                self.image = self.images['walk'][self.walk_frame]
            elif not self.on_ground:
                self.image = self.images['jump']
                self.walk_frame = 0
                self.walk_timer = 0
            else:
                self.image = self.images['stand']
                self.walk_frame = 0
                self.walk_timer = 0

            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
        else:
            # 死亡時
            self.vx = 0
            self.vy += self.MARIO_DEATH_GRAVITY
            self.rect.y += int(self.vy)
            self.death_timer += 1
            self.image = self.images['death']
            if self.death_timer > self.MARIO_DEATH_DURATION or self.rect.top > SCREEN_HEIGHT * SCALE:
                return 'dead'  # signal to quit

    def die(self):
        self.dead = True
        self.death_timer = 0
        self.vy = self.MARIO_DEATH_JUMP_VY
        self.jumping = False
        self.on_ground = False

class Kuribo(pygame.sprite.Sprite):
    def __init__(self, images, death_img, pos, floor_rect):
        super().__init__()
        self.images = images  # list: walk frames
        self.death_img = death_img
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.midbottom = pos
        self.vx = -KURIBO_WALK_SPEED
        self.vy = 0.0
        self.on_ground = False
        self.frame = 0
        self.timer = 0
        self.KURIBO_ANIM_INTERVAL = 16
        self.squashed = False
        self.squash_timer = 0
        self.KURIBO_SQUASH_DURATION = 40
        self.alive = True
        self.floor_rect = floor_rect

    def update(self):
        if not self.squashed:
            self.rect.x += int(self.vx)
            self.vy += KURIBO_GRAVITY
            self.rect.y += int(self.vy)

            # 床との接地判定
            if self.rect.colliderect(self.floor_rect):
                if self.vy >= 0 and self.rect.bottom - self.floor_rect.top < 32 * SCALE:
                    self.rect.bottom = self.floor_rect.top
                    self.vy = 0
                    self.on_ground = True
                else:
                    self.on_ground = False
            else:
                self.on_ground = False

            # 画面端で反転
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = KURIBO_WALK_SPEED
            if self.rect.right > SCREEN_WIDTH * SCALE:
                self.rect.right = SCREEN_WIDTH * SCALE
                self.vx = -KURIBO_WALK_SPEED

            # アニメーション
            self.timer += 1
            if self.timer >= self.KURIBO_ANIM_INTERVAL:
                self.frame = (self.frame + 1) % 2
                self.timer = 0
            self.image = self.images[self.frame]
        else:
            self.squash_timer += 1
            self.image = self.death_img
            # 潰れた画像の下端を元のクリボーの下端に合わせる
            death_rect = self.death_img.get_rect()
            death_rect.midbottom = self.rect.midbottom
            self.rect = death_rect
            if self.squash_timer >= self.KURIBO_SQUASH_DURATION:
                self.alive = False

    def squash(self):
        self.squashed = True
        self.squash_timer = 0
        self.vx = 0
        self.vy = 0

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH * SCALE, SCREEN_HEIGHT * SCALE))
    pygame.display.set_caption("スーパーマリオ風")

    # 画像の読み込み
    mario_stand = load_and_scale(os.path.join("images", "mario001.png"))
    mario_walk = [
        load_and_scale(os.path.join("images", "mario002.png")),
        load_and_scale(os.path.join("images", "mario003.png")),
        load_and_scale(os.path.join("images", "mario004.png")),
    ]
    mario_jump = load_and_scale(os.path.join("images", "mario_jump.png"))
    mario_death = load_and_scale(os.path.join("images", "mario_death.png"))

    kuribo_img = load_and_scale(os.path.join("images", "kuribo.png"))
    kuribo_walk = [
        kuribo_img,
        pygame.transform.flip(kuribo_img, True, False)
    ]
    kuribo_death_img = load_and_scale(os.path.join("images", "kuribo_death.png"))

    floor_rect = pygame.Rect(
        0,
        FLOOR_Y * SCALE,
        SCREEN_WIDTH * SCALE,
        FLOOR_HEIGHT * SCALE
    )

    # スプライト生成
    mario = Mario(
        images={
            'stand': mario_stand,
            'walk': mario_walk,
            'jump': mario_jump,
            'death': mario_death
        },
        pos=(SCREEN_WIDTH * SCALE // 2, (FLOOR_Y - 40) * SCALE),
        floor_rect=floor_rect
    )

    kuribo = Kuribo(
        images=kuribo_walk,
        death_img=kuribo_death_img,
        pos=(80 * SCALE, FLOOR_Y * SCALE),
        floor_rect=floor_rect
    )

    all_sprites = pygame.sprite.Group()
    all_sprites.add(mario)
    all_sprites.add(kuribo)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # マリオの更新
        mario_result = mario.update(keys)
        if mario_result == 'dead':
            running = False

        # クリボーの更新
        if kuribo.alive:
            kuribo.update()
        else:
            all_sprites.remove(kuribo)

        # マリオとクリボーの当たり判定
        if kuribo.alive and not kuribo.squashed and not mario.dead and mario.rect.colliderect(kuribo.rect):
            # マリオが上からクリボーに当たったか判定
            if mario.vy > 0 and mario.rect.bottom - kuribo.rect.top < 16 * SCALE and mario.rect.centery < kuribo.rect.centery:
                kuribo.squash()
                mario.vy = -JUMP_POWER * 0.6
            else:
                mario.die()

        screen.fill((92, 148, 252))  # マリオの空色

        # 床の描画
        pygame.draw.rect(screen, (160, 82, 45), floor_rect)

        # スプライト描画
        if kuribo.alive:
            screen.blit(kuribo.image, kuribo.rect)
        screen.blit(mario.image, mario.rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
