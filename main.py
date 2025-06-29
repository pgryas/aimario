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
# 最高速度（通常/Bダッシュ）、加速度、減速度
MARIO_WALK_MAX_SPEED = 2.2 * SCALE  # 通常歩き最大速度
MARIO_DASH_MAX_SPEED = 4.0 * SCALE  # Bダッシュ最大速度
MARIO_ACCEL = 0.15 * SCALE          # 加速度
MARIO_DECEL = 0.18 * SCALE          # 減速度
MARIO_AIR_ACCEL = 0.08 * SCALE      # 空中加速度
MARIO_AIR_DECEL = 0.10 * SCALE      # 空中減速度

# ジャンプ力と重力を初代スーパーマリオの仕様に近づけて調整
JUMP_POWER = 5.2 * SCALE  # ピョーンの高さを少し低く設定
GRAVITY = 0.5 * SCALE     # 重力も少し弱めに
JUMP_HOLD_TIME = 12       # ホールド時間も短めに

# クリボーのパラメータ
KURIBO_WALK_SPEED = 1.0 * SCALE  # クリボーの歩行速度
KURIBO_GRAVITY = GRAVITY         # クリボーにも同じ重力を適用

def load_and_scale(path):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (img.get_width() * SCALE, img.get_height() * SCALE))

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
    mario_death = load_and_scale(os.path.join("images", "mario_death.png"))  # 死亡画像

    # クリボーの画像を1枚だけ読み込む
    kuribo_img = load_and_scale(os.path.join("images", "kuribo.png"))
    # クリボーの歩行アニメーションは、左右反転画像を使ってパタパタ歩くようにする
    kuribo_walk = [
        kuribo_img,
        pygame.transform.flip(kuribo_img, True, False)
    ]
    # 潰れたクリボー画像の読み込み
    kuribo_death_img = load_and_scale(os.path.join("images", "kuribo_death.png"))

    # クリボーの初期位置を設定（床の上、左側に表示）
    kuribo_rect = kuribo_img.get_rect()
    kuribo_rect.midbottom = (80 * SCALE, FLOOR_Y * SCALE)

    # クリボーのアニメーション用変数
    kuribo_frame = 0
    kuribo_timer = 0
    # 本家マリオのクリボー歩行アニメは16フレームごとに切り替え（60fpsなら約0.27秒ごと）
    KURIBO_ANIM_INTERVAL = 16

    # クリボーの移動・物理用変数
    kuribo_vx = -KURIBO_WALK_SPEED  # 最初は左向きに移動
    kuribo_vy = 0.0
    kuribo_on_ground = False

    # クリボーの状態管理
    kuribo_alive = True
    kuribo_squashed = False
    kuribo_squash_timer = 0
    KURIBO_SQUASH_DURATION = 40  # 潰れてから消えるまでのフレーム数（約0.66秒）

    # マリオの初期位置
    mario_rect = mario_stand.get_rect()
    mario_rect.midbottom = (SCREEN_WIDTH * SCALE // 2, (FLOOR_Y - 40) * SCALE)
    mario_vx = 0.0
    mario_vy = 0.0
    on_ground = False
    facing_right = True

    walk_frame = 0
    walk_timer = 0

    # 歩きアニメーションのフレーム間隔（小さいほど速く切り替わる）
    MARIO_WALK_ANIM_INTERVAL = 6

    # ジャンプホールド用変数
    jumping = False
    jump_hold_count = 0

    # 死亡状態管理
    mario_dead = False
    mario_death_timer = 0
    MARIO_DEATH_JUMP_VY = -8.0 * SCALE  # 死亡時のジャンプ初速度
    MARIO_DEATH_GRAVITY = 0.35 * SCALE  # 死亡時の重力（本家は少し弱め）
    MARIO_DEATH_DURATION = 120  # 死亡演出の長さ（2秒）

    # 床のRect
    floor_rect = pygame.Rect(
        0,
        FLOOR_Y * SCALE,
        SCREEN_WIDTH * SCALE,
        FLOOR_HEIGHT * SCALE
    )

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        if not mario_dead:
            # Bダッシュ判定（左シフトまたは右シフト）
            dash = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            max_speed = MARIO_DASH_MAX_SPEED if dash else MARIO_WALK_MAX_SPEED
            accel = MARIO_ACCEL if on_ground else MARIO_AIR_ACCEL
            decel = MARIO_DECEL if on_ground else MARIO_AIR_DECEL

            move_left = keys[pygame.K_LEFT]
            move_right = keys[pygame.K_RIGHT]

            # 左右移動の加減速処理
            if move_left and not move_right:
                if mario_vx > -max_speed:
                    mario_vx -= accel
                    if mario_vx < -max_speed:
                        mario_vx = -max_speed
                facing_right = False
            elif move_right and not move_left:
                if mario_vx < max_speed:
                    mario_vx += accel
                    if mario_vx > max_speed:
                        mario_vx = max_speed
                facing_right = True
            else:
                # 減速（慣性で滑る）
                if mario_vx > 0:
                    mario_vx -= decel
                    if mario_vx < 0:
                        mario_vx = 0
                elif mario_vx < 0:
                    mario_vx += decel
                    if mario_vx > 0:
                        mario_vx = 0

            # ジャンプ処理（ホールドで高さ変化）
            if keys[pygame.K_SPACE]:
                if on_ground and not jumping:
                    # ジャンプ開始
                    mario_vy = -JUMP_POWER
                    jumping = True
                    jump_hold_count = 0
                    on_ground = False
                elif jumping and jump_hold_count < JUMP_HOLD_TIME:
                    # ジャンプ中にスペースを押し続けている間は上昇速度を維持
                    mario_vy -= 0.35 * SCALE  # 追加で上昇力を与える（値を控えめに）
                    jump_hold_count += 1
            else:
                # スペースを離したらジャンプホールド終了
                jumping = False

            # 横移動
            mario_rect.x += int(mario_vx)

            # 重力
            mario_vy += GRAVITY
            mario_rect.y += int(mario_vy)

            # 床との接地判定
            if mario_rect.colliderect(floor_rect):
                # マリオが床の上にいる場合のみ着地
                if mario_vy >= 0 and mario_rect.bottom - floor_rect.top < 32 * SCALE:
                    mario_rect.bottom = floor_rect.top
                    mario_vy = 0
                    on_ground = True
                    jumping = False
                    jump_hold_count = 0
                else:
                    on_ground = False
            else:
                on_ground = False

            # 画面外に出ないように
            if mario_rect.left < 0:
                mario_rect.left = 0
                mario_vx = 0
            if mario_rect.right > SCREEN_WIDTH * SCALE:
                mario_rect.right = SCREEN_WIDTH * SCALE
                mario_vx = 0

        else:
            # 死亡時の挙動
            mario_vx = 0  # 横移動なし
            mario_vy += MARIO_DEATH_GRAVITY
            mario_rect.y += int(mario_vy)
            mario_death_timer += 1
            # 死亡演出が終わったら終了（またはリセット等）
            if mario_death_timer > MARIO_DEATH_DURATION or mario_rect.top > SCREEN_HEIGHT * SCALE:
                running = False

        # --- ここからクリボーの移動・重力処理 ---
        if kuribo_alive:
            if not kuribo_squashed:
                # 横移動
                kuribo_rect.x += int(kuribo_vx)

                # 重力
                kuribo_vy += KURIBO_GRAVITY
                kuribo_rect.y += int(kuribo_vy)

                # 床との接地判定
                if kuribo_rect.colliderect(floor_rect):
                    # クリボーが床の上にいる場合のみ着地
                    if kuribo_vy >= 0 and kuribo_rect.bottom - floor_rect.top < 32 * SCALE:
                        kuribo_rect.bottom = floor_rect.top
                        kuribo_vy = 0
                        kuribo_on_ground = True
                    else:
                        kuribo_on_ground = False
                else:
                    kuribo_on_ground = False

                # 画面端で反転
                if kuribo_rect.left < 0:
                    kuribo_rect.left = 0
                    kuribo_vx = KURIBO_WALK_SPEED  # 右向きに反転
                if kuribo_rect.right > SCREEN_WIDTH * SCALE:
                    kuribo_rect.right = SCREEN_WIDTH * SCALE
                    kuribo_vx = -KURIBO_WALK_SPEED  # 左向きに反転

            # --- ここまでクリボーの移動・重力処理 ---

            # マリオがクリボーを踏んだか判定
            if not kuribo_squashed and not mario_dead and mario_rect.colliderect(kuribo_rect):
                # マリオが上からクリボーに当たったか判定
                # マリオの下端がクリボーの上端より上から接触し、かつマリオが下向きに落下している場合
                if mario_vy > 0 and mario_rect.bottom - kuribo_rect.top < 16 * SCALE and mario_rect.centery < kuribo_rect.centery:
                    kuribo_squashed = True
                    kuribo_squash_timer = 0
                    kuribo_vx = 0
                    kuribo_vy = 0
                    # マリオを少し跳ね返す
                    mario_vy = -JUMP_POWER * 0.6
                else:
                    # 横や下から当たった場合はマリオ死亡
                    mario_dead = True
                    mario_death_timer = 0
                    # 死亡時のジャンプ
                    mario_vy = MARIO_DEATH_JUMP_VY
                    # 死亡時はジャンプ中扱い
                    jumping = False
                    on_ground = False

            # 潰れた後のタイマー処理
            if kuribo_squashed:
                kuribo_squash_timer += 1
                if kuribo_squash_timer >= KURIBO_SQUASH_DURATION:
                    kuribo_alive = False

        # アニメーションの選択
        # 歩く時はアニメーションするように修正
        if mario_dead:
            current_image = mario_death
            walk_frame = 0
            walk_timer = 0
        elif not on_ground:
            current_image = mario_jump
            walk_frame = 0
            walk_timer = 0
        elif abs(mario_vx) > 0.5:
            walk_timer += 1
            if walk_timer >= MARIO_WALK_ANIM_INTERVAL:
                walk_frame = (walk_frame + 1) % len(mario_walk)
                walk_timer = 0
            current_image = mario_walk[walk_frame]
        else:
            current_image = mario_stand
            walk_frame = 0
            walk_timer = 0

        # 向きの反転
        if not facing_right and not mario_dead:
            current_image = pygame.transform.flip(current_image, True, False)

        # クリボーのアニメーション更新
        if kuribo_alive and not kuribo_squashed:
            kuribo_timer += 1
            if kuribo_timer >= KURIBO_ANIM_INTERVAL:
                kuribo_frame = (kuribo_frame + 1) % 2
                kuribo_timer = 0

        screen.fill((92, 148, 252))  # マリオの空色

        # 床の描画
        pygame.draw.rect(screen, (160, 82, 45), floor_rect)

        # クリボーの描画（歩行アニメーションまたは潰れた画像）
        if kuribo_alive:
            if kuribo_squashed:
                # 潰れた画像を描画
                # 潰れた画像の下端を元のクリボーの下端に合わせる
                death_rect = kuribo_death_img.get_rect()
                death_rect.midbottom = kuribo_rect.midbottom
                screen.blit(kuribo_death_img, death_rect)
            else:
                # 進行方向による画像の左右反転は行わず、歩行アニメーションのみ
                kuribo_draw_img = kuribo_walk[kuribo_frame]
                screen.blit(kuribo_draw_img, kuribo_rect)
        # kuribo_aliveがFalseなら何も描画しない（消える）

        # マリオの描画
        screen.blit(current_image, mario_rect)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
