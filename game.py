import datetime
import pickle
import random
import warnings

import pandas as pd
import pygame
import pygame_menu
from pygame.locals import *
from sklearn import metrics, neural_network
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import cross_validate, train_test_split

SCREEN_WIDTH: int = 400
SCREEN_HEIGHT: int = 600

GROUND_WIDTH: int = SCREEN_WIDTH * 2
GROUND_HEIGHT: int = 100

PIPE_WIDTH: int = 70
PIPE_HEIGHT: int = 500
PIPE_GAP_LEVEL = [200, 130, 60]
PIPE_GAP: int = PIPE_GAP_LEVEL[0]

SPEED: int = 10
GAME_SPEED: int = 10
GRAVITY: int = 1

COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)

IMG_BASE: str = "assets/base.png"
IMG_BACKGROUND: str = "assets/background-day.png"
IMG_BIRD_MIDFLAP: str = "assets/bluebird-midflap.png"
IMG_BIRD_UPFLAP: str = "assets/bluebird-upflap.png"
IMG_BIRD_DOWNFLAP: str = "assets/bluebird-downflap.png"
IMG_PIPE: str = "assets/pipe-red.png"

# CRIA BACKGROUND E DEIXA DO TAMANHO DA TELA
BACKGOUND = pygame.image.load(IMG_BACKGROUND)
BACKGOUND = pygame.transform.scale(BACKGOUND, (SCREEN_WIDTH, SCREEN_HEIGHT))

ERROS: int = 0
BEST_SCORE: int = 120
BEST_PIPES: int = 0
GAMES_PLAY: int = 1
FILENAME_MODEL: str = "models/model.sav"
HISTORICO_MELHORES = []


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        """ Funcao de propriedades do Bird.'"""

        pygame.sprite.Sprite.__init__(self)

        # convert_alpha = desconsidera pixel transparente
        self.images = [
            pygame.image.load(IMG_BIRD_UPFLAP).convert_alpha(),
            pygame.image.load(IMG_BIRD_MIDFLAP).convert_alpha(),
            pygame.image.load(IMG_BIRD_DOWNFLAP).convert_alpha(),
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
            self.rect[1] = -(self.rect[3] - ysize)

        else:
            self.rect[1] = SCREEN_HEIGHT - ysize
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED


class MyMLPClassifier(object):
    def __init__(self):

        self.data = None
        self.X_train = None
        self.X_test = None
        self.Y_train = None
        self.Y_test = None
        self.predict_y = None
        self.mlp = neural_network.MLPClassifier(hidden_layer_sizes=2, max_iter=500)

    def set_data(self, data):
        self.data = data

    def train_test(self, test_size: float = 0.3, random_state: int = 1):

        self.X_train, self.X_test, self.Y_train, self.Y_test = train_test_split(
            self.data.iloc[:, 0:3],
            self.data.iloc[:, 3],
            test_size=test_size,
            random_state=random_state,
        )

    def fit(self):

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=ConvergenceWarning, module="sklearn"
            )

            self.mlp.fit(self.X_train, self.Y_train)

    def predict(self, data):

        self.predict_y = self.mlp.predict(data)

    def score(self):

        test_score = metrics.mean_squared_error(
            self.Y_test, self.predict_y, multioutput="uniform_average"
        )
        print("mean absolute error:", round(test_score, 2))

    def saveModel(self):
        pickle.dump(self.mlp, open(FILENAME_MODEL, "wb"))
        pickle.dump(
            self.mlp,
            open(
                f"models/model-{datetime.datetime.now().strftime('%Y%m%d%H%m%S')}.sav",
                "wb",
            ),
        )

    def cross_validate(self, return_train_score=False):
        print(
            cross_validate(
                self.mlp,
                self.X_test,
                self.Y_test,
                return_train_score=return_train_score,
            )
        )


def get_random_pipes(xpos, min: int = 110, max: int = 350):
    """Gera canos aleatorios"""

    global PIPE_GAP
    size = random.randint(min, max)

    pipe = Pipe(xpos, size)
    pipe_inverted = Pipe(xpos, SCREEN_HEIGHT - size - PIPE_GAP, True)

    return (pipe, pipe_inverted)


# DIFICULDADE DO JOGO
def set_difficulty(value, difficulty):
    global PIPE_GAP
    PIPE_GAP = PIPE_GAP_LEVEL[difficulty]


# GAME
def start_the_game():

    global BEST_SCORE, ERROS, GAMES_PLAY, HISTORICO_MELHORES, BEST_PIPES
    distancia_total = pipes_count = 0
    historico = []

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
        pipes = get_random_pipes(SCREEN_WIDTH * i + 500, 350, 350)
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
        rect = pygame.draw.rect(screen, (COLOR_BLACK), (5, 5, 185, 175), 2)
        pygame.display.set_caption("Box Test")
        font = pygame.font.SysFont("Arial", 20)
        altura = (
            (SCREEN_HEIGHT - GROUND_HEIGHT)
            - bird_group.sprites()[0].rect[1]
            - bird.image.get_rect().height
        )
        if (pipe_group.sprites()[0].rect[0] - bird_group.sprites()[0].rect[0]) > 0:
            pass_pipe = False
            distancia = (
                pipe_group.sprites()[0].rect[0] - bird_group.sprites()[0].rect[0]
            )
            center_pipe = (
                pipe_group.sprites()[1].rect[1] + pipe_group.sprites()[1].rect[3]
            ) + (PIPE_GAP / 2)

        else:

            if not pass_pipe:
                pass_pipe = True
                pipes_count += 1

            distancia = (
                pipe_group.sprites()[2].rect[0] - bird_group.sprites()[0].rect[0]
            )
            center_pipe = (
                pipe_group.sprites()[3].rect[1] + pipe_group.sprites()[3].rect[3]
            ) + (PIPE_GAP / 2)

        distancia_total += GAME_SPEED
        screen.blit(font.render(f"Altura: {altura}", True, COLOR_RED), (15, 10))
        screen.blit(font.render(f"Distancia: {distancia}", True, COLOR_RED), (15, 30))
        screen.blit(font.render(f"Centro: {center_pipe}", True, COLOR_RED), (15, 50))
        screen.blit(font.render(f"Score: {distancia_total}", True, COLOR_RED), (15, 70))
        screen.blit(font.render(f"Pipe: {pipes_count}", True, COLOR_RED), (15, 90))
        screen.blit(
            font.render(f"Best Score: {BEST_SCORE}", True, COLOR_RED), (15, 110)
        )
        screen.blit(
            font.render(f"Best Pipes: {BEST_PIPES}", True, COLOR_RED), (15, 130)
        )
        screen.blit(font.render(f"Jogos: {GAMES_PLAY}", True, COLOR_RED), (15, 150))

        mlp.predict(
            pd.DataFrame(
                [[altura, distancia, center_pipe]],
                columns=["altura", "distancia", "centerpipe"],
            )
        )
        if mlp.predict_y[0] == 1:
            bird.bump()
        historico.append([altura, distancia, center_pipe, mlp.predict_y[0]])

        # ATUALIZA GROUPS
        bird_group.update()
        pipe_group.update()
        ground_group.update()

        # DESENHA GROUPS
        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        # VALIDA COLISAO COM O CHAO / PIPE
        if pygame.sprite.groupcollide(
            bird_group, ground_group, False, False, pygame.sprite.collide_mask
        ) or pygame.sprite.groupcollide(
            bird_group, pipe_group, False, False, pygame.sprite.collide_mask
        ):

            if distancia_total > BEST_SCORE:

                ERROS = 0
                BEST_SCORE = distancia_total
                BEST_PIPES = pipes_count

                mlp.set_data(
                    pd.DataFrame(
                        historico, columns=["altura", "distancia", "centerpipe", "acao"]
                    )
                )
                mlp.train_test()
                mlp.fit()

                if BEST_PIPES >= 1:
                    HISTORICO_MELHORES.append(historico)
                    mlp.saveModel()

            else:
                if ERROS > 10:
                    ERROS = 0
                    pd1 = pdGeral = None
                    if HISTORICO_MELHORES:
                        for i in HISTORICO_MELHORES:
                            if pdGeral is None:
                                pdGeral = pd.DataFrame(
                                    i,
                                    columns=[
                                        "altura",
                                        "distancia",
                                        "centerpipe",
                                        "acao",
                                    ],
                                )
                            else:
                                pd1 = pd.DataFrame(
                                    i,
                                    columns=[
                                        "altura",
                                        "distancia",
                                        "centerpipe",
                                        "acao",
                                    ],
                                )
                                pdGeral.append(pd1)

                        mlp.set_data(
                            pd.DataFrame(
                                pdGeral,
                                columns=["altura", "distancia", "centerpipe", "acao"],
                            )
                        )
                        mlp.train_test()
                        mlp.fit()
                    else:
                        try:
                            mlp.mlp = pickle.load(open(FILENAME_MODEL, "rb"))
                        except:
                            pass

                else:
                    mlp.train_test(random_state=random.randint(0, 200))
                    mlp.fit()

                ERROS += 1

            GAMES_PLAY += 1
            break

        # ATUALIZA DA TELA
        pygame.display.update()


# REDE NEURAL
data = []
for i in range(0, 1000, 1):
    data.append(
        [
            random.randint(1, 500),
            random.randint(1, 300),
            random.randint(110, 350),
            random.choices([0, 1])[0],
        ]
    )

mlp = MyMLPClassifier()
mlp.set_data(pd.DataFrame(data, columns=["altura", "distancia", "centerpipe", "acao"]))
mlp.train_test()
mlp.fit()

# INICIA JOGO COM SCREEN
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Box Test")

while True:
    start_the_game()

# MENU
# menu = pygame_menu.Menu(SCREEN_HEIGHT, SCREEN_WIDTH, 'Bem Vindo(a)!', theme=pygame_menu.themes.THEME_GREEN)
# menu.add_selector('Dificuldade :', [('Fácil', 0), ('Normal', 1), ('Difícil', 2)], onchange=set_difficulty)
# menu.add_button('Jogar', start_the_game)
# menu.add_button('Sair', pygame_menu.events.EXIT)
# menu.mainloop(screen)
