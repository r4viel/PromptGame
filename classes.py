"""Classes do jogo (entidades, projéteis, armas e inimigos)."""
import pygame
import random
import math

# Constantes de tela usadas pelas classes (mantidas em sincronia com jogo_tiro.py)
LARGURA = 800
ALTURA = 600


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
                             
class Jogador(Entidade):
    def __init__(self, x, y):
        super().__init__(x, y, 5, 0)
        self.image.fill((0, 255, 0))         
        self.vida = 5
        self.vida_maxima = 5
        self.ultima_direcao = pygame.Vector2(0, -1)                            
        self.dano_cooldown = 0 
        self.nivel = 1
        self.xp_necessario = 100
        self.level_ups_pendentes = 0                                     
        self.armas = {}

    def ganhar_xp(self, quantidade):
        self.xp += quantidade
        while self.xp >= self.xp_necessario:
            self.xp -= self.xp_necessario
            self.nivel += 1
            self.xp_necessario += 50
            self.level_ups_pendentes += 1

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
            self.ultima_direcao = direcao.copy()
            self.mover(direcao.x * self.velocidade, direcao.y * self.velocidade)

        self.rect.x = max(0, min(self.rect.x, LARGURA - 40))
        self.rect.y = max(0, min(self.rect.y, ALTURA - 40))

        if self.dano_cooldown > 0:
            self.dano_cooldown -= 1
                                
class Tiro(Entidade):
    def __init__(self, x, y, direcao, dano=1, velocidade=10,
                 perfurante=False, persistente=False,
                 cor=(255, 255, 0), tamanho=(10, 10)):
        super().__init__(x, y, velocidade, xp=0)
        self.image = pygame.Surface(tamanho)
        self.image.fill(cor)
        self.rect = self.image.get_rect(center=(x, y))
        self.direcao = direcao
        self.dano = dano
        self.perfurante = perfurante                                                
        self.persistente = persistente                                                           
        self.atingidos = {}                                               

    def update(self):
        self.rect.x += self.direcao.x * self.velocidade
        self.rect.y += self.direcao.y * self.velocidade

        if not self.persistente:
            if (self.rect.bottom < 0 or self.rect.top > ALTURA or
                    self.rect.right < 0 or self.rect.left > LARGURA):
                self.kill()
                                      
class Orbe(pygame.sprite.Sprite):
    def __init__(self, jogador, angulo_offset, raio, dano):
        super().__init__()
        self.image = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 200, 255), (11, 11), 11)
        pygame.draw.circle(self.image, (255, 255, 255), (11, 11), 11, 2)
        self.rect = self.image.get_rect()
        self.jogador = jogador
        self.angulo_offset = angulo_offset
        self.raio = raio
        self.dano = dano
        self.perfurante = True
        self.persistente = True
        self.atingidos = {}
        self.angulo_global = 0

    def update(self):
        self.angulo_global = (self.angulo_global + 3) % 360
        ang = math.radians(self.angulo_global + self.angulo_offset)
        cx, cy = self.jogador.rect.center
        self.rect.centerx = cx + math.cos(ang) * self.raio
        self.rect.centery = cy + math.sin(ang) * self.raio
                                       
class Espada(pygame.sprite.Sprite):
    def __init__(self, jogador, dano, raio, duracao, angulo_arco, angulo_inicial):
        super().__init__()
        self.image_original = pygame.Surface((46, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.image_original, (110, 80, 40), [(0, 7), (10, 7), (10, 13), (0, 13)])
        pygame.draw.polygon(self.image_original, (225, 232, 240),
                             [(9, 10), (40, 3), (46, 10), (40, 17)])
        pygame.draw.polygon(self.image_original, (255, 255, 255),
                             [(9, 10), (40, 3), (46, 10), (40, 17)], 2)

        self.jogador = jogador
        self.dano = dano
        self.raio = raio
        self.duracao = duracao
        self.tempo = 0
        self.angulo_arco = angulo_arco
        self.angulo_inicial = angulo_inicial
        self.perfurante = True
        self.persistente = False
        self.atingidos = {}

        self.image = self.image_original
        self.rect = self.image.get_rect()
        self._posicionar(self.angulo_inicial)

    def _posicionar(self, angulo):
        cx, cy = self.jogador.rect.center
        ang_rad = math.radians(angulo)
        centro = (cx + math.cos(ang_rad) * self.raio, cy + math.sin(ang_rad) * self.raio)
        self.image = pygame.transform.rotate(self.image_original, -angulo)
        self.rect = self.image.get_rect(center=centro)

    def update(self):
        self.tempo += 1
        progresso = min(1, self.tempo / self.duracao)
        angulo_atual = self.angulo_inicial + self.angulo_arco * progresso
        self._posicionar(angulo_atual)

        if self.tempo >= self.duracao:
            self.kill()

class Arma:
    nome_arma = "Arma"
    cooldown_base = 60
    nivel_max = 8

    def __init__(self):
        self.nivel = 1
        self.timer = 0

    def cooldown(self):
        return max(12, self.cooldown_base - self.nivel * 4)

    def descricao(self):
        return f"{self.nome_arma} - Nível {self.nivel}"

    def upar(self):
        if self.nivel < self.nivel_max:
            self.nivel += 1

    def ao_upar(self, jogador, todos_sprites, tiros):
        pass

    def update(self, jogador, todos_sprites, tiros, inimigos):
        self.timer -= 1
        if self.timer <= 0:
            self.disparar(jogador, todos_sprites, tiros, inimigos)
            self.timer = self.cooldown()

    def disparar(self, jogador, todos_sprites, tiros, inimigos):
        raise NotImplementedError

class ArmaEspada(Arma):
    nome_arma = "Espada"
    cooldown_base = 60

    def cooldown(self):
        return max(10, self.cooldown_base - self.nivel * 6)

    def disparar(self, jogador, todos_sprites, tiros, inimigos):
        dano = 2 + self.nivel
        raio = 50 + self.nivel * 9      
        duracao = 14
        arco = 130 + self.nivel * 4

        dir_v = jogador.ultima_direcao
        angulo_base = math.degrees(math.atan2(dir_v.y, dir_v.x))
        angulo_inicial = angulo_base - arco / 2

        espada = Espada(jogador, dano=dano, raio=raio, duracao=duracao,
                          angulo_arco=arco, angulo_inicial=angulo_inicial)
        todos_sprites.add(espada)
        tiros.add(espada)

class ArmaTripla(Arma):
    nome_arma = "Rajada Tripla"
    cooldown_base = 75

    def disparar(self, jogador, todos_sprites, tiros, inimigos):
        dano = 1 + self.nivel // 3
        qtd = 3 + (self.nivel - 1) // 3
        base = jogador.ultima_direcao
        angulo_total = 55

        for i in range(qtd):
            offset = -angulo_total / 2 + i * (angulo_total / (qtd - 1)) if qtd > 1 else 0
            d = base.rotate(offset)
            t = Tiro(jogador.rect.centerx, jogador.rect.centery, d,
                      dano=dano, velocidade=9, cor=(255, 150, 0), tamanho=(9, 9))
            todos_sprites.add(t)
            tiros.add(t)

class ArmaLaser(Arma):
    nome_arma = "Laser Perfurante"
    cooldown_base = 95

    def disparar(self, jogador, todos_sprites, tiros, inimigos):
        dano = 2 + self.nivel
        base = jogador.ultima_direcao
        t = Tiro(jogador.rect.centerx, jogador.rect.centery, base,
                  dano=dano, velocidade=16, perfurante=True,
                  cor=(255, 0, 255), tamanho=(6, 26))
        todos_sprites.add(t)
        tiros.add(t)

class ArmaOrbital(Arma):
    nome_arma = "Orbe Girante"
    cooldown_base = 999999                                              

    def __init__(self):
        super().__init__()
        self.orbes = []

    def _recriar_orbes(self, jogador, todos_sprites, tiros):
        for orbe in self.orbes:
            orbe.kill()
        self.orbes.clear()

        qtd = 1 + self.nivel // 2
        dano = 1 + self.nivel // 2
        raio = 90
        for i in range(qtd):
            offset = i * (360 / qtd)
            orbe = Orbe(jogador, offset, raio, dano)
            todos_sprites.add(orbe)
            tiros.add(orbe)
            self.orbes.append(orbe)

    def ao_upar(self, jogador, todos_sprites, tiros):
        self._recriar_orbes(jogador, todos_sprites, tiros)

    def update(self, jogador, todos_sprites, tiros, inimigos):
        pass                                                       

TODAS_AS_ARMAS = [ArmaEspada, ArmaTripla, ArmaLaser, ArmaOrbital]
                                               
class Robo(Entidade):
    def __init__(self, x, y, velocidade, xp, vida=1, cor=(255, 0, 0),
                 tamanho=(40, 40), dano=1):
        super().__init__(x, y, velocidade, xp)
        self.image = pygame.Surface(tamanho)
        self.image.fill(cor)
        self.rect = self.image.get_rect(center=(x, y))
        self.vida = vida
        self.vida_max = vida
        self.dano = dano

    def atualizar_posicao(self):
        raise NotImplementedError

    def update(self):
        self.atualizar_posicao()
        if self.rect.y > ALTURA + 60:
            self.kill()

class RoboZigueZague(Robo):
    """Desce em zigue-zague, ricocheteando nas bordas laterais."""
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=3, xp=15, vida=1,
                          cor=(255, 0, 0), tamanho=(40, 40), dano=1)
        self.direcao = random.choice([-1, 1])

    def atualizar_posicao(self):
        self.rect.y += self.velocidade
        self.rect.x += self.direcao * 3
        if self.rect.x <= 0 or self.rect.x >= LARGURA - 40:
            self.direcao *= -1

class RoboReto(Robo):
  
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=5, xp=10, vida=1,
                          cor=(255, 140, 0), tamanho=(32, 32), dano=1)

    def atualizar_posicao(self):
        self.rect.y += self.velocidade

class RoboPerseguidor(Robo):
    """Persegue a posição atual do jogador."""
    def __init__(self, x, y, jogador):
        super().__init__(x, y, velocidade=2.4, xp=25, vida=2,
                          cor=(200, 0, 200), tamanho=(36, 36), dano=1)
        self.jogador = jogador

    def atualizar_posicao(self):
        alvo = pygame.Vector2(self.jogador.rect.center)
        pos = pygame.Vector2(self.rect.center)
        diff = alvo - pos
        if diff.length() > 0:
            diff = diff.normalize()
        self.rect.x += diff.x * self.velocidade
        self.rect.y += diff.y * self.velocidade

class RoboTanque(Robo):
    """Lento, muito resistente, dá bastante xp."""
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=1.2, xp=50, vida=6,
                          cor=(110, 60, 60), tamanho=(60, 60), dano=2)

    def atualizar_posicao(self):
        self.rect.y += self.velocidade

class RoboKamikaze(Robo):

    def __init__(self, x, y, jogador):
        super().__init__(x, y, velocidade=4.2, xp=20, vida=1,
                          cor=(255, 90, 0), tamanho=(28, 28), dano=2)
        self.jogador = jogador
        self.pisca = 0

    def atualizar_posicao(self):
        alvo = pygame.Vector2(self.jogador.rect.center)
        pos = pygame.Vector2(self.rect.center)
        diff = alvo - pos
        if diff.length() > 0:
            diff = diff.normalize()
        self.rect.x += diff.x * self.velocidade
        self.rect.y += diff.y * self.velocidade

        self.pisca = (self.pisca + 1) % 20
        cor = (255, 255, 255) if self.pisca < 6 else (255, 90, 0)
        self.image.fill(cor)

class Boss(Robo):
    def __init__(self, x, y, jogador):
        super().__init__(x, y, velocidade=2.2, xp=300, vida=70,
                          cor=(180, 0, 0), tamanho=(110, 110), dano=2)
        self.jogador = jogador
        self.direcao_x = 1
        self.fase = "descendo"
        self.y_alvo = 110

    def atualizar_posicao(self):
        if self.fase == "descendo":
            self.rect.y += 3
            if self.rect.y >= self.y_alvo:
                self.rect.y = self.y_alvo
                self.fase = "lutando"
        else:
            self.rect.x += self.direcao_x * self.velocidade
            if self.rect.x <= 0 or self.rect.x >= LARGURA - self.rect.width:
                self.direcao_x *= -1

class Explosao(pygame.sprite.Sprite):
    """Área de dano temporária deixada pela explosão do Robô Kamikaze.

    Fica ativa por `duracao` quadros com um raio fixo (bem maior que o corpo
    do kamikaze), pegando o jogador mesmo que ele não tenha encostado
    diretamente no robô — por exemplo, se ele for destruído por uma arma
    perto demais do jogador.
    """
    def __init__(self, x, y, raio=85, duracao=16):
        super().__init__()
        self.raio = raio
        self.duracao = duracao
        self.tempo = 0
        self.image = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self._redesenhar()

    def _redesenhar(self):
        self.image.fill((0, 0, 0, 0))
        progresso = self.tempo / self.duracao
        alpha = max(0, 255 - int(progresso * 255))
        pygame.draw.circle(self.image, (255, 140, 0, alpha), (self.raio, self.raio), self.raio)
        pygame.draw.circle(self.image, (255, 235, 140, alpha), (self.raio, self.raio), int(self.raio * 0.55))

    def update(self):
        self.tempo += 1
        self._redesenhar()
        if self.tempo >= self.duracao:
            self.kill()
