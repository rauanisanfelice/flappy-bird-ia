import pygame, random, pygame_menu, warnings
import numpy as np
import pandas as pd

from sklearn import neural_network, metrics
from sklearn.model_selection import train_test_split
from sklearn.exceptions import ConvergenceWarning

from pygame.locals import *

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600

GROUND_WIDTH = SCREEN_WIDTH * 2
GROUND_HEIGHT = 100

PIPE_WIDTH = 70
PIPE_HEIGHT = 500
PIPE_GAP_LEVEL = [200, 130, 60]
PIPE_GAP = PIPE_GAP_LEVEL[0]

SPEED = 10
GAME_SPEED = 10
GRAVITY = 0.05

COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)

IMG_BASE = 'assets/base.png'
IMG_BACKGROUND = 'assets/background-day.png'
IMG_BIRD_MIDFLAP = 'assets/bluebird-midflap.png'
IMG_BIRD_UPFLAP = 'assets/bluebird-upflap.png'
IMG_BIRD_DOWNFLAP = 'assets/bluebird-downflap.png'
IMG_PIPE = 'assets/pipe-red.png'

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


class Scenario(object):

    def __init__(self):
        super().__init__()
    
    def is_off_screen(self):
        """Função que valida se o sprite esta fora da tela"""

        return self.rect[0] < -(self.rect[2])


class Ground(pygame.sprite.Sprite, Scenario):
    
    def __init__(self, xpos=GROUND_WIDTH):
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


class Pipe(pygame.sprite.Sprite, Scenario):

    def __init__(self, xpos, ysize, inverted=False):
        """ Funcao de propriedades do Canos.'"""
        
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load(IMG_PIPE).convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED


class MyMLPRegressor(object):
    
    def __init__(self):

        self.X_train = None
        self.X_test = None
        self.Y_train = None
        self.Y_test = None
        self.mlp = neural_network.MLPRegressor(hidden_layer_sizes=3)

    def train_test(self, data, test_size:float=0.25, random_state:int=1):

        self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(
            data.iloc[:,0:3],
            data.iloc[:,3],
            test_size=test_size,
            random_state=random_state
        )

    def fit(self):
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning, module="sklearn")
            
            self.mlp.fit(self.X_train, self.Y_train)
    
    def predict(self, data):

        self.pre_test_y = self.mlp.predict(data)

    def score(self):

        test_score = metrics.mean_squared_error(self.Y_test, self.pre_test_y, multioutput='uniform_average')
        print("mean absolute error:", round(test_score, 2))
        


def get_random_pipes(xpos):
    """Gera canos aleatorios"""
    
    global PIPE_GAP
    size = random.randint(110, 350)
    
    pipe = Pipe(xpos, size)
    pipe_inverted = Pipe(xpos, SCREEN_HEIGHT - size - PIPE_GAP, True)
    
    return (pipe, pipe_inverted)


# DIFICULDADE DO JOGO
def set_difficulty(value, difficulty):
    global PIPE_GAP
    PIPE_GAP = PIPE_GAP_LEVEL[difficulty]


# GAME
def start_the_game():
    
    distancia_total = 0

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
        pipes = get_random_pipes(SCREEN_WIDTH * i + 500)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    # FPS
    clock = pygame.time.Clock()
    
    while True:
        
        # 30 FPS  
        clock.tick(30)
        
        # VERIFICA EVENTOS
        for event in pygame.event.get():
            # SAIR
            if event.type == QUIT:
                pygame.quit()
            
            # VOAR
            if event.type == KEYDOWN:
                if event.key == K_SPACE:
                    bird.bump()
        
        # INICIA TELA
        screen.blit(BACKGOUND, (0, 0))
        
        # VERIFCA SE O GROUND SAIU DA TELA
        if ground_group.sprites()[0].is_off_screen():
            ground_group.remove(ground_group.sprites()[0])

            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        # VERIFCA SE O PIPE SAIU DA TELA
        if pipe_group.sprites()[0].is_off_screen():
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])

            pipes = get_random_pipes(SCREEN_WIDTH * 2)

            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        # INFORMACOES
        rect = pygame.draw.rect(screen, (COLOR_BLACK), (5, 5, 170, 85), 2)
        pygame.display.set_caption('Box Test')
        font = pygame.font.SysFont('Arial', 20)
        altura = (SCREEN_HEIGHT - GROUND_HEIGHT) - bird_group.sprites()[0].rect[1] - bird.image.get_rect().height
        if (pipe_group.sprites()[0].rect[0] - bird_group.sprites()[0].rect[0]) > 0:
            distancia = pipe_group.sprites()[0].rect[0] - bird_group.sprites()[0].rect[0]
            center_pipe = (pipe_group.sprites()[1].rect[1] + pipe_group.sprites()[1].rect[3]) + (PIPE_GAP / 2)
        else: 
            distancia = pipe_group.sprites()[2].rect[0] - bird_group.sprites()[0].rect[0]
            center_pipe = (pipe_group.sprites()[3].rect[1] + pipe_group.sprites()[3].rect[3]) + (PIPE_GAP / 2)
        
        distancia_total += GAME_SPEED
        screen.blit(font.render(f'Altura: {altura}', True, COLOR_RED), (15, 10))
        screen.blit(font.render(f'Distancia: {distancia}', True, COLOR_RED), (15, 30))
        screen.blit(font.render(f'Centro: {center_pipe}', True, COLOR_RED), (15, 50))
        screen.blit(font.render(f'Score: {distancia_total}', True, COLOR_RED), (15, 70))

        mlp.predict(pd.DataFrame([[altura, distancia, center_pipe]], columns=['altura','distancia','centerpipe']))
        if int(round(mlp.pre_test_y[0], 0)) > 0:
            print('Pula')
            bird.bump()

        # ATUALIZA GROUPS
        bird_group.update()
        pipe_group.update()
        ground_group.update()

        # DESENHA GROUPS
        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        # VALIDA COLISAO COM O CHAO / PIPE
        if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
            pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
            break

        # ATUALIZA DA TELA
        pygame.display.update()

# REDE NEURAL
data = []
for i  in range(0, 100, 1):
    data.append([random.randint(1,500), random.randint(1,300), random.randint(110, 350), random.randint(0,1)])

mlp = MyMLPRegressor()
mlp.train_test(pd.DataFrame(data, columns=['altura','distancia','centerpipe','acao']))
mlp.fit()

# INICIA JOGO COM SCREEN
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Box Test')

# MENU
menu = pygame_menu.Menu(SCREEN_HEIGHT, SCREEN_WIDTH, 'Bem Vindo(a)!', theme=pygame_menu.themes.THEME_GREEN)
menu.add_selector('Dificuldade :', [('Fácil', 0), ('Normal', 1), ('Difícil', 2)], onchange=set_difficulty)
menu.add_button('Jogar', start_the_game)
menu.add_button('Sair', pygame_menu.events.EXIT)
menu.mainloop(screen)
