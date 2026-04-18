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
title_font = pygame.font.SysFont("georgia", 52, True)
big_font   = pygame.font.SysFont("arial", 34, True)
mid_font   = pygame.font.SysFont("arial", 26, True)
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
        sun_cache = pygame.Surface((size,size), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = sun_cache

        filled_circle(60,60,55,GOLD)

        globals()['screen'] = old_screen

    x = 180 + math.sin(frame*0.0025)*220
    y = 115 + math.cos(frame*0.0018)*35

    screen.blit(sun_cache, (x-60,y-60))

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

def guide(x,y):

    global guide_head_cache

    if guide_head_cache is None:

        guide_head_cache = pygame.Surface((50,50), pygame.SRCALPHA)

        old_screen = screen
        globals()['screen'] = guide_head_cache

        filled_circle(25,25,18,WHITE)

        globals()['screen'] = old_screen

    breathe = math.sin(frame*0.08)*3
    body_y = y + breathe

    # head cached
    screen.blit(guide_head_cache,(x-25,body_y-83))

    # body lines normal
    pygame.draw.line(screen,GREEN,(x,int(body_y-40)),(x,int(body_y+35)),5)

    pygame.draw.line(screen,GREEN,(x,int(body_y-10)),(x-25,int(body_y+10)),4)
    pygame.draw.line(screen,GREEN,(x,int(body_y-10)),(x+28,int(body_y-18)),4)

    pygame.draw.line(screen,GREEN,(x,int(body_y+35)),(x-18,int(body_y+70)),4)
    pygame.draw.line(screen,GREEN,(x,int(body_y+35)),(x+18,int(body_y+70)),4)
    
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

    pygame.draw.circle(screen, GOLD, (x+28, y-72), 4)

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
    x = guide_x - box_w - 40
    y = guide_y - 210

    # keep inside screen
    if x < 20:
        x = 20
    if y < 20:
        y = 20

    # translucent surface
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((255, 255, 255, 230))   # ~0.9 opacity

    # rounded rectangle
    pygame.draw.rect(panel, (255,255,255,230),
                     (0,0,box_w,box_h),
                     border_radius=8)

    pygame.draw.rect(panel, (0,0,0),
                     (0,0,box_w,box_h),
                     width=2,
                     border_radius=8)

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
def button(text):
    rect = pygame.Rect(420, 665, 360, 42)
    pygame.draw.rect(screen, (250,240,210), rect, border_radius=12)
    pygame.draw.rect(screen, BLACK, rect, 2, border_radius=12)
    txt = mid_font.render(text, True, BLACK)
    screen.blit(txt, (455, 674))

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
def intro():
    base_world()
    panel = pygame.Rect(250,180,700,300)
    pygame.draw.rect(screen, (245,220,170), panel, border_radius=20)
    pygame.draw.rect(screen, BLACK, panel, 3, border_radius=20)

    screen.blit(title_font.render("Welcome to the Giza Plateau", True, BROWN), (285,250))
    screen.blit(mid_font.render("A Living Journey Through Ancient Egypt", True, BLACK), (355,340))
    screen.blit(mid_font.render("Press SPACE to Begin", True, BLACK), (430,410))

def khufu():
    sunx = base_world()
    pyramid(250,540,450,350,(214,182,120), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble([
        "Khufu Pyramid",
        "Originally 146.6m tall.",
        "Built with 2 million blocks.",
        "Oldest Great Pyramid."
    ], gx, gy)

    screen.blit(big_font.render("Scene 1 : Khufu", True, WHITE), (450,40))
    button("RIGHT ARROW → Next")

def khafre():
    sunx = base_world()
    pyramid(330,540,390,310,(205,175,118), sunx)

    pygame.draw.polygon(screen, (230,230,220),
        [(525,230),(485,295),(565,295)])

    gx, gy = 980, 540
    guide(gx, gy)

    bubble([
        "Khafre Pyramid",
        "Built on higher ground.",
        "Still has casing stones.",
        "Connected to Sphinx."
    ], gx, gy)

    screen.blit(big_font.render("Scene 2 : Khafre", True, WHITE), (440,40))
    button("RIGHT ARROW → Next")

def menkaure():
    sunx = base_world()
    pyramid(430,540,270,220,(190,150,100), sunx)

    gx, gy = 980, 540
    guide(gx, gy)

    bubble([
        "Menkaure Pyramid",
        "Smallest of the three.",
        "Granite lower casing.",
        "Elegant design."
    ], gx, gy)

    screen.blit(big_font.render("Scene 3 : Menkaure", True, WHITE), (410,40))
    button("RIGHT ARROW → Finish")

def ending():
    base_world()
    screen.blit(title_font.render("Thank You For Visiting Egypt", True, WHITE), (250,300))
    screen.blit(big_font.render("History Still Breathes Here.", True, GOLD), (390,390))
    button("Press R To Restart")

# ---------------------------------------------------------------
# INTERIOR FUNCTIONS
# ---------------------------------------------------------------
def torch_flame(x,y):
    flick = random.randint(-5,5)
    pygame.draw.rect(screen, BROWN, (x-3,y,6,35))
    pygame.draw.circle(screen,(255,180,50),(x,y+flick),14)
    pygame.draw.circle(screen,(255,120,30),(x,y+flick+2),10)

def interior_scene():

    screen.fill((28,22,18))

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
    # ARTIFACTS
    # -----------------------------------------------------------
    pygame.draw.ellipse(screen,(150,100,60),(260,560,35,45))
    pygame.draw.ellipse(screen,(150,100,60),(930,560,35,45))

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

    # -----------------------------------------------------------
    # TITLE
    # -----------------------------------------------------------
    title = big_font.render("Inside The Pyramid", True, WHITE)
    screen.blit(title, (420,30))

    # -----------------------------------------------------------
    # RETURN BUTTON
    # -----------------------------------------------------------
    button("ESC → Return")
# ---------------------------------------------------------------
# ZOOM TRANSITION
# ---------------------------------------------------------------
# ===============================================================
# 6) zoom faster
# استبدل zoom_transition بالكامل
# ===============================================================

def zoom_transition():
    global zoom, scene

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

            mx,my = pygame.mouse.get_pos()

            if scene in [1,2,3]:

                # click pyramid area
                if 220 <= mx <= 760 and 160 <= my <= 540:
                    inside_from = scene
                    scene = 6
                    zoom = 0
                    reset_fade()

        if event.type == pygame.KEYDOWN:

            if scene == 0 and event.key == pygame.K_SPACE:
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

    fade_in()
    pygame.display.update()

pygame.quit()
sys.exit()