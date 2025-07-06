import pygame

class Block:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_x = x
        self.base_y = y
        self.bounce_offset = 0.0
        self.bouncing = False
        self.bounce_speed = -8.0  # 跳ね上がる初速（大きくして目立つように）
        self.bounce_gravity = 1.0  # 跳ね上がる重力（大きくして戻りやすく）
        self.bounce_vy = 0.0

    def hit_from_below(self):
        if not self.bouncing:
            self.bouncing = True
            self.bounce_vy = self.bounce_speed

    def update(self):
        if self.bouncing:
            self.bounce_offset += self.bounce_vy
            self.bounce_vy += self.bounce_gravity
            if self.bounce_offset >= 0:
                self.bounce_offset = 0
                self.bouncing = False
                self.bounce_vy = 0
            self.rect.y = self.base_y + int(round(self.bounce_offset))
        else:
            self.rect.y = self.base_y

    def draw(self, surface, camera_x):
        # camera_x分だけ左にずらして描画
        draw_rect = self.rect.copy()
        draw_rect.x -= camera_x
        surface.blit(self.image, draw_rect)

import sys
import os

# タイルサイズ
TILE_SIZE = 16
SCALE = 2
TILE_SIZE_SCALED = TILE_SIZE * SCALE

# 画面サイズ
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 240

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

# タイルマップ（0:空, 1:床, 2:ブロック）
# 横スクロール用に横幅を拡張
TILEMAP = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# 下2行を床にする
for y in range(len(TILEMAP)-2, len(TILEMAP)):
    for x in range(len(TILEMAP[0])):
        TILEMAP[y][x] = 1

# 適当にブロックを配置
TILEMAP[10][5] = 2
TILEMAP[10][6] = 2
TILEMAP[7][10] = 2
TILEMAP[10][20] = 2
TILEMAP[7][25] = 2
TILEMAP[12][28] = 2

# --- 床(t==1)のみ返す。ブロック(t==2)はBlockクラスで管理 ---
def get_tile_rects():
    rects = []
    for y, row in enumerate(TILEMAP):
        for x, t in enumerate(row):
            if t == 1:  # 床だけ
                rects.append(pygame.Rect(x * TILE_SIZE_SCALED, y * TILE_SIZE_SCALED, TILE_SIZE_SCALED, TILE_SIZE_SCALED))
    return rects

class Mario(pygame.sprite.Sprite):
    def __init__(self, images, pos, tile_rects, blocks):
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
        self.tile_rects = tile_rects
        self.blocks = blocks  # Blockインスタンスのリスト

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

            # 横移動
            self.rect.x += int(self.vx)
            # 横方向の当たり判定（床）
            for tile in self.tile_rects():
                if self.rect.colliderect(tile):
                    if self.vx > 0:
                        self.rect.right = tile.left
                        self.vx = 0
                    elif self.vx < 0:
                        self.rect.left = tile.right
                        self.vx = 0
            # 横方向の当たり判定（ブロック）
            for block in self.blocks:
                if self.rect.colliderect(block.rect):
                    if self.vx > 0:
                        self.rect.right = block.rect.left
                        self.vx = 0
                    elif self.vx < 0:
                        self.rect.left = block.rect.right
                        self.vx = 0

            # 重力
            self.vy += GRAVITY
            self.rect.y += int(self.vy)
            self.on_ground = False
            # 縦方向の当たり判定（床）
            for tile in self.tile_rects():
                if self.rect.colliderect(tile):
                    if self.vy > 0:
                        self.rect.bottom = tile.top
                        self.vy = 0
                        self.on_ground = True
                        self.jumping = False
                        self.jump_hold_count = 0
                    elif self.vy < 0:
                        self.rect.top = tile.bottom
                        self.vy = 0
            # 縦方向の当たり判定（ブロック）
            for block in self.blocks:
                if self.rect.colliderect(block.rect):
                    if self.vy > 0:
                        self.rect.bottom = block.rect.top
                        self.vy = 0
                        self.on_ground = True
                        self.jumping = False
                        self.jump_hold_count = 0
                    elif self.vy < 0:
                        # ブロックは跳ね上がるが、床は跳ね上がらない
                        # ここでvyを0にしてしまうと、mainループでの跳ね上がり判定に使えない
                        # vyを0にせず、mainループでの跳ね上がり判定後にvyを0にする
                        self.rect.top = block.rect.bottom
                        # self.vy = 0  # ここをコメントアウトまたは削除

            # マップ外に出ないように（マップ全体の範囲で制限）
            map_pixel_width = len(TILEMAP[0]) * TILE_SIZE_SCALED
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = 0
            if self.rect.right > map_pixel_width:
                self.rect.right = map_pixel_width
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
    def __init__(self, images, death_img, pos, tile_rects, blocks):
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
        self._alive = True
        self.tile_rects = tile_rects
        self.blocks = blocks  # Blockインスタンスのリスト

    @property
    def alive(self):
        return self._alive

    def update(self):
        if not self.squashed:
            self.rect.x += int(self.vx)
            # 横方向の当たり判定（床）
            for tile in self.tile_rects():
                if self.rect.colliderect(tile):
                    if self.vx > 0:
                        self.rect.right = tile.left
                        self.vx = -KURIBO_WALK_SPEED
                    elif self.vx < 0:
                        self.rect.left = tile.right
                        self.vx = KURIBO_WALK_SPEED
            # 横方向の当たり判定（ブロック）
            for block in self.blocks:
                if self.rect.colliderect(block.rect):
                    if self.vx > 0:
                        self.rect.right = block.rect.left
                        self.vx = -KURIBO_WALK_SPEED
                    elif self.vx < 0:
                        self.rect.left = block.rect.right
                        self.vx = KURIBO_WALK_SPEED

            self.vy += KURIBO_GRAVITY
            self.rect.y += int(self.vy)
            self.on_ground = False
            # 縦方向の当たり判定（床）
            for tile in self.tile_rects():
                if self.rect.colliderect(tile):
                    if self.vy > 0:
                        self.rect.bottom = tile.top
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:
                        self.rect.top = tile.bottom
                        self.vy = 0
            # 縦方向の当たり判定（ブロック）
            for block in self.blocks:
                if self.rect.colliderect(block.rect):
                    if self.vy > 0:
                        self.rect.bottom = block.rect.top
                        self.vy = 0
                        self.on_ground = True
                    elif self.vy < 0:
                        self.rect.top = block.rect.bottom
                        self.vy = 0

            # マップ端で反転
            map_pixel_width = len(TILEMAP[0]) * TILE_SIZE_SCALED
            if self.rect.left < 0:
                self.rect.left = 0
                self.vx = KURIBO_WALK_SPEED
            if self.rect.right > map_pixel_width:
                self.rect.right = map_pixel_width
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
                self._alive = False

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

    # タイル画像
    wall_img = load_and_scale(os.path.join("images", "wall.png"))
    block_img = load_and_scale(os.path.join("images", "block.png"))

    # タイル当たり判定取得関数
    def tile_rects():
        return get_tile_rects()

    # ブロックオブジェクトのリストを作成
    blocks = []
    for y, row in enumerate(TILEMAP):
        for x, t in enumerate(row):
            if t == 2:
                blocks.append(Block(block_img, x * TILE_SIZE_SCALED, y * TILE_SIZE_SCALED))

    # スプライト生成
    mario = Mario(
        images={
            'stand': mario_stand,
            'walk': mario_walk,
            'jump': mario_jump,
            'death': mario_death
        },
        pos=(SCREEN_WIDTH * SCALE // 2, 10 * TILE_SIZE_SCALED),
        tile_rects=tile_rects,
        blocks=blocks
    )

    kuribo = Kuribo(
        images=kuribo_walk,
        death_img=kuribo_death_img,
        pos=(80 * SCALE, 10 * TILE_SIZE_SCALED),
        tile_rects=tile_rects,
        blocks=blocks
    )

    all_sprites = pygame.sprite.Group()
    all_sprites.add(mario)
    all_sprites.add(kuribo)

    clock = pygame.time.Clock()
    running = True

    # カメラのx座標
    camera_x = 0

    # マップのピクセル幅
    map_pixel_width = len(TILEMAP[0]) * TILE_SIZE_SCALED

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

        # マリオがブロックを下から叩いたか判定
        for block in blocks:
            # マリオの頭がブロックに当たった瞬間のみ跳ね上げる
            prev_top = mario.rect.top - int(mario.vy)
            # 修正版: prev_topがblock.rect.bottom以上、かつ現在のtopがblock.rect.bottom以下（未満だと1ピクセルのズレで判定されないことがある）
            if (mario.vy < 0 and
                prev_top >= block.rect.bottom and
                mario.rect.top <= block.rect.bottom and
                mario.rect.right > block.rect.left and
                mario.rect.left < block.rect.right):
                block.hit_from_below()
                # 跳ね上がり判定後にvyを0にする
                mario.vy = 0
        # ※床は跳ね上がらない（床はBlockクラスで管理されていない）

        # ブロックの更新
        for block in blocks:
            block.update()

        # カメラのx座標をマリオ中心で更新
        # マリオが画面中央より右に行ったらカメラを右に動かす
        # 画面中央より左に行ったらカメラを左に動かす
        mario_center_x = mario.rect.centerx
        camera_x = mario_center_x - (SCREEN_WIDTH * SCALE) // 2
        # カメラの範囲をマップ内に制限
        camera_x = max(0, min(camera_x, map_pixel_width - SCREEN_WIDTH * SCALE))

        screen.fill((92, 148, 252))  # マリオの空色

        # タイルマップの描画（カメラ分ずらす）
        for y, row in enumerate(TILEMAP):
            for x, t in enumerate(row):
                if t == 1:
                    draw_x = x * TILE_SIZE_SCALED - camera_x
                    draw_y = y * TILE_SIZE_SCALED
                    # 画面外は描画しない
                    if -TILE_SIZE_SCALED < draw_x < SCREEN_WIDTH * SCALE:
                        screen.blit(wall_img, (draw_x, draw_y))
                # ブロックはBlockクラスで描画するのでここでは描画しない

        # ブロックの描画
        for block in blocks:
            block.draw(screen, camera_x)

        # スプライト描画
        # マリオとクリボーの描画位置もカメラ分ずらす
        if kuribo.alive:
            kuribo_draw_rect = kuribo.rect.copy()
            kuribo_draw_rect.x -= camera_x
            screen.blit(kuribo.image, kuribo_draw_rect)
        mario_draw_rect = mario.rect.copy()
        mario_draw_rect.x -= camera_x
        screen.blit(mario.image, mario_draw_rect)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
