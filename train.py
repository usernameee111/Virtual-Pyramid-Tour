# ---------------------------------------------------------------
# 1. Imports
# ---------------------------------------------------------------
import pygame
import sys
import math
import random
# ---------------------------------------------------------------
# 2. Set ups & Constants
# ---------------------------------------------------------------
pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(8)

WIDTH, HEIGHT = 1200, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Living Pyramid Tour")
clock = pygame.time.Clock()
# ---------------------------------------------------------------
# 3. Constants
# ---------------------------------------------------------------
# Colors
BLACK=(0,0,0)
WHITE=(255,255,255)
GOLD = (255, 200, 90)
BROWN=(148,108,72)
GREEN=(45,180,75)
CARD_COLOR = (40, 30, 20)   
CARD_BORDER = (200, 170, 110)
SUB_COLOR = (90, 70, 40)
SAND = (210, 170, 110)
DARK_SAND = (150, 110, 70)
SHADOW = (35, 20, 10)
SKY1 = (15, 25, 60)
SKY2 = (255, 140, 60)
MAIN_PYRAMID_COLOR = (185, 140, 85)
LEFT_FACE_COLOR = (125, 95, 60)
RIGHT_FACE_COLOR = (220, 175, 110)
TEXT_LIGHT = (240, 230, 210)
ACCENT = (255, 180, 80)
# FONTS
title_font = pygame.font.SysFont("timesnewroman", 48, True)
mid_font   = pygame.font.SysFont("georgia", 26)
big_font   = pygame.font.SysFont("arial", 34, True)
small_font = pygame.font.SysFont("arial", 20)
# images
guide_img = pygame.image.load("assest/guide.png").convert_alpha()
guide_img = pygame.transform.smoothscale(guide_img, (160, 240))
guide_img.set_colorkey((255, 255, 255))  
end_bg = pygame.image.load("assest/images/closing.png").convert()
end_bg = pygame.transform.scale(end_bg, (WIDTH, HEIGHT))
intro_bg = pygame.image.load("assest/images/first_background.png")
# ---------------------------------------------------------------
# 4. Audio maneger
# ---------------------------------------------------------------
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

        if self.current_key == key:
            return

        self.channel.stop()
        self.channel.play(self.sounds[key])
        self.current_key = key

    def reset(self):
        pygame.mixer.stop()
        self.channel.stop()      
        self.current_key = None  
        
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
audio.load("roomm", "assest/roomm.mp3")
audio.load("unlock", "assest/pass.mp3")
audio.load("fail", "assest/fail.mp3")
audio.load("end", "assest/end.mp3")        

overview_played = False
# ---------------------------------------------------------------
# 5. State & Global Variables
# ---------------------------------------------------------------
scene = 0
fade = 255
frame = 0
zoom = 0
inside_from = 1
unlock_frame = 0
tile_size = 80
zoom_level = 1.0
MIN_ZOOM = 0.6
MAX_ZOOM = 5.0

symbols = [
    ("A", "ankh"),  
    ("N", "water"), 
    ("K", "basket"),  
    ("H", "twist")  
]
correct_answer = 3 
puzzle_solved = False
puzzle_x = 460
puzzle_y = 200

pyramid_cache = {}
sun_cache = None
guide_head_cache = None

room_sound_played = False

show_hint = True

played_audio = set()

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
# 6. CORE GRAPHICS ALGORITHMS
# ---------------------------------------------------------------
def put_pixel(x, y, color):
    if 0 <= int(x) < WIDTH and 0 <= int(y) < HEIGHT:
        screen.set_at((int(x), int(y)), color)

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

def filled_circle(cx, cy, r, color):
    for rr in range(r, 0, -1):
        midpoint_circle(cx, cy, rr, color)

def filled_circle_on_surface(surface, cx, cy, r, color):
    for rr in range(r, 0, -1):
        midpoint_circle_on_surface(surface, cx, cy, rr, color)

def midpoint_circle_on_surface(surface, cx, cy, r, color):
    x = 0
    y = r
    p = 1 - r

    while x <= y:
        pts = [
            (cx+x, cy+y), (cx-x, cy+y),
            (cx+x, cy-y), (cx-x, cy-y),
            (cx+y, cy+x), (cx-y, cy+x),
            (cx+y, cy-x), (cx-y, cy-x)
        ]

        for px, py in pts:
            if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
                surface.set_at((px, py), color)

        x += 1
        if p < 0:
            p += 2*x + 1
        else:
            y -= 1
            p += 2*(x-y) + 1

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

def transform_point(x, y, tx=0, ty=0, sx=1, sy=1):
    # Scaling
    x = x * sx
    y = y * sy

    # Translation
    x = x + tx
    y = y + ty

    return (int(x), int(y))
# ---------------------------------------------------------------
# 7. UI & HELPERS Functions
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
        t = (y / HEIGHT) ** 1.3
        r = int(SKY1[0]*(1-t) + SKY2[0]*t)
        g = int(SKY1[1]*(1-t) + SKY2[1]*t)
        b = int(SKY1[2]*(1-t) + SKY2[2]*t)
        pygame.draw.line(screen, (r,g,b), (0,y), (WIDTH,y))

def ground():
    pygame.draw.rect(screen, SAND, (0,520,WIDTH,230))

def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "

    if current_line:
        lines.append(current_line)

    return lines

def bubble(lines, guide_x, guide_y):
    box_w = 600
    box_h = 200
    padding = 20
    x = guide_x - box_w // 2 -100
    y = guide_y - box_h - 250
    if x < 20:
        x = 20
    if y < 20:
        y = 20
    shadow = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80),
                     (0, 0, box_w, box_h),
                     border_radius=12)
    screen.blit(shadow, (x + 5, y + 5))
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)

    pygame.draw.rect(panel, (30, 20, 10, 230),
                     (0, 0, box_w, box_h),
                     border_radius=12)

    pygame.draw.rect(panel, (80, 55, 30),
                     (0, 0, box_w, box_h),
                     2, border_radius=12)

    screen.blit(panel, (x, y))

    max_text_width = box_w - padding * 2
    max_lines = (box_h - padding * 2) // 24

    wrapped_lines = []

    for line in lines:
        clean_line = line.replace("\n", " ").strip()
        wrapped_lines.extend(
            wrap_text(clean_line, small_font, max_text_width)
        )

    wrapped_lines = wrapped_lines[:max_lines]

    line_y = y + padding

    for line in wrapped_lines:
        txt = small_font.render(line, True, (240, 220, 180))
        screen.blit(txt, (x + padding, line_y))
        line_y += 24

def button(text, align="right"):
    box_w = 360
    box_h = 50
    y = 660

    if align == "right":
        x = WIDTH - box_w - 40  
    else:
        x = 40            

    rect = pygame.Rect(x, y, box_w, box_h)

    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (210,170,110,220), (0,0,box_w,box_h), border_radius=12)
    screen.blit(panel, (x,y))
    pygame.draw.rect(screen, (120, 80, 40), rect, 3, border_radius=12)

    txt = mid_font.render(text, True, (40,30,20))
    screen.blit(txt, txt.get_rect(center=rect.center))

def hint_box(text, x, y):
    box_w = 320
    box_h = 70

    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)

    pygame.draw.rect(panel, (20, 10, 5, 210),
                     (0, 0, box_w, box_h),
                     border_radius=12)

    pygame.draw.rect(panel, (255, 200, 120),
                     (0, 0, box_w, box_h),
                     2, border_radius=12)

    screen.blit(panel, (x, y))

    txt = small_font.render(text, True, (255, 230, 180))
    txt_rect = txt.get_rect(center=(x + box_w//2, y + box_h//2))
    screen.blit(txt, txt_rect)
# ------------------------------------------
# 11. Environment
# ------------------------------------------
def base_world():
    gradient()
    sunx, suny = draw_sun()
    ground()
    draw_dust()
    flag(1100, 540)
    return sunx

def scale_background(img, screen_w, screen_h):
    img_w, img_h = img.get_size()
    scale = min(screen_w / img_w, screen_h / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    return pygame.transform.smoothscale(img, (new_w, new_h))

intro_bg = scale_background(intro_bg, WIDTH, HEIGHT)

def bg_intro_():
    bg_x = (WIDTH - intro_bg.get_width()) // 2
    bg_y = (HEIGHT - intro_bg.get_height()) // 2
    screen.blit(intro_bg, (bg_x, bg_y))    
# --------------------------------------------------------------
# Intro Scene
# ---------------------------------------------------------------
def intro():
    bg_intro_()

    audio.play_once("intro")
    panel_x = 250
    panel_y = 180
    panel_w = 700
    panel_h = 300

    center_x = panel_x + panel_w // 2
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((25, 15, 5, 160))
    screen.blit(panel, (panel_x, panel_y))

    pygame.draw.rect(screen, (255,220,150),
                     (panel_x, panel_y, panel_w, panel_h),
                     2, border_radius=20)

    title_text = "Journey Into Ancient Egypt"

    shadow = title_font.render(title_text, True, (0,0,0))
    shadow_rect = shadow.get_rect(center=(center_x + 2, panel_y + 70 + 2))
    screen.blit(shadow, shadow_rect)

    glow = title_font.render(title_text, True, ACCENT)
    glow_rect = glow.get_rect(center=(center_x - 2, panel_y + 70 - 2))
    screen.blit(glow, glow_rect)

    title = title_font.render(title_text, True, GOLD)
    title_rect = title.get_rect(center=(center_x, panel_y + 70))
    screen.blit(title, title_rect)

    sub = mid_font.render(
        "Where Legends Were Carved in Stone",
        True,
        (220,200,150)
    )

    sub_rect = sub.get_rect(center=(center_x, panel_y + 140))
    screen.blit(sub, sub_rect)

    part1 = mid_font.render("Press ", True, TEXT_LIGHT)
    space = mid_font.render("SPACE", True, ACCENT)
    part2 = mid_font.render(" to Begin Your Explroation", True, TEXT_LIGHT)

    total_w = part1.get_width() + space.get_width() + part2.get_width()
    start_x = center_x - total_w // 2

    y = panel_y + 210

    screen.blit(part1, (start_x, y))
    screen.blit(space, (start_x + part1.get_width(), y))
    screen.blit(part2, (start_x + part1.get_width() + space.get_width(), y))
# --------------------------------------
# 8. Draw Sun & Dust
# -----------------------------------
# Sun
def draw_sun():
    global sun_cache

    if sun_cache is None:
        size = 120
        sun_cache = pygame.Surface((size,size), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = sun_cache

        filled_circle(60,60,55,GOLD)

        globals()['screen'] = old_screen

    x = 180
    y = 115

    screen.blit(sun_cache, (x - 60, y - 60))

    return x, y

# Dust
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
        filled_circle_on_surface(surf, 2, 2, 2, (255,240,200,alpha))
        screen.blit(surf, (p[0], p[1]))
# --------------------------------------
# 9. guide
# --------------------------------------
def guide(x, ground_y):
    img = guide_img
    step = math.sin(frame * 0.1) * 6
    bounce = abs(math.sin(frame * 0.1)) * 2

    screen.blit(
        img,
        (
            x - img.get_width() // 2 + step,
            ground_y - img.get_height() + bounce
        )
    )
# --------------------------------------
# 10. flag
# --------------------------------------
def flag(x, y):
    bresenham_line(x, y, x, y - 95, BLACK)

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
# --------------------------------------------------------------
# Pyramids
# ---------------------------------------------------------------
def get_pyramid_points(w, h):
    left  = (0, h)
    right = (w, h)
    top   = (w * 0.45, 0)
    ridge = (w * 0.32, h)

    return left, right, top, ridge

def transform_pyramid(points, tx, ty, sx, sy):
    transformed = []
    for (x, y) in points:
        transformed.append(transform_point(x, y, tx, ty, sx, sy))
    return transformed

def draw_transformed_pyramid(x, by, w, h, color, sunx):

    key = (w, h, color)

    if key not in pyramid_cache:

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = surf

        base_w, base_h = 300, 240

        sx = w / base_w
        sy = h / base_h

        left  = (0, base_h)
        right = (base_w, base_h)
        top   = (base_w * 0.45, 0)
        ridge = (base_w * 0.32, base_h)

        def T(p):
            return (
                int(p[0] * sx),
                int(p[1] * sy)
            )

        left  = T(left)
        right = T(right)
        top   = T(top)
        ridge = T(ridge)
        scanline_fill_triangle(left, ridge, top, LEFT_FACE_COLOR)
        scanline_fill_triangle(ridge, right, top, RIGHT_FACE_COLOR)
        edge_color = (60,40,20)

        bresenham_line(*left, *top, edge_color)
        bresenham_line(*top, *right, edge_color)
        bresenham_line(*left, *right, edge_color)
        layers = 10

        for i in range(1, layers):

            y = h - (h/layers)*i
            ratio = y / h

            x_left = int(left[0] + (top[0] - left[0]) * (1 - ratio))
            x_right = int(right[0] + (top[0] - right[0]) * (1 - ratio))
            x_ridge = int(ridge[0] + (top[0] - ridge[0]) * (1 - ratio))

            dda_line(x_left, int(y), x_ridge, int(y), (150,120,80))
            dda_line(x_ridge, int(y), x_right, int(y), (170,135,90))

        globals()['screen'] = old_screen
        pyramid_cache[key] = surf
    screen.blit(pyramid_cache[key], (x, by - h))
    shadow_len = 90 + (sunx/10)

    pygame.draw.polygon(screen, SHADOW, [
        (x+w, by),
        (x+w+shadow_len, by+35),
        (x+w//2+shadow_len*0.4, by)
    ])

def pyramid(x, by, w, h, color, sunx):

    key = (w, h, color)
    if key not in pyramid_cache:

        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = surf

        left  = (0, h)
        right = (w, h)

        top   = (int(w * 0.45), 0)   
        ridge = int(w * 0.32)       

        base_mid = (ridge, h)
        left_color = LEFT_FACE_COLOR


        right_color = RIGHT_FACE_COLOR
        scanline_fill_triangle(left, base_mid, top, left_color)
        scanline_fill_triangle(base_mid, right, top, right_color)
        edge_color = (60,40,20)

        bresenham_line(*left, *top, edge_color)
        bresenham_line(*top, *right, edge_color)
        bresenham_line(*left, *right, edge_color)

        layers = 10

        for i in range(1, layers):

            y = h - (h/layers)*i
            ratio = y / h
            x_left = int(left[0] + (top[0] - left[0]) * (1 - ratio))
            x_right = int(right[0] + (top[0] - right[0]) * (1 - ratio))

            x_ridge = int(base_mid[0] + (top[0] - base_mid[0]) * (1 - ratio))

            dda_line(x_left, int(y), x_ridge, int(y), (150,120,80))

            dda_line(x_ridge, int(y), x_right, int(y), (170,135,90))
        globals()['screen'] = old_screen
        pyramid_cache[key] = surf

    screen.blit(pyramid_cache[key], (x, by-h))

    shadow_len = 90 + (sunx/10)

    pygame.draw.polygon(screen, SHADOW, [
        (x+w, by),
        (x+w+shadow_len, by+35),
        (x+w//2+shadow_len*0.4, by)
    ])





def pyramids_overview():
    global overview_played

    if not overview_played:
       audio.play_once("overview")
    sunx = base_world()

    draw_transformed_pyramid(450, 540, 300, 240, MAIN_PYRAMID_COLOR, sunx)
    draw_transformed_pyramid(200, 540, 240, 190, MAIN_PYRAMID_COLOR, sunx)
    draw_transformed_pyramid(800, 540, 180, 140, MAIN_PYRAMID_COLOR, sunx)

    screen.blit(big_font.render("Giza Pyramids", True, (255,220,140)), (495, 40))

    button("Press RIGHT Arrow to move",'right')  
# -----------------------------------------------------
# Khufu
# -----------------------------------------------------
def khufu():
    sunx = base_world()

    audio.play_once("khufu")

    pyramid(250, 540, 450, 350, (214,182,120), sunx)

    gx = int(WIDTH * 0.82)
    gy = 540
    guide(gx, gy)

    bubble([
        '''The Great Pyramid of Khufu, the only surviving Wonder of the Ancient World. Its built from over 2.3 million stone blocks, some weighing up to 15 tons! For nearly 4,000 years, it was the tallest structure on Earth. Most impressively, its base is perfectly aligned with the four cardinal points with incredible precision. Its not just a tomb; its a timeless miracle of Egyptian engineering that still baffles the world today'''], gx, gy)

    screen.blit(big_font.render("Khufu", True, (255,220,140)), (440,40))

    button("Press RIGHT Arrow to move",'right')
    if show_hint:
            hint_box("To enter the pyramid Click it", 50, HEIGHT - 120)
# -----------------------------------------------------
# khafre
# -----------------------------------------------------
def khafre():
    sunx = base_world()

    audio.play_once("khafre")
    pyramid(330,540,390,310,(205,175,118), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble(['''Now, let’s look at the Pyramid of Khafre, the second-largest pyramid in Giza.You can easily recognize it by the original casing stones still clinging to its peak, giving us a glimpse of how polished and shining these pyramids once looked. Although it appears taller than Khufu’s, it’s actually slightly shorter but built on higher ground. Right next to it stands its legendary guardian, the Great Sphinx, carved from a single ridge of limestone. It remains a magnificent symbol of power and royal majesty."'''
    ], gx, gy)

    screen.blit(big_font.render("Khafre", True, (255,220,140)), (440,40))

    button("Press RIGHT Arrow to move",'right')
# -----------------------------------------------------
# menkaure
# -----------------------------------------------------
def menkaure():
    sunx = base_world()

    audio.play_once("menkaure")

    pyramid(430,540,270,220,(190,150,100), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble(['''Lastly, we reach the Pyramid of Menkaure, the smallest of the three main pyramids,but uniquely beautiful. What makes it truly special is the granite casing at its base;unlike the others, Menkaure chose expensive, hard granite brought all the way from Aswan.Despite its smaller size, its construction is incredibly precise, showing a shift towards more refined architectural details. Next to it, you can see the three Queen's Pyramids, making this spot a perfect ending to our journey through the divine Giza plateau."'''
    ], gx, gy)

    screen.blit(big_font.render("Menkaure", True, (255,220,140)), (410,40))

    button("Press RIGHT Arrow to move",'right')
# -----------------------------------
# Zoom & Inside the Pyramid
# ------------------------------------
def zoom_transition():
    global zoom, scene

    draw_sun()

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
        reset_puzzle() 
        reset_fade()

def draw_symbol_shape(shape, x, y):
    cx = x + 30
    cy = y + 30

    if shape == "ankh":
        midpoint_circle(cx, cy - 5, 12, BLACK)
        bresenham_line(cx, cy + 5, cx, cy + 20, BLACK)
        bresenham_line(cx - 8, cy + 8, cx + 8, cy + 8, BLACK)

    elif shape == "water":
        for i in range(2):
            pygame.draw.arc(screen, BLACK, (x + 10, y + 15 + i * 10, 40, 15), 0, math.pi, 2)

    elif shape == "basket":
        pygame.draw.arc(screen, BLACK, (x + 15, y + 20, 30, 20), math.pi, 2 * math.pi, 3)

    elif shape == "twist":
        bresenham_line(x + 15, y + 15, x + 45, y + 45, BLACK)
        bresenham_line(x + 45, y + 15, x + 15, y + 45, BLACK)

def draw_question():
    question = "Which symbol represents the letter H?"
    txt = mid_font.render(question, True, WHITE)
    screen.blit(txt, (360, 140))

    for i, (letter, shape) in enumerate(symbols):
        x = puzzle_x + i * (tile_size + 20)
        y = puzzle_y

        pygame.draw.rect(screen, (230, 200, 150), (x, y, tile_size, tile_size), border_radius=15)
        pygame.draw.rect(screen, (70, 40, 20), (x, y, tile_size, tile_size), 2, border_radius=15)

        draw_symbol_shape(shape, x, y)

def click_answer(index):
    global puzzle_solved, scene

    if index == correct_answer:
        puzzle_solved = True
        audio.play("unlock")
        scene = 7  
    else:
        print("Wrong answer")

def torch_flame(x,y):
    flick = random.randint(-5,5)
    pygame.draw.rect(screen, BROWN, (x-3,y,6,35))
    filled_circle(x, y+flick, 14, (255,180,50))
    filled_circle(x, y+flick+2, 10, (255,120,30))

def flashlight_effect(base_radius=150, darkness=170):
    mx, my = pygame.mouse.get_pos()

    radius = int(base_radius * zoom_level)

    dark_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark_layer.fill((0, 0, 0, darkness))  
    steps = 20
    for i in range(steps):
        r = int(radius * (i / steps))
        alpha = int(darkness * (i / steps))  
        pygame.draw.circle(dark_layer, (0, 0, 0, alpha), (mx, my), r)
    pygame.draw.circle(dark_layer, (0, 0, 0, 0), (mx, my), int(radius * 0.6))

    screen.blit(dark_layer, (0, 0))

def interior_scene():
    global room_sound_played
    screen.fill((28,22,18))

    pygame.draw.polygon(screen,(70,60,50),
        [(0,0),(260,220),(260,750),(0,750)])

    pygame.draw.polygon(screen,(70,60,50),
        [(1200,0),(940,220),(940,750),(1200,750)])

    pygame.draw.rect(screen,(55,48,40),(260,0,680,750))
    pygame.draw.polygon(screen,(95,80,65),
        [(400,750),(800,750),(700,260),(500,260)])

    torch_flame(150,250)
    torch_flame(1050,250)
    glow = pygame.Surface((1200,750), pygame.SRCALPHA)

    pygame.draw.circle(glow,(255,140,20,60),(150,250),180)
    pygame.draw.circle(glow,(255,140,20,60),(1050,250),180)

    screen.blit(glow,(0,0))

    pygame.draw.rect(screen,(120,120,120),(500,520,220,70))
    pygame.draw.rect(screen,(90,90,90),(530,490,160,35))
    pygame.draw.rect(screen,(40,40,40),(500,520,220,70),2)

    draw_question()
    if not puzzle_solved:
        ()

    gx = int(WIDTH * 0.85)
    gy = int(HEIGHT * 0.90)

    guide(gx, gy)
    audio.play_once("roomm")
    
    title = big_font.render("Inside The Pyramid", True, BROWN)
    flashlight_effect()
    screen.blit(title, (420,30))

    if puzzle_solved:
        button("ESC to Return")
    else:
        button("ESC to Return",'left')
        button("Solve to get tressure")

def reset_puzzle():
    global puzzle_solved
    puzzle_solved = False

def unlock_scene():
    global unlock_frame, scene

    screen.fill((10,10,10))

    shake_x = random.randint(-3,3)
    shake_y = random.randint(-3,3)

    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    radius = min(10 + unlock_frame*6, 500)

    pygame.draw.circle(glow, (255,200,100,120), (WIDTH//2, HEIGHT//2), radius)
    screen.blit(glow, (0,0))

    txt = big_font.render("Ancient Chamber Unlocked!", True, (255,215,90))
    screen.blit(txt, (WIDTH//2 - 180 + shake_x, HEIGHT//2 - 50 + shake_y))

    audio.play_once("unlock")

    unlock_frame += 1

    if unlock_frame > 80:
        scene = 8 
        unlock_frame = 0

def treasure_scene():
    
    screen.fill((10, 8, 5))
    pygame.draw.rect(screen, (40,35,25), (0,0,WIDTH,HEIGHT))
    pygame.draw.rect(screen, (70,55,40), (0,500,WIDTH,250))
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    for i in range(5):
        pygame.draw.circle(
            glow,
            (255, 215, 90, 40),
            (WIDTH//2, 480),
            120 + i*40
        )

    screen.blit(glow, (0,0))
    chest_x = WIDTH//2 - 120
    chest_y = 430

    pygame.draw.rect(screen, (120,85,40), (chest_x, chest_y, 240, 120))
    pygame.draw.rect(screen, (80,60,30), (chest_x, chest_y, 240, 120), 3)

    pygame.draw.rect(screen, (140,100,50), (chest_x, chest_y-60, 240, 60))
    pygame.draw.rect(screen, (80,60,30), (chest_x, chest_y-60, 240, 60), 3)

    for i in range(20):
        gx = chest_x + 20 + (i%5)*40
        gy = chest_y + 20 + (i//5)*20
        filled_circle(gx, gy, 8, (255,215,0))

    filled_circle(chest_x+60, chest_y+40, 10, (0,255,200))
    filled_circle(chest_x+160, chest_y+60, 10, (255,0,100))
    filled_circle(chest_x+120, chest_y+30, 10, (100,200,255))
    for _ in range(15):
        x = random.randint(chest_x, chest_x+240)
        y = random.randint(chest_y-80, chest_y)
        filled_circle(x, y, 2, (255,255,200))

    title = big_font.render("Treasure Discovered!", True, GOLD)
    screen.blit(title, (WIDTH//2 - 180, 120))

    msg = mid_font.render("You unlocked the secrets of the pyramid", True, WHITE)
    screen.blit(msg, (WIDTH//2 - 220, 180))
    gx = int(WIDTH * 0.85)
    gy = int(HEIGHT * 0.90)

    guide(gx, gy)
    button("Press ESC to Exit")  
# --------------------------------------------
# Final Scene
# --------------------------------------------
def ending():
    screen.blit(end_bg, (0, 0))

    audio.play_once("end")
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 120))
    screen.blit(overlay, (0, 0))
    title = title_font.render("Thank you for joining", True, (255, 220, 120))
    screen.blit(title, title.get_rect(center=(WIDTH//3,300)))

    title = title_font.render("our virtual tour of", True, (255, 220, 120))
    screen.blit(title, title.get_rect(center=(WIDTH//3, 360)))

    title = title_font.render("The Great Pyramids ♥", True, (255, 220, 120))
    screen.blit(title, title.get_rect(center=(WIDTH//3, 430)))

    msg2 = mid_font.render("History still breathes here", True, (220,200,150))
    screen.blit(msg2, msg2.get_rect(center=(WIDTH//3, 500)))
    button("Press R to Restart",'left')


# --------------------------------------------------------------  
# Main Loop
# ---------------------------------------------------------------
running = True

while running:
    clock.tick(60)
    frame += 1

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = pygame.mouse.get_pos()
            if scene in [1,2,3]:
                if 220 <= mx <= 760 and 180 <= my <= 540:
                    inside_from = scene
                    scene = 6
                    zoom = 0
                    reset_fade()
            elif scene == 5:
                for i in range(len(symbols)):
                    x = puzzle_x + i * (tile_size + 20)
                    y = puzzle_y

                    if x <= mx <= x+tile_size and y <= my <= y+tile_size:
                        click_answer(i)

        if event.type == pygame.MOUSEWHEEL:
            zoom_level += event.y * 0.1   
            zoom_level = max(MIN_ZOOM, min(MAX_ZOOM, zoom_level))

        if event.type == pygame.KEYDOWN:

            if scene == 0 and event.key == pygame.K_SPACE:
                scene = 0.5
                reset_fade()

            elif scene == 0.5 and event.key == pygame.K_RIGHT:
                audio.reset()
                overview_played = False
                scene = 1
                reset_fade()

            elif scene in [1,2,3] and event.key == pygame.K_RIGHT:
                scene += 1
                reset_fade()

            elif scene == 4 and event.key == pygame.K_r:
                audio.reset() 
                scene = 0
                reset_fade()

            elif event.key == pygame.K_ESCAPE:
                if scene in [5, 7, 8]:
                    scene = inside_from
                    reset_fade()

            elif event.key == pygame.K_r:
                audio.reset()
                reset_puzzle()
                scene = 0
                reset_fade()
            elif scene == 8 and event.key == pygame.K_r:
                scene = 0
                reset_fade()

    # DRAW
    # -----------------------------------------------------------
    if scene == 0:
        intro()
    elif scene == 0.5:
        pyramids_overview()
        if not overview_played:
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