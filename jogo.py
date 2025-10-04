# Mini Roguelike (PgZero-only, ASCII-safe) - shooting + lives + win/lose
# - Only PgZero, math, random (no pygame)
# - Menu with Start / Sound ON-OFF / Exit
# - Hero & enemies animated (idle/walk)
# - Enemies patrol territory & chase hero
# - Shooting (SPACE / left click)
# - Lives: hero dies after 10 enemy touches -> Game Over screen
# - Win: if all enemies are killed -> Win screen

import random
import math


_last_mouse_pos = (0, 0)
def get_mouse_pos():
    return _last_mouse_pos
def on_mouse_move(pos, rel, buttons):
    global _last_mouse_pos
    _last_mouse_pos = pos

TITLE = "Mini Roguelike (ASCII)"
WIDTH, HEIGHT = 800, 600


GAME_STATE = "menu"
SOUND_ENABLED = True
game_time = 0.0

# lives / hits
MAX_HITS = 5
hero_hits = 0  

# ---- helpers
def dist2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

# ---- audio (safe)
def safe_music_play(track, loop=True, volume=0.6):
    if not SOUND_ENABLED:
        try:
            music.stop()
        except Exception:
            pass
        return
    try:
        music.set_volume(volume)
        music.play(track, loop=loop)
    except Exception:
        pass
def safe_sound_play(name, volume=0.8):
    if not SOUND_ENABLED:
        return
    try:
        s = sounds.__getattr__(name)
        s.set_volume(volume)
        s.play()
    except Exception:
        pass

# ---- animation
class SpriteAnimator:
    def __init__(self, frames, fps=6):
        self.frames = frames[:] if frames else []
        self.fps = max(1, int(fps))
        self.t = 0.0
        self.i = 0
    def update(self, dt):
        if not self.frames: return
        self.t += dt
        step = 1.0 / self.fps
        while self.t >= step:
            self.t -= step
            self.i = (self.i + 1) % len(self.frames)
    def current(self):
        if not self.frames: return ""
        return self.frames[self.i]

from pgzero.actor import Actor  # PgZero built-in

def draw_actor_or_circle(actor, img, x, y, r, color):
    ok = False
    if isinstance(actor, Actor):
        try:
            if img: actor.image = img
            actor.pos = (x, y)
            actor.draw()
            ok = True
        except Exception:
            ok = False
    if not ok:
        screen.draw.filled_circle((int(x), int(y)), int(r), color)
        screen.draw.circle((int(x), int(y)), int(r), (0, 0, 0))

# ---- entities
class Entity:
    def __init__(self, x, y, anim_idle, anim_walk, speed=120, radius=14, tint=(140,200,240)):
        self.x = float(x); self.y = float(y)
        self.state = "idle"
        self.speed = float(speed)
        self.anim_idle = anim_idle
        self.anim_walk = anim_walk
        self.radius = float(radius)
        self.tint = tint
        start_img = self.anim_idle.current() or self.anim_walk.current() or ""
        try:
            self.actor = Actor(start_img, (x, y))
        except Exception:
            self.actor = None
        self.hit_timer = 0.0
    def pos(self): return (self.x, self.y)
    def current_frame(self):
        return self.anim_walk.current() if self.state == "walk" else self.anim_idle.current()
    def update_anim(self, dt):
        (self.anim_walk if self.state == "walk" else self.anim_idle).update(dt)
        if self.hit_timer > 0: self.hit_timer -= dt
    def draw(self):
        if self.hit_timer > 0:
            screen.draw.filled_circle((int(self.x), int(self.y)), int(self.radius + 3), (255,80,80))
        draw_actor_or_circle(self.actor, self.current_frame(), self.x, self.y, self.radius, self.tint)
    def hit_flash(self, dur=0.15): self.hit_timer = dur

class Hero(Entity):
    def __init__(self, x, y):
        idle = [f"hero_idle_{i}" for i in range(4)]
        walk = [f"hero_walk_{i}" for i in range(4)]
        super().__init__(x, y, SpriteAnimator(idle, 6), SpriteAnimator(walk, 10),
                         speed=170, radius=15, tint=(90,190,255))
        # shooting
        self.fire_cooldown = 0.25
        self._time_since_last_shot = 0.0
        self.bullet_speed = 420.0
        # damage cooldown (to count discrete touches)
        self.damage_cooldown = 0.4
        self.damage_timer = 0.0
    def update(self, dt):
        dx = (1 if keyboard.right or keyboard.d else 0) - (1 if keyboard.left or keyboard.a else 0)
        dy = (1 if keyboard.down or keyboard.s else 0) - (1 if keyboard.up or keyboard.w else 0)
        if dx or dy:
            self.state = "walk"
            mag = (dx*dx + dy*dy) ** 0.5
            dx /= mag; dy /= mag
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt
        else:
            self.state = "idle"
        self.x = clamp(self.x, 16, WIDTH-16)
        self.y = clamp(self.y, 16, HEIGHT-16)
        self._time_since_last_shot += dt
        if self.damage_timer > 0: self.damage_timer -= dt
        self.update_anim(dt)
    def can_shoot(self): return self._time_since_last_shot >= self.fire_cooldown
    def shoot_towards(self, tx, ty, bullets_list):
        if not self.can_shoot(): return
        vx = tx - self.x; vy = ty - self.y
        mag = (vx*vx + vy*vy) ** 0.5 or 1.0
        vx /= mag; vy /= mag
        bx = Bullet(self.x + vx*(self.radius+6), self.y + vy*(self.radius+6),
                    vx*self.bullet_speed, vy*self.bullet_speed)
        bullets_list.append(bx)
        self._time_since_last_shot = 0.0
        safe_sound_play("shoot")

class Enemy(Entity):
    def __init__(self, x, y, territory_radius=140, chase_radius=150, base_speed=120, hue=0):
        idle = [f"enemy_idle_{i}" for i in range(4)]
        walk = [f"enemy_walk_{i}" for i in range(4)]
        color = (180, 90 + (hue*40) % 165, 120 + (hue*25) % 120)
        super().__init__(x, y, SpriteAnimator(idle, 6), SpriteAnimator(walk, 10),
                         speed=base_speed, radius=14, tint=color)
        self.home = (float(x), float(y))
        self.territory = float(territory_radius)
        self.chase_radius = float(chase_radius)
        self.tx, self.ty = x, y
        self._pick_wander_target()
    def _pick_wander_target(self):
        ang = random.random() * (2.0 * math.pi)
        rad = random.random() * self.territory
        self.tx = self.home[0] + math.cos(ang) * rad
        self.ty = self.home[1] + math.sin(ang) * rad
    def _dist_to(self, p): return math.hypot(self.x - p[0], self.y - p[1])
    def update(self, dt, hero_obj):
        hero_pos = hero_obj.pos()
        if self._dist_to(hero_pos) <= self.chase_radius:
            target = hero_pos
        else:
            target = (self.tx, self.ty)
            if self._dist_to(target) < 8: self._pick_wander_target()
        vx = target[0] - self.x; vy = target[1] - self.y
        mag = (vx*vx + vy*vy) ** 0.5
        if mag > 1e-3:
            vx /= mag; vy /= mag
            self.x += vx * self.speed * dt
            self.y += vy * self.speed * dt
            self.state = "walk"
        else:
            self.state = "idle"
        self.x = clamp(self.x, 16, WIDTH-16)
        self.y = clamp(self.y, 16, HEIGHT-16)
        self.update_anim(dt)

# ---- Bullet
class Bullet:
    def __init__(self, x, y, vx, vy, life=2.5, radius=5.0, tint=(255,200,80)):
        self.x = float(x); self.y = float(y)
        self.vx = float(vx); self.vy = float(vy)
        self.life = float(life)
        self.radius = float(radius)
        self.tint = tint
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
    def draw(self):
        screen.draw.filled_circle((int(self.x), int(self.y)), int(self.radius), self.tint)
        screen.draw.circle((int(self.x), int(self.y)), int(self.radius), (0,0,0))
    def is_alive(self):
        if self.life <= 0: return False
        if not (-50 <= self.x <= WIDTH+50 and -50 <= self.y <= HEIGHT+50): return False
        return True

# ---- world
hero = Hero(WIDTH // 2, HEIGHT // 2)
enemies = []
bullets = []

def start_game():
    global GAME_STATE, enemies, game_time, bullets, hero_hits, hero
    GAME_STATE = "playing"
    game_time = 0.0
    hero_hits = 0
    bullets = []
    # reset hero to center (new instance to clear timers)
    hero = Hero(WIDTH // 2, HEIGHT // 2)
    enemies = []
    spots = [(140,140), (660,120), (120,460), (680,480), (400,120), (400,500)]
    for i, (sx, sy) in enumerate(spots):
        enemies.append(Enemy(sx, sy,
                             territory_radius=random.randint(100, 180),
                             chase_radius=random.randint(130, 190),
                             base_speed=random.randint(100, 150),
                             hue=i))
    safe_music_play("bgm")

# ---- circular buttons (no Rect)
class CircleButton:
    def __init__(self, cx, cy, r, label):
        self.cx, self.cy, self.r = cx, cy, r
        self.label = label
    def hovered(self, pos): return dist2((self.cx, self.cy), pos) <= self.r * self.r
    def draw(self):
        base = (70, 90, 120); hi = (100, 130, 170)
        color = hi if self.hovered(get_mouse_pos()) else base
        screen.draw.filled_circle((self.cx, self.cy), self.r, color)
        screen.draw.circle((self.cx, self.cy), self.r, (220,230,240))
        screen.draw.text(self.label, center=(self.cx, self.cy), fontsize=28, color="white")

menu_buttons = [
    CircleButton(WIDTH // 2, 270, 60, "Start"),
    CircleButton(WIDTH // 2, 370, 60, "Sound: ON"),
    CircleButton(WIDTH // 2, 470, 60, "Exit"),
]
def _update_sound_button_label():
    menu_buttons[1].label = f"Sound: {'ON' if SOUND_ENABLED else 'OFF'}"

# ---- pgzero hooks
def update(dt):
    global game_time, enemies, bullets, hero_hits, GAME_STATE
    if GAME_STATE != "playing": return

    game_time += dt
    hero.update(dt)

    # enemies
    for e in enemies:
        e.update(dt, hero)

    # bullets
    alive_bullets = []
    for b in bullets:
        b.update(dt)
        if b.is_alive():
            alive_bullets.append(b)
    bullets[:] = alive_bullets

    # bullet -> enemy collision
    removed_enemies = []
    removed_bullets = []
    for bi, b in enumerate(bullets):
        for ei, e in enumerate(enemies):
            if math.hypot(b.x - e.x, b.y - e.y) < (b.radius + e.radius):
                removed_enemies.append(ei)
                removed_bullets.append(bi)
                e.hit_flash()
                safe_sound_play("enemy_die")
                break
    if removed_enemies:
        for idx in sorted(set(removed_enemies), reverse=True):
            try: enemies.pop(idx)
            except Exception: pass
    if removed_bullets:
        for idx in sorted(set(removed_bullets), reverse=True):
            try: bullets.pop(idx)
            except Exception: pass

    # hero <-> enemy collision (counts hits with cooldown)
    for e in enemies:
        if math.hypot(e.x - hero.x, e.y - hero.y) < (e.radius + hero.radius):
            if hero.damage_timer <= 0:
                hero_hits += 1
                hero.hit_flash()
                e.hit_flash()
                hero.damage_timer = hero.damage_cooldown
                safe_sound_play("hit")
                # small knockback
                vx = hero.x - e.x; vy = hero.y - e.y
                mag = (vx*vx + vy*vy) ** 0.5 or 1.0
                hero.x += (vx / mag) * 10
                hero.y += (vy / mag) * 10
            break  # only one hit counted per frame

    # check win/lose
    if hero_hits >= MAX_HITS:
        GAME_STATE = "gameover"
        try: music.stop()
        except Exception: pass
        safe_sound_play("game_over")
    elif len(enemies) == 0:
        GAME_STATE = "win"
        try: music.stop()
        except Exception: pass
        safe_sound_play("win")

def draw():
    screen.clear()
    if GAME_STATE == "menu":
        _draw_menu()
    elif GAME_STATE == "playing":
        _draw_game()
    elif GAME_STATE == "win":
        _draw_win()
    elif GAME_STATE == "gameover":
        _draw_gameover()
    else:
        _draw_quit()

def _draw_menu():
    screen.fill((18,18,22))
    screen.draw.text("Mini Roguelike", center=(WIDTH//2, 160), fontsize=52, color="white")
    for b in menu_buttons: b.draw()
    screen.draw.text("Controls: WASD / Arrows   Shoot: SPACE or Left Click",
                     center=(WIDTH//2, 540), fontsize=20, color=(210,210,210))

def _draw_game():
    screen.fill((22,26,32))
    # territories
    for e in enemies:
        screen.draw.circle((int(e.home[0]), int(e.home[1])), int(e.territory), (40,60,85))
    # entities
    for e in enemies: e.draw()
    hero.draw()
    # bullets
    for b in bullets: b.draw()
    # HUD
    lives_left = max(0, MAX_HITS - hero_hits)
    screen.draw.text(f"Time: {game_time:05.1f}", topleft=(10, 10), fontsize=28, color="white")
    screen.draw.text(f"Enemies: {len(enemies)}", topleft=(10, 42), fontsize=22, color=(200,200,200))
    screen.draw.text(f"Lives: {lives_left}/{MAX_HITS}", topleft=(10, 70), fontsize=22, color=(200,230,200))

def _draw_win():
    screen.fill((16, 24, 18))
    screen.draw.text("YOU WIN!", center=(WIDTH//2, HEIGHT//2 - 30), fontsize=64, color=(180,255,180))
    screen.draw.text("Press ENTER to return to menu", center=(WIDTH//2, HEIGHT//2 + 30),
                     fontsize=28, color=(220,220,220))

def _draw_gameover():
    screen.fill((28, 16, 16))
    screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 30), fontsize=64, color=(255,160,160))
    screen.draw.text("Press ENTER to return to menu", center=(WIDTH//2, HEIGHT//2 + 30),
                     fontsize=28, color=(220,220,220))

def _draw_quit():
    screen.fill((10,10,12))
    screen.draw.text("Thanks for playing!", center=(WIDTH//2, HEIGHT//2), fontsize=46, color="white")

def on_mouse_down(pos, button):
    global GAME_STATE, SOUND_ENABLED
    if GAME_STATE == "menu":
        if button != mouse.LEFT: return
        if menu_buttons[0].hovered(pos):
            start_game(); return
        if menu_buttons[1].hovered(pos):
            SOUND_ENABLED = not SOUND_ENABLED
            _update_sound_button_label()
            if SOUND_ENABLED: safe_music_play("bgm")
            else:
                try: music.stop()
                except Exception: pass
            return
        if menu_buttons[2].hovered(pos):
            GAME_STATE = "quit"
            try: music.stop()
            except Exception: pass
            return
    elif GAME_STATE == "playing":
        if button == mouse.LEFT:
            tx, ty = pos
            hero.shoot_towards(tx, ty, bullets)

def on_key_down(key):
    global GAME_STATE
    if key == keys.ESCAPE:
        GAME_STATE = "menu"
        safe_music_play("bgm")
        return
    if GAME_STATE == "playing":
        if key == keys.SPACE:
            mx, my = get_mouse_pos()
            hero.shoot_towards(mx, my, bullets)
    elif GAME_STATE in ("win", "gameover"):
        if key in (keys.RETURN, keys.ENTER, keys.SPACE):
            GAME_STATE = "menu"
            safe_music_play("bgm")

# start menu music if available
safe_music_play("bgm")
