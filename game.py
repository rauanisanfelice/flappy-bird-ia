import pygame, random
from pygame.locals import *

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

GROUND_WIDTH = SCREEN_WIDTH * 2
GROUND_HEIGHT = 100

PIPE_WIDTH = 80
PIPE_HEIGHT = 500
PIPE_GAP = 150

SPEED = 10
GAME_SPEED = 10
GRAVITY = 1

IMG_BASE = 'base.png'
IMG_BACKGROUND = 'background-day.png'
IMG_BIRD_MIDFLAP = 'bluebird-midflap.png'
IMG_BIRD_UPFLAP = 'bluebird-upflap.png'
IMG_BIRD_DOWNFLAP = 'bluebird-downflap.png'
IMG_PIPE = 'pipe-red.png'

# CRIA BACKGROUND E DEIXA DO TAMANHO DA TELA
BACKGOUND = pygame.image.load(IMG_BACKGROUND)
BACKGOUND = pygame.transform.scale(BACKGOUND, (SCREEN_WIDTH, SCREEN_HEIGHT))


class Bird(pygame.sprite.Sprite):
    
    def __init__(self):
        """ Funcao de propriedades do Bird.'"""

        pygame.sprite.Sprite.__init__(self)

        # convert_alpha = desconsidera pixel transparente
        self.images = [
            pygame.image.load(IMG_BIRD_UPFLAP).convert_alpha(),
            pygame.image.load(IMG_BIRD_MIDFLAP).convert_alpha(),
            pygame.image.load(IMG_BIRD_DOWNFLAP).convert_alpha()
        ]
        
        self.speed = SPEED
        self.current_image = 0
        self.image = pygame.image.load(IMG_BIRD_MIDFLAP).convert_alpha()
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

        # CENTRALIZA
        self.rect[0] = (SCREEN_WIDTH / 2) - (self.rect[2] / 2)
        self.rect[1] = (SCREEN_HEIGHT / 2) - (self.rect[3] / 2)
        
    def update(self):
        """Funcao atualiza o movimento do Bird"""

        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]

        # INCLUI GRAVIDADE
        self.speed += GRAVITY

        # ATUALIZA ALTURA
        self.rect[1] += self.speed
    
    def bump(self):
        """Funcao que faz o Bird pular"""

        self.speed = -SPEED


class Ground(pygame.sprite.Sprite):
    
    def __init__(self, xpos):
        """ Funcao de propriedades do Fundo.'"""
        
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(IMG_BASE).convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED


class Pipe(pygame.sprite.Sprite):

    def __init__(self, xpos, ysize, inverted=False):
        """ Funcao de propriedades do Canos.'"""
        
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(IMG_PIPE).convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image =pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED


def is_off_screen(sprite):
    """Função que valida se o sprite esta fora da tela"""

    return sprite.rect[0] < -(sprite.rect[2])


def get_random_pipes(xpos):
    """Gera canos aleatorios"""

    size = random.randint(100, 300)
    
    pipe = Pipe(xpos, size)
    pipe_inverted = Pipe(xpos, SCREEN_HEIGHT - size - PIPE_GAP, True)
    
    return (pipe, pipe_inverted)


# INICIA JOGO COM SCREEN
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# INICIA BIRD
bird_group = pygame.sprite.Group()
bird = Bird()
bird_group.add(bird)

# INICIA GROUND
ground_group = pygame.sprite.Group()
for i in range(2):
    ground = Ground(GROUND_WIDTH * i)
    ground_group.add(ground)

# INICIA PIPE
pipe_group = pygame.sprite.Group()
for i in range(2):
    pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
    pipe_group.add(pipes[0])
    pipe_group.add(pipes[1])

# FPS
clock = pygame.time.Clock()

while True:
    
    # 30 FPS
    clock.tick(30)

    # VERIFICA EVENTOS
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
        
        if event.type == KEYDOWN:
            if event.key == K_SPACE:
                bird.bump()
    
    # INICIA TELA
    screen.blit(BACKGOUND, (0, 0))
    
    # VERIFCA SE O GROUND SAIU DA TELA
    if is_off_screen(ground_group.sprites()[0]): 
        ground_group.remove(ground_group.sprites()[0])

        new_ground = Ground(GROUND_WIDTH - 20)
        ground_group.add(new_ground)

    # VERIFCA SE O PIPE SAIU DA TELA
    if is_off_screen(pipe_group.sprites()[0]):
        pipe_group.remove(pipe_group.sprites()[0])
        pipe_group.remove(pipe_group.sprites()[0])

        pipes = get_random_pipes(SCREEN_WIDTH * 2)

        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    # MOSTRA O BIRD
    bird_group.update()
    bird_group.draw(screen)

    # MOSTRA O GROUND 
    ground_group.update()
    ground_group.draw(screen)

    # MOSTRA O PIP
    pipe_group.update()
    pipe_group.draw(screen)

    # VALIDA COLISAO COM O CHAO
    if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
        pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
        # TODO Game Over
        break

    # ATUALIZA DA TELA
    pygame.display.update()