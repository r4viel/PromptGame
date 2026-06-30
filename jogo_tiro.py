import pygame
import random

pygame.init()

LARGURA = 800
ALTURA = 600
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Robot Defense - Template")

FPS = 60
clock = pygame.time.Clock()


# CLASSE BASE
class Entidade(pygame.sprite.Sprite):
    def __init__(self, x, y, velocidade, xp):
        super().__init__()
        self.velocidade = velocidade
        self.image = pygame.Surface((40, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.xp = xp 

    def mover(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy


# JOGADOR
class Jogador(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, 5, 0)
        self.image.fill((0, 255, 0))  # verde
        self.vida = 5
        self.ultima_direcao = pygame.Vector2(0, -1)  # direção padrão: pra cima

        # --- NOVO: sistema de nível ---
        self.nivel = 1
        self.xp_necessario = 100

    def ganhar_xp(self, quantidade):
        self.xp += quantidade
        # pode subir mais de um nível de uma vez se ganhar muito xp
        while self.xp >= self.xp_necessario:
            self.xp -= self.xp_necessario
            self.nivel += 1
            self.xp_necessario += 50

    def update(self):
        keys = pygame.key.get_pressed()
        direcao = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direcao.y = -1
        if keys[pygame.K_s]:
            direcao.y = 1
        if keys[pygame.K_a]:
            direcao.x = -1
        if keys[pygame.K_d]:
            direcao.x = 1

        if direcao.length() > 0:
            direcao = direcao.normalize()
            self.ultima_direcao = direcao.copy()  # só atualiza se andou
            self.mover(direcao.x * self.velocidade, direcao.y * self.velocidade)

        # limites de tela
        self.rect.x = max(0, min(self.rect.x, LARGURA - 40))
        self.rect.y = max(0, min(self.rect.y, ALTURA - 40))


# TIRO (DO JOGADOR)
class Tiro(Entidade):
    def __init__(self, x, y, direcao):
        super().__init__(x, y, 10, 0)
        self.image.fill((255, 255, 0))  # amarelo
        self.direcao = direcao  # Vector2

    def update(self):
        self.rect.x += self.direcao.x * self.velocidade
        self.rect.y += self.direcao.y * self.velocidade

        # remove se sair da tela em qualquer direção
        if (self.rect.bottom < 0 or self.rect.top > ALTURA or
                self.rect.right < 0 or self.rect.left > LARGURA):
            self.kill()


# ROBO BASE
class Robo(Entidade):
    def __init__(self, x, y, velocidade, xp):
        super().__init__(x, y, velocidade, xp)
        self.image.fill((255, 0, 0))  # vermelho

    def atualizar_posicao(self):
        raise NotImplementedError


# ROBO EXEMPLO — ZigueZague
class RoboZigueZague(Robo):
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=3, xp=15)
        self.direcao = 1

    def atualizar_posicao(self):
        self.rect.y += self.velocidade
        self.rect.x += self.direcao * 3

        if self.rect.x <= 0 or self.rect.x >= LARGURA - 40:
            self.direcao *= -1

    def update(self):
        self.atualizar_posicao()
        if self.rect.y > ALTURA:
            self.kill()


todos_sprites = pygame.sprite.Group()
inimigos = pygame.sprite.Group()
tiros = pygame.sprite.Group()

jogador = Jogador(LARGURA // 2, ALTURA - 60)
todos_sprites.add(jogador)

pontos = 0
spawn_timer = 0

# --- timers de cronômetro e tiro automático ---
tempo_inicio = pygame.time.get_ticks()
TIRO_AUTOMATICO_EVENTO = pygame.USEREVENT + 1
pygame.time.set_timer(TIRO_AUTOMATICO_EVENTO, 1000)  # dispara a cada 1000 ms

font = pygame.font.SysFont(None, 30)

rodando = True
while rodando:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                tiro = Tiro(jogador.rect.centerx, jogador.rect.centery, jogador.ultima_direcao)
                todos_sprites.add(tiro)
                tiros.add(tiro)

        # tiro automático
        if event.type == TIRO_AUTOMATICO_EVENTO:
            tiro = Tiro(jogador.rect.centerx, jogador.rect.centery, jogador.ultima_direcao)
            todos_sprites.add(tiro)
            tiros.add(tiro)

    # timer de entrada dos inimigos
    spawn_timer += 1
    if spawn_timer > 40:
        robo = RoboZigueZague(random.randint(40, LARGURA - 40), -40)
        todos_sprites.add(robo)
        inimigos.add(robo)
        spawn_timer = 0

    # colisão tiro x robô
    colisao = pygame.sprite.groupcollide(inimigos, tiros, True, True)
    pontos += len(colisao)
    if colisao:
        jogador.ganhar_xp(sum(robo.xp for robo in colisao))

    # colisão robô x jogador
    if pygame.sprite.spritecollide(jogador, inimigos, True):
        jogador.vida -= 1
        if jogador.vida <= 0:
            print("GAME OVER!")
            rodando = False

    # atualizar
    todos_sprites.update()

    # desenhar
    TELA.fill((20, 20, 20))
    todos_sprites.draw(TELA)

    # Painel de pontos e vida
    texto = font.render(f"Vida: {jogador.vida}  |  Pontos: {pontos}  |  Nivel: {jogador.nivel}", True, (255, 255, 255))
    TELA.blit(texto, (10, 10))

    # cronômetro no canto superior direito
    tempo_ms = pygame.time.get_ticks() - tempo_inicio
    segundos_totais = tempo_ms // 1000
    minutos = segundos_totais // 60
    segundos = segundos_totais % 60
    texto_tempo = font.render(f"{minutos:02}:{segundos:02}", True, (255, 255, 255))
    TELA.blit(texto_tempo, (LARGURA - texto_tempo.get_width() - 10, 10))

    # --- NOVO: barra de XP na parte inferior da tela ---
    barra_largura = LARGURA - 20
    barra_altura = 20
    barra_x = 10
    barra_y = ALTURA - barra_altura - 10

    proporcao = jogador.xp / jogador.xp_necessario
    proporcao = max(0, min(proporcao, 1))  # garante que fique entre 0 e 1

    # fundo da barra (cinza escuro)
    pygame.draw.rect(TELA, (60, 60, 60), (barra_x, barra_y, barra_largura, barra_altura))
    # preenchimento (azul)
    pygame.draw.rect(TELA, (0, 150, 255), (barra_x, barra_y, barra_largura * proporcao, barra_altura))
    # borda
    pygame.draw.rect(TELA, (255, 255, 255), (barra_x, barra_y, barra_largura, barra_altura), 2)

    # texto "XP: x / y" centralizado na barra
    texto_xp = font.render(f"XP: {jogador.xp} / {jogador.xp_necessario}", True, (255, 255, 255))
    TELA.blit(texto_xp, (barra_x + barra_largura // 2 - texto_xp.get_width() // 2, barra_y - 2))

    pygame.display.flip()

pygame.quit()