import pygame, sys, random

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# --- fundo só pra você enxergar o efeito ---
bg = pygame.Surface((WIDTH, HEIGHT))
bg.fill((90, 100, 110))
for x in range(0, WIDTH, 40):
    pygame.draw.line(bg, (80, 90, 100), (x, 0), (x, HEIGHT))
for y in range(0, HEIGHT, 40):
    pygame.draw.line(bg, (80, 90, 100), (0, y), (WIDTH, y))
pygame.draw.rect(bg, (150, 120, 70), (200, 150, 120, 100))
pygame.draw.circle(bg, (60, 160, 80), (600, 400), 60)

# --- MUDANÇA: A função agora aceita um parâmetro de cor ---
def create_radial_light(radius, color=(255, 255, 255), strength=255):
    """Retorna uma surface (SRCALPHA) com gradiente da cor especificada.
        color = cor da luz no centro.
        strength = quão forte fica o centro (0..255)."""
    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    cx = cy = radius
    
    for r in range(radius, 0, -1):
        t = r / radius
        intensity = int((1 - t*t) * strength)
        if intensity <= 0:
            continue
        
        # --- MUDANÇA: Escala a cor de entrada pela intensidade ---
        # Em vez de (intensity, intensity, intensity), multiplicamos cada
        # componente (R, G, B) da cor pela intensidade normalizada.
        factor = intensity / 255.0
        r_val = int(color[0] * factor)
        g_val = int(color[1] * factor)
        b_val = int(color[2] * factor)

        pygame.draw.circle(surf, (r_val, g_val, b_val, 255), (cx, cy), r)
        
    return surf

# --- MUDANÇA: Definimos a cor da tocha e a passamos para a função ---
BASE_RADIUS = 140
TORCH_COLOR = (255, 170, 100) # Um laranja quente para a tocha 🔥
light_tex = create_radial_light(BASE_RADIUS, color=TORCH_COLOR, strength=255)


# posição do player/tocha
px, py = WIDTH // 2, HEIGHT // 2

# luz ambiente (0=totalmente escuro, 255=sem escurecer)
AMBIENT = 25

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    keys = pygame.key.get_pressed()
    v = 5
    px += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * v
    py += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * v

    # fundo do jogo
    screen.blit(bg, (0, 0))

    # --- cria o lightmap deste frame ---
    lightmap = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    lightmap.fill((AMBIENT, AMBIENT, AMBIENT, 255))

    # tremulação leve da tocha
    jitter = random.randint(-6, 6)
    if jitter:
        scaled = pygame.transform.smoothscale(light_tex, ((BASE_RADIUS+jitter)*2, (BASE_RADIUS+jitter)*2))
        lx = px - scaled.get_width() // 2
        ly = py - scaled.get_height() // 2
        lightmap.blit(scaled, (lx, ly), special_flags=pygame.BLEND_RGBA_ADD)
    else:
        lx = px - light_tex.get_width() // 2
        ly = py - light_tex.get_height() // 2
        lightmap.blit(light_tex, (lx, ly), special_flags=pygame.BLEND_RGBA_ADD)

    # --- aplica a iluminação multiplicando na cena ---
    screen.blit(lightmap, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    pygame.display.flip()
    clock.tick(60)