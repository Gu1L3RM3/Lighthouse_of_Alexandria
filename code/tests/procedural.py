import pygame
from perlin_noise import PerlinNoise
import random

# --- Constantes ---
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 10
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE

# --- Cores para os Tiles ---
COLOR_DEEP_WATER = (3, 3, 79)
COLOR_WATER = (28, 107, 160)
COLOR_SAND = (210, 190, 122)
COLOR_GRASS = (65, 141, 43)
COLOR_FOREST = (34, 85, 30)
COLOR_ROCK = (87, 87, 87)
COLOR_SNOW = (255, 255, 255)

terrain_map = {
    -0.5: COLOR_DEEP_WATER,
    -0.1: COLOR_WATER,
    -0.05: COLOR_SAND,
    0.1: COLOR_GRASS,
    0.25: COLOR_FOREST,
    0.35: COLOR_ROCK,
    0.5: COLOR_SNOW,
}

# --- Constantes de Iluminação ---
AMBIENT_LIGHT = 50 # Quão escuro o ambiente é, de 0 (totalmente preto) a 255 (totalmente claro)
TORCH_RADIUS = 150 # Raio de luz da tocha em pixels
TORCH_BRIGHTNESS = 200 # Intensidade da luz da tocha (0-255)

# --- Função de Geração do Mapa (Mesma do exemplo anterior) ---
def generate_map(width, height):
    octaves = 8
    seed = random.randint(0, 100)
    noise_generator = PerlinNoise(octaves=octaves, seed=seed)
    
    map_data = [[0 for _ in range(width)] for _ in range(height)]
    
    scale = 100.0

    for y in range(height):
        for x in range(width):
            value = noise_generator([x / scale, y / scale])
            map_data[y][x] = value
            
    return map_data

# --- Função para Desenhar o Mapa (Mesma do exemplo anterior) ---
def draw_map(surface, map_data):
    for y, row in enumerate(map_data):
        for x, value in enumerate(row):
            terrain_color = COLOR_GRASS
            for threshold, color in sorted(terrain_map.items()):
                if value <= threshold:
                    terrain_color = color
                    break
            
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, terrain_color, rect)

# --- NOVA FUNÇÃO: Gerar Superfície de Luz ---
def create_light_surface(width, height, ambient_light):
    """
    Cria uma superfície preta para ser a base da iluminação.
    Ambient_light define a cor base (escuridão).
    """
    light_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    # Preenche com uma cor escura (que será o ambiente)
    light_surface.fill((ambient_light, ambient_light, ambient_light))
    return light_surface

# --- NOVA FUNÇÃO: Desenhar uma Tocha na Superfície de Luz ---
def draw_torch_light(light_surface, position, radius, brightness):
    """
    Desenha um círculo de luz radial na superfície de luz.
    position: (x, y) centro da tocha
    radius: raio da luz
    brightness: intensidade da luz no centro
    """
    # Cria uma superfície temporária para o gradiente da tocha
    torch_gradient = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    
    # Desenha círculos com cores alpha decrescentes para criar o gradiente
    for r in range(radius, 0, -1):
        # Calcula o alpha baseado na distância do centro
        # Mais perto do centro = mais brilhante (alpha mais alto)
        alpha = int(brightness * (r / radius)) 
        pygame.draw.circle(torch_gradient, (255, 255, 255, alpha), (radius, radius), r)
    
    # Blit (cola) o gradiente da tocha na superfície de luz principal
    # A posição é o centro da tocha na superfície de luz
    light_surface.blit(torch_gradient, (position[0] - radius, position[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)


# --- Função Principal (Main) ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mapa Procedural com Iluminação de Tocha")
    clock = pygame.time.Clock()

    print("Gerando mapa... Isso pode levar um momento.")
    map_data = generate_map(GRID_WIDTH, GRID_HEIGHT)
    print("Mapa gerado!")

    # Posição inicial da tocha (no centro da tela para começar)
    torch_x, torch_y = WIDTH // 2, HEIGHT // 2
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    print("Gerando novo mapa...")
                    map_data = generate_map(GRID_WIDTH, GRID_HEIGHT)
                    print("Novo mapa gerado!")
                
                # Mover a tocha com as setas do teclado
                if event.key == pygame.K_LEFT:
                    torch_x = max(0, torch_x - 10)
                if event.key == pygame.K_RIGHT:
                    torch_x = min(WIDTH, torch_x + 10)
                if event.key == pygame.K_UP:
                    torch_y = max(0, torch_y - 10)
                if event.key == pygame.K_DOWN:
                    torch_y = min(HEIGHT, torch_y + 10)

        # 1. Desenha o mapa base
        screen.fill((0, 0, 0)) # Limpa a tela
        draw_map(screen, map_data)

        # 2. Cria e desenha a superfície de luz
        light_surface = create_light_surface(WIDTH, HEIGHT, AMBIENT_LIGHT)
        
        # 3. Desenha a(s) tocha(s) na superfície de luz
        # Podemos ter várias tochas, por exemplo:
        draw_torch_light(light_surface, (torch_x, torch_y), TORCH_RADIUS, TORCH_BRIGHTNESS)
        
        # Exemplo de uma segunda tocha estática
        # draw_torch_light(light_surface, (100, 100), TORCH_RADIUS, TORCH_BRIGHTNESS)

        # 4. Aplica a superfície de luz na tela principal
        # Usamos BLEND_RGBA_ADD para "somar" a luz ao mapa
        screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 5. Atualiza a tela
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()