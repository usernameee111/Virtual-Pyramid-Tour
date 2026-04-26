# ---------------------------------------------------------------
# PIXEL DRAW
# ---------------------------------------------------------------
def put_pixel(x, y, color):
    if 0 <= int(x) < WIDTH and 0 <= int(y) < HEIGHT:
        screen.set_at((int(x), int(y)), color)

# ---------------------------------------------------------------
# DDA LINE ALGORITHM
# ---------------------------------------------------------------
def dda_line(x1, y1, x2, y2, color):

    dx = x2 - x1
    dy = y2 - y1

    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        put_pixel(x1, y1, color)
        return

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1

    for _ in range(steps):
        put_pixel(round(x), round(y), color)
        x += x_inc
        y += y_inc

# ---------------------------------------------------------------
# BRESENHAM LINE
# ---------------------------------------------------------------
def bresenham_line(x1, y1, x2, y2, color):

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    err = dx - dy

    while True:

        put_pixel(x1, y1, color)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x1 += sx

        if e2 < dx:
            err += dx
            y1 += sy

# ---------------------------------------------------------------
# MIDPOINT CIRCLE
# ---------------------------------------------------------------
def circle_points(cx, cy, x, y, color):

    pts = [
        (cx+x, cy+y), (cx-x, cy+y),
        (cx+x, cy-y), (cx-x, cy-y),
        (cx+y, cy+x), (cx-y, cy+x),
        (cx+y, cy-x), (cx-y, cy-x)
    ]

    for px, py in pts:
        put_pixel(px, py, color)

def midpoint_circle(cx, cy, r, color):

    x = 0
    y = r
    p = 1 - r

    while x <= y:

        circle_points(cx, cy, x, y, color)

        x += 1

        if p < 0:
            p += 2*x + 1
        else:
            y -= 1
            p += 2*(x-y) + 1

# ---------------------------------------------------------------
# FILLED CIRCLE (for sun / head)
# ---------------------------------------------------------------
def filled_circle(cx, cy, r, color):
    for rr in range(r, 0, -1):
        midpoint_circle(cx, cy, rr, color)

# ---------------------------------------------------------------
# SCANLINE TRIANGLE FILL
# ---------------------------------------------------------------
def scanline_fill_triangle(p1, p2, p3, color):

    pts = sorted([p1,p2,p3], key=lambda p: p[1])

    x1,y1 = pts[0]
    x2,y2 = pts[1]
    x3,y3 = pts[2]

    def interp(y, xa, ya, xb, yb):
        if yb == ya:
            return xa
        return xa + (y-ya)*(xb-xa)/(yb-ya)

    for y in range(int(y1), int(y3)+1):

        if y < y2:
            xa = interp(y,x1,y1,x2,y2)
            xb = interp(y,x1,y1,x3,y3)
        else:
            xa = interp(y,x2,y2,x3,y3)
            xb = interp(y,x1,y1,x3,y3)

        if xa > xb:
            xa, xb = xb, xa

        for x in range(int(xa), int(xb)+1):
            put_pixel(x,y,color)

# ===============================================================
# INTERACTIVE PYRAMID TOUR - FULL MERGED VERSION
# Added Interior Pyramid Scene + Zoom Transition
# ===============================================================

import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(8)

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))

voice_channel = pygame.mixer.Channel(0)
current_sound = None

overview_sound = pygame.mixer.Sound("assest/pyramids.mp3")
overview_played = False

# 👇 هنا تحطي الصور
guide_img = pygame.image.load("assest/guide.png").convert_alpha()
guide_img = pygame.transform.smoothscale(guide_img, (160, 240))
guide_img.set_colorkey((255, 255, 255))  # يشيل الأبيض

khufu_sound = pygame.mixer.Sound("assest/khufu.mp3")
khafre_sound = pygame.mixer.Sound("assest/khafre.mp3")
menkaure_sound = pygame.mixer.Sound("assest/Menkaure.mp3")
menkaure_played = False
# -----------------
# =========================
# AUDIO MANAGER
# =========================

class AudioManager:
    def __init__(self):
        self.channel = pygame.mixer.Channel(0)
        self.sounds = {}
        self.current_key = None

    def load(self, key, path):
        self.sounds[key] = pygame.mixer.Sound(path)

    def play(self, key):
        if key not in self.sounds:
            return

        # ❌ لو الصوت لسه شغال متعيدوش
        if self.channel.get_busy():
            return

        self.channel.play(self.sounds[key])
        self.current_key = key

    def play_once(self, key):
        if self.current_key == key and self.channel.get_busy():
            return
        self.play(key)
        

audio = AudioManager()
audio.load("intro", "assest/intro.mp3")
audio.load("overview", "assest/pyramids.mp3")
audio.load("khufu", "assest/khufu.mp3")
audio.load("khafre", "assest/khafre.mp3")
audio.load("menkaure", "assest/Menkaure.mp3")
audio.load("room", "assest/room.mp3")
audio.load("unlock", "assest/pass.mp3")
audio.load("fail", "assest/fail.mp3")
audio.load("end", "assest/end.mp3")        
#voice
played_audio = set()
current_key = None

def play_sound_once(key, sound):
    global current_key

    # لو نفس الصوت مايتكررش
    if current_key == key:
        return

    # وقف أي صوت شغال
    voice_channel.stop()

    # شغل الجديد
    voice_channel.play(sound)

    current_key = key
    played_audio.add(key)
voice_channel = pygame.mixer.Channel(0)
def play_voice_once(key, sound):
    if key in played_audio:
        return

    voice_channel.stop()
    voice_channel.play(sound)

    played_audio.add(key)

# ---------------------------------------------------------------
# TIMER
# ---------------------------------------------------------------
import time

time_limit = 60  
start_time = None
time_up = False


# ---------------------------------------------------------------
# WINDOW
# ---------------------------------------------------------------

pyramid_cache = {}
sun_cache = None
guide_head_cache = None

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Living Pyramid Tour")

clock = pygame.time.Clock()

# ---------------------------------------------------------------
# FONTS
# ---------------------------------------------------------------
title_font = pygame.font.SysFont("georgia", 44, True)
big_font   = pygame.font.SysFont("arial", 34, True)
mid_font   = pygame.font.SysFont("timesnewroman", 26, True)
small_font = pygame.font.SysFont("arial", 20)

# ---------------------------------------------------------------
# COLORS
# ---------------------------------------------------------------
BLACK=(0,0,0)
WHITE=(255,255,255)
GOLD=(255,215,90)
SAND=(232,202,154)
DARK_SAND=(178,140,92)
BROWN=(148,108,72)
SHADOW=(70,50,25)
GREEN=(45,180,75)
SKY1=(35,55,120)
SKY2=(255,170,90)

# ---------------------------------------------------------------
# STATES
# ---------------------------------------------------------------
scene = 0
# 0 intro / 1 khufu / 2 khafre / 3 menkaure / 4 ending
# 5 interior / 6 zoom transition

fade = 255
frame = 0
zoom = 0
inside_from = 1
unlock_frame = 0

symbols = [
    ("A", "bird"),
    ("R", "eye"),
    ("S", "snake"),
    ("E", "leaf")
]

correct_code = ["A","R","S","E"]

player_input = []

# ---------------------------------------------------------------
# DUST PARTICLES
# ---------------------------------------------------------------
dust = []
for _ in range(80):
    dust.append([
        random.randint(0, WIDTH),
        random.randint(100, 620),
        random.uniform(0.3, 1.0),
        random.uniform(-0.2, 0.2),
        random.uniform(-0.1, 0.1)
    ])

# ---------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------
def reset_fade():
    global fade
    fade = 255

def fade_in():
    global fade
    if fade > 0:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(fade)
        screen.blit(overlay, (0,0))
        fade -= 5

def gradient():
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(SKY1[0]*(1-t) + SKY2[0]*t)
        g = int(SKY1[1]*(1-t) + SKY2[1]*t)
        b = int(SKY1[2]*(1-t) + SKY2[2]*t)
        pygame.draw.line(screen, (r,g,b), (0,y), (WIDTH,y))

def ground():
    pygame.draw.rect(screen, SAND, (0,520,WIDTH,230))

# ---------------------------------------------------------------
# SUN
# ---------------------------------------------------------------
# ===============================================================
# PATCH 2 : استبدل دالة draw_sun القديمة بالكامل
# ===============================================================

def draw_sun():
    global sun_cache

    if sun_cache is None:
        size = 120
        sun_cache = pygame.Surface((size, size), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = sun_cache

        filled_circle(60, 60, 55, GOLD)

        globals()['screen'] = old_screen

    # ⭐ مكان ثابت للشمس
    x = 180
    y = 115

    screen.blit(sun_cache, (x - 60, y - 60))

    return x, y
# ---------------------------------------------------------------
# DUST
# ---------------------------------------------------------------
def draw_dust():
    for p in dust:
        p[0] += p[2]
        p[1] += p[3]
        p[3] += p[4] * 0.03

        if p[0] > WIDTH:
            p[0] = -10
        if p[1] < 80 or p[1] > 650:
            p[1] = random.randint(120, 620)

        alpha = random.randint(70,130)
        surf = pygame.Surface((4,4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255,240,200,alpha), (2,2), 2)
        screen.blit(surf, (p[0], p[1]))

# ---------------------------------------------------------------
# PYRAMID
# ---------------------------------------------------------------
# ===============================================================
# PATCH 4 : استبدل دالة pyramid بالكامل
# ===============================================================

def pyramid(x, by, w, h, color, sunx):

    key = (w,h,color)

    if key not in pyramid_cache:

        surf = pygame.Surface((w+220,h+120), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = surf

        p1 = (0,h)
        p2 = (w,h)
        p3 = (w//2,0)

        scanline_fill_triangle(p1,p2,p3,color)

        bresenham_line(*p1,*p2,BLACK)
        bresenham_line(*p1,*p3,BLACK)
        bresenham_line(*p2,*p3,BLACK)

        for i in range(16):
            yy = h - (h/16)*i
            lx = (w/2)*(i/16)
            rx = w - (w/2)*(i/16)

            dda_line(lx,yy,rx,yy,DARK_SAND)

        globals()['screen'] = old_screen

        pyramid_cache[key] = surf

    # draw cached pyramid
    screen.blit(pyramid_cache[key], (x, by-h))

    # dynamic shadow only
    shadow_len = 90 + (sunx/10)

    pygame.draw.polygon(screen, SHADOW, [
        (x+w, by),
        (x+w+shadow_len, by+35),
        (x+w//2+shadow_len*0.4, by)
    ])
# ===============================================================

def guide(x, ground_y):
    img = guide_img

    # 👣 خطوة يمين وشمال + إحساس مشي
    step = math.sin(frame * 0.1) * 6

    # 🦶 نزول بسيط كأنه بيدوس الأرض
    bounce = abs(math.sin(frame * 0.1)) * 2

    screen.blit(
        img,
        (
            x - img.get_width() // 2 + step,
            ground_y - img.get_height() + bounce
        )
    )
# ---------------------------------------------------------------
# FLAG
# ---------------------------------------------------------------
def flag(x, y):
    pygame.draw.line(screen, BLACK, (x, y), (x, y - 95), 3)

    wave = math.sin(frame * 0.12) * 8

    pygame.draw.polygon(screen, (206,17,38), [
        (x,y-95),(x+58,y-88+wave),(x+58,y-76+wave),(x,y-82)
    ])

    pygame.draw.polygon(screen, WHITE, [
        (x,y-82),(x+58,y-76+wave),(x+58,y-64+wave),(x,y-69)
    ])

    pygame.draw.polygon(screen, BLACK, [
        (x,y-69),(x+58,y-64+wave),(x+58,y-52+wave),(x,y-56)
    ])


# ---------------------------------------------------------------
# BUBBLE
# ---------------------------------------------------------------
def bubble(lines, guide_x, guide_y):
    """
    Professional rectangular speech/info box
    Positioned above-left of guide
    """

    # box size
    box_w = 340
    box_h = 145
    padding = 15

    # place above-left of character head
    x = guide_x - box_w - 260
    y = guide_y - 210
   
    # keep inside screen
    if x < 20:
        x = 20
    if y < 20:
        y = 20

    # translucent surface
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 0))   

    # rounded rectangle
    pygame.draw.rect(panel, (255,245,230,230),
                     (0,0,box_w,box_h),
                     border_radius=8)

    pygame.draw.rect(panel, (60, 40, 20), 
                     (0,0,box_w,box_h), 
                     width=2, border_radius=8)

    screen.blit(panel, (x, y))

    # text centered + padded
    line_y = y + padding + 8

    for line in lines:
        txt = small_font.render(line, True, (20,20,20))
        txt_rect = txt.get_rect(center=(x + box_w//2, line_y + 10))
        screen.blit(txt, txt_rect)
        line_y += 28
# ---------------------------------------------------------------
# BUTTON
# ---------------------------------------------------------------
def button(text, x=None, y=None):
    # 📍 لو مفيش position → يستخدم القديم (fallback)
    if x is None:
        x = WIDTH//2 - 180
    if y is None:
        y = 665

    rect = pygame.Rect(x, y, 360, 50)

    mx, my = pygame.mouse.get_pos()

    hovered = rect.collidepoint(mx, my)

    if hovered:
        glow_color = (255, 240, 180)
        scale = 1.05
    else:
        glow_color = (245, 235, 200)
        scale = 1.0

    new_rect = rect.inflate(rect.width * (scale - 1), rect.height * (scale - 1))

    # جسم الزر
    pygame.draw.rect(screen, glow_color, new_rect, border_radius=12)
    pygame.draw.rect(screen, (120, 90, 50), new_rect, 3, border_radius=12)

 
    arrow_move = 0  # ثابت
    arrow = mid_font.render("→", True, (120, 90, 50))
    screen.blit(arrow, (new_rect.right - 40, new_rect.centery - 15))

    # النص
    txt = mid_font.render(text, True, (40, 30, 20))
    screen.blit(txt, txt.get_rect(center=new_rect.center))
# ---------------------------------------------------------------
# WORLD
# ---------------------------------------------------------------
def base_world():
    gradient()
    sunx, suny = draw_sun()
    ground()
    draw_dust()
    flag(1100, 540)
    return sunx

# ---------------------------------------------------------------
# EXTERIOR SCENES
# ---------------------------------------------------------------
voice_channel = pygame.mixer.Channel(0)
played_audio = set()

def restart_game():
    global scene, khufu_played, khafre_played, menkaure_played
    global overview_played, current_scene_sound

    voice_channel.stop()

    played_audio.clear()
    current_scene_sound = None

    khufu_played = False
    khafre_played = False
    menkaure_played = False
    overview_played = False

    scene = 0
def play_sound_once(key, sound):
    global current_scene_sound

    if current_scene_sound == key and voice_channel.get_busy():
        return

    voice_channel.stop()
    voice_channel.play(sound)

    current_scene_sound = key
    played_audio.add(key)
intro_sound = pygame.mixer.Sound("assest/intro.mp3")
def intro():
    base_world()
    

    if "intro" not in played_audio:
        audio.play_once("intro")
    # 🔊 تشغيل الصوت مرة واحدة بشكل صحيح
    audio.play_once("intro")

    panel_rect = pygame.Rect(250, 180, 700, 300)
    pygame.draw.rect(screen, (245, 220, 170), panel_rect, border_radius=20)

    DARK_BROWN = (60, 40, 20)
    pygame.draw.rect(screen, DARK_BROWN, panel_rect, 3, border_radius=20)

    title_surf = title_font.render("Welcome to the Giza Plateau", True, DARK_BROWN)
    title_rect = title_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 70))
    screen.blit(title_surf, title_rect)

    GOLD_TITLE = (218, 165, 32)
    sub_surf = mid_font.render("'A Living Journey Through Ancient Egypt'", True, GOLD_TITLE)
    sub_rect = sub_surf.get_rect(center=(panel_rect.centerx, panel_rect.top + 160))
    screen.blit(sub_surf, sub_rect)

    part1_surf = mid_font.render("Press '", True, DARK_BROWN)
    space_surf = mid_font.render("SPACE", True, (255, 0, 0))
    part2_surf = mid_font.render("' to Begin your journey", True, DARK_BROWN)

    total_width = part1_surf.get_width() + space_surf.get_width() + part2_surf.get_width()
    start_x = panel_rect.centerx - (total_width // 2)
    y_position = panel_rect.top + 230

    screen.blit(part1_surf, (start_x, y_position))
    screen.blit(space_surf, (start_x + part1_surf.get_width(), y_position))
    screen.blit(part2_surf, (start_x + part1_surf.get_width() + space_surf.get_width(), y_position))
overview_sound = pygame.mixer.Sound("assest/pyramids.mp3")
overview_played = False
def pyramids_overview():
    global overview_played

    if not overview_played:
      play_sound_once("overview", overview_sound)
      overview_played = True
    sunx = base_world()
    pyramid(450, 540, 300, 240, (214,182,120), sunx)

    pyramid(200, 540, 240, 190, (205,175,118), sunx)

    pyramid(800, 540, 180, 140, (190,150,100), sunx)

    screen.blit(big_font.render("Giza Pyramids", True, WHITE), (495, 40))

    button("Press RIGHT → Go to Khufu")  
voice_channel = pygame.mixer.Channel(0)
current_scene_sound = None
def play_sound(key, sound):
    global current_scene_sound

    if current_scene_sound == key and voice_channel.get_busy():
        return

    voice_channel.stop()
    voice_channel.play(sound)

    current_scene_sound = key
  
def khufu():
    sunx = base_world()

    audio.play_once("khufu")

    pyramid(250, 540, 450, 350, (214,182,120), sunx)

    gx = int(WIDTH * 0.82)
    gy = 540
    guide(gx, gy)

    bubble([
        "Khufu Pyramid",
        "Originally 146.6m tall",
        "Built with 2 million blocks",
        "Oldest Great Pyramid"
    ], gx + 200, gy - 140)

    screen.blit(big_font.render("Scene 1 : Khufu", True, WHITE), (440,40))

    button("RIGHT ARROW → Next")
def khafre():
    sunx = base_world()

    play_sound_once("khafre", khafre_sound)

    pyramid(330,540,390,310,(205,175,118), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble([
        "Khafre Pyramid",
        "Built on higher ground.",
        "Still has casing stones.",
        "Connected to Sphinx."
    ], gx + 200, gy - 170)

    screen.blit(big_font.render("Scene 2 : Khafre", True, WHITE), (440,40))

    button("RIGHT ARROW → Next")
# ---------------------------------------------------------------
# PUZZLE STATE
# ---------------------------------------------------------------
puzzle = [1,2,3,
          4,5,6,
          7,8,0]  # 0 = empty

import random
random.shuffle(puzzle)

tile_size = 80
puzzle_x = 460
puzzle_y = 200

puzzle_solved = False


def draw_symbols():
    for i, (letter, shape) in enumerate(symbols):

        x = puzzle_x + i * (tile_size + 20)
        y = puzzle_y

        pygame.draw.rect(screen, (230,200,150), (x,y,tile_size,tile_size), border_radius=10)
        pygame.draw.rect(screen, (60,40,20), (x,y,tile_size,tile_size), 2, border_radius=10)

        # رسم بسيط للرموز (بدون صور)
        if shape == "bird":
            pygame.draw.circle(screen, BLACK, (x+40,y+40), 15)

        elif shape == "eye":
            pygame.draw.ellipse(screen, BLACK, (x+20,y+30,40,20), 2)

        elif shape == "snake":
            pygame.draw.line(screen, BLACK, (x+20,y+60),(x+60,y+20),3)

        elif shape == "leaf":
            pygame.draw.polygon(screen, BLACK, [(x+40,y+20),(x+60,y+60),(x+20,y+60)])


def click_symbol(index):
    global player_input, puzzle_solved, scene

    player_input.append(symbols[index][0])

    # لو طول الإدخال أكبر من المطلوب → reset
    if len(player_input) > len(correct_code):
        player_input = []

    # تحقق
    if player_input == correct_code:
        puzzle_solved = True
        scene = 7


def draw_timer():
    global time_up

    if start_time is None:
        return

    elapsed = int(time.time() - start_time)
    remaining = max(0, time_limit - elapsed)

    # لو الوقت خلص
    if remaining == 0:
        time_up = True

    # لون حسب الوقت
    color = (255,255,255)
    if remaining <= 10:
        color = (255,50,50)  # أحمر خطر

    txt = mid_font.render(f"Time: {remaining}s", True, color)
    screen.blit(txt, (50, 40))

################################################################
def menkaure():
    sunx = base_world()

    play_sound_once("menkaure", menkaure_sound)

    pyramid(430,540,270,220,(190,150,100), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble([
        "Menkaure Pyramid",
        "Smallest of the three.",
        "Granite lower casing.",
        "Elegant design."
    ], gx + 200, gy - 140)

    screen.blit(big_font.render("Scene 3 : Menkaure", True, WHITE), (410,40))

    button("RIGHT ARROW → Finish")

def ending():
    base_world()

    play_sound_once("end", pygame.mixer.Sound("assest/end.mp3"))

    screen.blit(title_font.render("Thank You For Visiting Egypt", True, WHITE),
                (250, 300))

    screen.blit(big_font.render("History Still Breathes Here", True, GOLD),
                (350, 380))

    button("Press R to Restart")
# INTERIOR FUNCTIONS
# ---------------------------------------------------------------
def torch_flame(x,y):
    flick = random.randint(-5,5)
    pygame.draw.rect(screen, BROWN, (x-3,y,6,35))
    pygame.draw.circle(screen,(255,180,50),(x,y+flick),14)
    pygame.draw.circle(screen,(255,120,30),(x,y+flick+2),10)

def interior_scene():
    txt = mid_font.render("Your Code: " + "".join(player_input), True, WHITE)
    screen.blit(txt, (450, 180))
    screen.fill((28,22,18))
    draw_timer()
    # -----------------------------------------------------------
    # SIDE WALLS
    # -----------------------------------------------------------
    pygame.draw.polygon(screen,(70,60,50),
        [(0,0),(260,220),(260,750),(0,750)])

    pygame.draw.polygon(screen,(70,60,50),
        [(1200,0),(940,220),(940,750),(1200,750)])

    # center wall / chamber
    pygame.draw.rect(screen,(55,48,40),(260,0,680,750))

    # -----------------------------------------------------------
    # PERSPECTIVE FLOOR PATH
    # -----------------------------------------------------------
    pygame.draw.polygon(screen,(95,80,65),
        [(400,750),(800,750),(700,260),(500,260)])

    # -----------------------------------------------------------
    # TORCHES
    # -----------------------------------------------------------
    torch_flame(150,250)
    torch_flame(1050,250)

    # light glow
    glow = pygame.Surface((1200,750), pygame.SRCALPHA)

    pygame.draw.circle(glow,(255,140,20,60),(150,250),180)
    pygame.draw.circle(glow,(255,140,20,60),(1050,250),180)

    screen.blit(glow,(0,0))

    # -----------------------------------------------------------
    # SARCOPHAGUS
    # -----------------------------------------------------------
    pygame.draw.rect(screen,(120,120,120),(500,520,220,70))
    pygame.draw.rect(screen,(90,90,90),(530,490,160,35))
    pygame.draw.rect(screen,(40,40,40),(500,520,220,70),2)

    # -----------------------------------------------------------
    # PUZZLE (يتترسم بعد الخلفية)
    # -----------------------------------------------------------
    draw_symbols()
    if not puzzle_solved:
        txt = mid_font.render("Solve the puzzle to unlock the chamber", True, BROWN)
        screen.blit(txt, (380, 150))
    else:
        txt = mid_font.render("Chamber Unlocked!", True, (0,255,120))
        screen.blit(txt, (450, 150))

    if time_up:
    
       overlay = pygame.Surface((WIDTH, HEIGHT))
       overlay.fill((0,0,0))
       overlay.set_alpha(180)
       screen.blit(overlay, (0,0))

       play_voice_once("fail", "assest/fail.mp3") 

       # ===== نصوص مرتبة في المنتصف =====

       title = big_font.render("You Failed!", True, (255,50,50))
       hint1 = mid_font.render("Press R to Restart", True, (255,255,255))
       hint2 = mid_font.render("Press ESC to Exit", True, (255,255,255))

       # حساب التمركز
       title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
       hint1_rect = hint1.get_rect(center=(WIDTH//2, HEIGHT//2))
       hint2_rect = hint2.get_rect(center=(WIDTH//2, HEIGHT//2 + 40))

       # رسم
       screen.blit(title, title_rect)
       screen.blit(hint1, hint1_rect)
       screen.blit(hint2, hint2_rect)
    # -----------------------------------------------------------
    # GUIDE POSITION (85%,90%)
    # -----------------------------------------------------------
    gx = int(WIDTH * 0.85)
    gy = int(HEIGHT * 0.90)

    guide(gx, gy)

    # -----------------------------------------------------------
    # INFO BOX ABOVE GUIDE
    # -----------------------------------------------------------
    bubble([
        "King's Chamber",
        "This room held the royal",
        "stone sarcophagus.",
        "Burial rituals occurred here."
    ], gx, gy)

    audio.play_once("room")
    # -----------------------------------------------------------
    # TITLE
    # -----------------------------------------------------------
    title = big_font.render("Inside The Pyramid", True, BROWN)
    screen.blit(title, (420,30))

    # -----------------------------------------------------------
    # RETURN BUTTON
    # -----------------------------------------------------------
    if puzzle_solved:
        button("ESC → Return")
    else:
        button("Solve Puzzle First!")


def unlock_scene():
    global unlock_frame, scene

    screen.fill((10,10,10))

    # اهتزاز خفيف (Shake effect)
    shake_x = random.randint(-3,3)
    shake_y = random.randint(-3,3)

    # ضوء بيكبر تدريجياً
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    radius = min(10 + unlock_frame*6, 500)

    pygame.draw.circle(glow, (255,200,100,120), (WIDTH//2, HEIGHT//2), radius)
    screen.blit(glow, (0,0))

    # نص فتح الغرفة
    txt = big_font.render("Ancient Chamber Unlocked!", True, (255,215,90))
    screen.blit(txt, (WIDTH//2 - 180 + shake_x, HEIGHT//2 - 50 + shake_y))

    # صوت مرة واحدة
    play_voice_once("unlock", "assest/pass.mp3")

    unlock_frame += 1

    # بعد ثواني ننتقل تلقائي
    if unlock_frame > 80:
        scene = 8   # يرجع داخل الغرفة (أو أي reward scene)
        unlock_frame = 0

# ---------------------------------------------------------------
# TREASURE SCENE (Scene 8)
# ---------------------------------------------------------------
def treasure_scene():

    screen.fill((10, 8, 5))

    # -----------------------------
    # جدران مظلمة
    # -----------------------------
    pygame.draw.rect(screen, (40,35,25), (0,0,WIDTH,HEIGHT))

    # -----------------------------
    # أرضية
    # -----------------------------
    pygame.draw.rect(screen, (70,55,40), (0,500,WIDTH,250))

    # -----------------------------
    # توهج ذهبي
    # -----------------------------
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for i in range(5):
        pygame.draw.circle(
            glow,
            (255, 215, 90, 40),
            (WIDTH//2, 480),
            120 + i*40
        )

    screen.blit(glow, (0,0))

    # -----------------------------
    # صندوق الكنز
    # -----------------------------
    chest_x = WIDTH//2 - 120
    chest_y = 430

    # جسم الصندوق
    pygame.draw.rect(screen, (120,85,40), (chest_x, chest_y, 240, 120))
    pygame.draw.rect(screen, (80,60,30), (chest_x, chest_y, 240, 120), 3)

    # الغطاء (مفتوح)
    pygame.draw.rect(screen, (140,100,50), (chest_x, chest_y-60, 240, 60))
    pygame.draw.rect(screen, (80,60,30), (chest_x, chest_y-60, 240, 60), 3)

    # -----------------------------
    # الذهب (جوا الصندوق)
    # -----------------------------
    for i in range(20):
        gx = chest_x + 20 + (i%5)*40
        gy = chest_y + 20 + (i//5)*20
        pygame.draw.circle(screen, (255,215,0), (gx,gy), 8)

    # -----------------------------
    # جواهر
    # -----------------------------
    pygame.draw.circle(screen, (0,255,200), (chest_x+60, chest_y+40), 10)
    pygame.draw.circle(screen, (255,0,100), (chest_x+160, chest_y+60), 10)
    pygame.draw.circle(screen, (100,200,255), (chest_x+120, chest_y+30), 10)

    # -----------------------------
    # بريق متحرك ✨
    # -----------------------------
    for _ in range(15):
        x = random.randint(chest_x, chest_x+240)
        y = random.randint(chest_y-80, chest_y)
        pygame.draw.circle(screen, (255,255,200), (x,y), 2)

    # -----------------------------
    # النصوص
    # -----------------------------
    title = big_font.render("Treasure Discovered!", True, GOLD)
    screen.blit(title, (WIDTH//2 - 180, 120))

    msg = mid_font.render("You unlocked the secrets of the pyramid", True, WHITE)
    screen.blit(msg, (WIDTH//2 - 220, 180))

    # -----------------------------
    # المرشد
    # -----------------------------
    gx = int(WIDTH * 0.85)
    gy = int(HEIGHT * 0.90)

    guide(gx, gy)

    bubble([
        "Incredible!",
        "You found the hidden treasure!",
        "Ancient riches are yours."
    ], gx, gy)

    # -----------------------------
    # زر الرجوع
    # -----------------------------
    button("Press R → Restart | ESC → Exit")  
# ---------------------------------------------------------------
# ZOOM TRANSITION
# ---------------------------------------------------------------
# ===============================================================
# 6) zoom faster
# استبدل zoom_transition بالكامل
# ===============================================================

def zoom_transition():
    global zoom, scene, start_time, time_up

    draw_sun()

    # استخدم الهرم الأساسي من الكاش
    key = (450,350,(214,182,120))

    if key not in pyramid_cache:
        pyramid(250,540,450,350,(214,182,120),300)

    base = pyramid_cache[key]

    scale = 1 + zoom * 0.08

    new_w = int(base.get_width() * scale)
    new_h = int(base.get_height() * scale)

    img = pygame.transform.smoothscale(base, (new_w, new_h))

    px = WIDTH//2 - new_w//2
    py = HEIGHT//2 - new_h//2 + 120

    screen.blit(img, (px, py))

    fade_layer = pygame.Surface((WIDTH, HEIGHT))
    fade_layer.fill((255,255,255))
    fade_layer.set_alpha(min(zoom*7, 220))
    screen.blit(fade_layer,(0,0))

    zoom += 2

    if zoom >= 18:
        zoom = 0
        scene = 5
        start_time = time.time()   # ⏱️ start timer
        time_up = False
        reset_fade()
        
# ---------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------
running = True

while running:
    clock.tick(60)
    frame += 1

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if scene == 5 and not puzzle_solved:
               mx, my = pygame.mouse.get_pos()

               for i in range(len(symbols)):
                   x = puzzle_x + i * (tile_size + 20)
                   y = puzzle_y

                   if x <= mx <= x+tile_size and y <= my <= y+tile_size:
                      click_symbol(i)

        if event.type == pygame.KEYDOWN:

            if scene == 0 and event.key == pygame.K_SPACE:
                scene = 0.5
                reset_fade()

            elif scene == 0.5 and event.key == pygame.K_RIGHT:
                overview_sound.stop()
                overview_played = False
                scene = 1
                reset_fade()

            elif scene in [1,2,3] and event.key == pygame.K_RIGHT:
                scene += 1
                reset_fade()

            elif scene == 4 and event.key == pygame.K_r:
                scene = 0
                reset_fade()

            elif scene == 5 and event.key == pygame.K_ESCAPE:
                scene = inside_from
                reset_fade()
            elif scene == 8 and event.key == pygame.K_r:
                scene = 0
                reset_fade()
            # ⭐ هنا تضيف الكود بتاع الريست بعد الخسارة
            if event.key == pygame.K_r:
               restart_game()
               reset_fade()
               puzzle_solved = False
               time_up = False
               puzzle[:] = [1,2,3,4,5,6,7,8,0]
               random.shuffle(puzzle)
               start_time = time.time()

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx,my = pygame.mouse.get_pos()

            if scene in [1,2,3]:
                if 220 <= mx <= 760 and 180 <= my <= 540:
                    inside_from = scene
                    scene = 6
                    zoom = 0
                    reset_fade()
    # -----------------------------------------------------------
    # DRAW
    # -----------------------------------------------------------
    if scene == 0:
        intro()
    elif scene == 0.5:
        pyramids_overview()
        if not overview_played:
           overview_sound.play()
           overview_played = True
    elif scene == 1:
        khufu()
    elif scene == 2:
        khafre()
    elif scene == 3:
        menkaure()
    elif scene == 4:
        ending()
    elif scene == 5:
        interior_scene()
    elif scene == 6:
        zoom_transition()
    elif scene == 7:
        unlock_scene()
    elif scene == 8:
        treasure_scene()

    fade_in()
    pygame.display.update()

pygame.quit()
sys.exit()
