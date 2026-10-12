"""Classes do jogo (entidades, projéteis, armas e inimigos)."""
import os
import pygame
import random
import math

# Constantes de tela usadas pelas classes (mantidas em sincronia com jogo_tiro.py,
# que atualiza LARGURA/ALTURA a cada frame caso a janela seja redimensionada)
LARGURA = 1200
ALTURA = 900

# Pasta onde este arquivo está localizado. Usar isso (em vez de nomes de
# arquivo "soltos") evita o bug de FileNotFoundError quando o jogo é
# executado a partir de outra pasta (outro diretório de trabalho atual).
PASTA_JOGO = os.path.dirname(os.path.abspath(__file__))


def caminho_imagem(nome_arquivo):
    """Monta o caminho absoluto de uma imagem que fica na pasta Img."""
    return os.path.join(PASTA_JOGO, 'Img', nome_arquivo)


_FRAMES_PODER = {}
_FRAMES_TRIPLO = None


def carregar_frames_poder(prefixo, quantidade):
    """Carrega e armazena em cache os quadros de uma animação de poder."""
    chave = (prefixo, quantidade)
    if chave not in _FRAMES_PODER:
        frames = []
        for indice in range(quantidade):
            caminho = caminho_imagem(
                os.path.join("Poderes", f"{prefixo}_{indice}.png")
            )
            frames.append(pygame.image.load(caminho).convert_alpha())
        _FRAMES_PODER[chave] = tuple(frames)
    return _FRAMES_PODER[chave]


def recortar_projetil_triplo(frame, indice):
    """Mantém o projétil principal e remove fragmentos fora do corpo."""
    mascara = pygame.mask.from_surface(frame)
    componentes = mascara.connected_components()
    if not componentes:
        raise ValueError(f"Quadro vazio na animação da rajada tripla: {indice}")

    maior_area = max(componente.count() for componente in componentes)
    candidatos = [
        componente for componente in componentes
        if componente.count() >= maior_area * 0.75
    ]
    if indice == 0 and len(candidatos) > 1:
        principal = max(
            candidatos,
            key=lambda componente: componente.get_bounding_rects()[0].centerx,
        )
    else:
        principal = max(candidatos, key=lambda componente: componente.count())

    limites = principal.get_bounding_rects()[0]
    mascara_local = pygame.mask.Mask((limites.width, limites.height))
    for x in range(limites.width):
        for y in range(limites.height):
            if principal.get_at((x + limites.x, y + limites.y)):
                mascara_local.set_at((x, y))
    recorte = frame.subsurface(limites).copy()
    return mascara_local.to_surface(
        surface=recorte,
        setcolor=None,
        unsetcolor=(0, 0, 0, 0),
    )


def carregar_frames_triplo():
    """Devolve quadros recortados, sem repetir o trabalho por projétil."""
    global _FRAMES_TRIPLO
    if _FRAMES_TRIPLO is None:
        originais = carregar_frames_poder("triplo", 9)
        _FRAMES_TRIPLO = tuple(
            recortar_projetil_triplo(frame, indice)
            for indice, frame in enumerate(originais[:7])
        )
    return _FRAMES_TRIPLO


POSES_ESPADA = 5
OMBRO = (90, 64)
FOLHAS_ESPADA = [
    ("Ataque_espada_combinado_1.png", (107, 17)),
    ("Ataque_espada_combinado_2.png", (133, 46)),
    ("Ataque_espada_combinado_3.png", (163, 79)),
]

_cache_quadros_espada = {}
_cache_imagens_espada = {}


def _quadros_espada(tier, espelhado):
    """Retorna poses do golpe combinado e o pivô do ombro em cada pose."""
    chave = (tier, espelhado)
    if chave not in _cache_quadros_espada:
        arquivo, origem = FOLHAS_ESPADA[tier]
        folha = pygame.image.load(caminho_imagem(arquivo)).convert_alpha()
        largura = folha.get_width() // POSES_ESPADA
        quadros = [
            folha.subsurface(
                (indice * largura, 0, largura, folha.get_height())
            ).copy()
            for indice in range(POSES_ESPADA)
        ]
        pivo_x = origem[0] + OMBRO[0] * 2
        pivo_y = origem[1] + OMBRO[1] * 2
        if espelhado:
            quadros = [pygame.transform.flip(q, True, False) for q in quadros]
            pivo_x = largura - pivo_x
        _cache_quadros_espada[chave] = (quadros, (pivo_x, pivo_y))
    return _cache_quadros_espada[chave]


def _girar_em_torno(imagem, pivo, angulo):
    """Gira uma imagem e calcula onde ficou o pivô após a rotação."""
    girada = pygame.transform.rotate(imagem, angulo)
    centro_original = pygame.Vector2(imagem.get_size()) / 2
    deslocamento = pygame.Vector2(pivo) - centro_original
    angulo_rad = math.radians(angulo)
    deslocamento_girado = pygame.Vector2(
        deslocamento.x * math.cos(angulo_rad)
        + deslocamento.y * math.sin(angulo_rad),
        -deslocamento.x * math.sin(angulo_rad)
        + deslocamento.y * math.cos(angulo_rad),
    )
    novo_pivo = pygame.Vector2(girada.get_size()) / 2 + deslocamento_girado
    return girada, (novo_pivo.x, novo_pivo.y)


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

        folha = pygame.image.load(
            caminho_imagem("Protagonista.png")
        ).convert_alpha()

        self.frames = []
        self.frame_bounds = []
        for i in range(16):
            frame = folha.subsurface((i * 128, 0, 128, 128)).copy()
            bbox = frame.get_bounding_rect()

            if bbox.width > 0 and bbox.height > 0:
                frame = frame.subsurface(bbox).copy()

            self.frame_bounds.append(bbox)
            frame = pygame.transform.scale(
                frame,
                (frame.get_width() * 2, frame.get_height() * 2)
            )
            self.frames.append(frame)

        self.frame_atual = 0
        self.animacao_timer = 0
        self.esta_movendo = False
        self.virado_esquerda = False
        self.ataque_espada_ativo = False
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.vida = 5
        self.vida_maxima = 5
        self.ultima_direcao = pygame.Vector2(0, -1)
        self.dano_cooldown = 0
        self.nivel = 1
        self.xp_necessario = 100
        self.level_ups_pendentes = 0
        self.armas = {}

    def origem_canvas(self):
        """Retorna o canto do canvas 128x128 não recortado na tela."""
        bbox = self.frame_bounds[self.frame_atual]
        if self.virado_esquerda:
            offset_x = 128 - bbox.right
        else:
            offset_x = bbox.left
        return (
            self.rect.left - offset_x * 2,
            self.rect.top - bbox.top * 2,
        )

    def ganhar_xp(self, quantidade):
        self.xp += quantidade
        while self.xp >= self.xp_necessario:
            self.xp -= self.xp_necessario
            self.nivel += 1
            self.xp_necessario += 50
            self.level_ups_pendentes += 1

    def _animar(self, direcao):
        self.esta_movendo = direcao.length_squared() > 0

        if self.esta_movendo:
            if direcao.x != 0:
                self.virado_esquerda = direcao.x < 0

            self.animacao_timer += 1
            if self.animacao_timer >= 5:
                self.animacao_timer = 0
                self.frame_atual = (self.frame_atual + 1) % len(self.frames)

        frame = self.frames[self.frame_atual]
        if self.virado_esquerda:
            frame = pygame.transform.flip(frame, True, False)

        centro = self.rect.center
        self.image = frame
        self.rect = self.image.get_rect(center=centro)

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

        self._animar(direcao)

        if self.ataque_espada_ativo:
            centro = self.rect.center
            self.image = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            self.rect = self.image.get_rect(center=centro)

        if self.dano_cooldown > 0:
            self.dano_cooldown -= 1



    
                                
class Tiro(Entidade):
    def __init__(self, x, y, direcao, dano=1, velocidade=10,
                 perfurante=False, persistente=False,
                 cor=(255, 255, 0), tamanho=(10, 10)):
        super().__init__(x, y, velocidade, xp=0)
        self.direcao = direcao
        self.dano = dano
        self.perfurante = perfurante
        self.persistente = persistente
        self.atingidos = {}                                               
        self.tipo_sprite = None
        self.tipo_impacto = "triplo"
        self.frames = ()
        self.frame_atual = 0
        self.animacao_timer = 0
        self.escala_sprite = 1.0

        if cor[0] > 200 and 60 < cor[1] < 210:
            self.tipo_sprite = "triplo"
            self.tipo_impacto = "triplo"
            self.frames = carregar_frames_triplo()
            self.frame_atual = 0
            escala = 0.48
        elif cor[0] > 200 and cor[2] > 150:
            self.tipo_sprite = "laser"
            self.tipo_impacto = "laser"
            self.frames = carregar_frames_poder("laser", 6)
            self.frame_atual = 2
            escala = 0.34
        else:
            escala = self.escala_sprite

        if self.frames:
            self.image = self._imagem_frame(escala)
        else:
            self.image = pygame.Surface(tamanho, pygame.SRCALPHA)
            pygame.draw.circle(
                self.image,
                cor,
                (tamanho[0] // 2, tamanho[1] // 2),
                max(2, min(tamanho) // 2),
            )
        self.rect = self.image.get_rect(center=(x, y))
        self.escala_sprite = escala

    def _imagem_frame(self, escala=None):
        if escala is None:
            escala = self.escala_sprite
        base = self.frames[self.frame_atual]
        tamanho_sprite = (
            max(1, int(base.get_width() * escala)),
            max(1, int(base.get_height() * escala)),
        )
        base = pygame.transform.scale(base, tamanho_sprite)
        angulo = -math.degrees(math.atan2(self.direcao.y, self.direcao.x))
        return pygame.transform.rotate(base, angulo)

    def update(self):
        self.rect.x += self.direcao.x * self.velocidade
        self.rect.y += self.direcao.y * self.velocidade

        if self.frames:
            self.animacao_timer += 1
            intervalo = 3 if self.tipo_sprite == "triplo" else 2
            if self.animacao_timer >= intervalo:
                self.animacao_timer = 0
                if self.tipo_sprite == "triplo" and self.frame_atual >= 2:
                    self.frame_atual = 2 + (self.frame_atual - 1) % 5
                else:
                    self.frame_atual = (self.frame_atual + 1) % len(self.frames)
                centro = self.rect.center
                self.image = self._imagem_frame()
                self.rect = self.image.get_rect(center=centro)

        if not self.persistente:
            if (self.rect.bottom < 0 or self.rect.top > ALTURA or
                    self.rect.right < 0 or self.rect.left > LARGURA):
                self.kill()
                                      
class Orbe(pygame.sprite.Sprite):
    def __init__(self, jogador, angulo_offset, raio, dano):
        super().__init__()
        frames = carregar_frames_poder("orbe", 8)
        self.frames = tuple(
            pygame.transform.scale(frame, (44, 44)) for frame in frames
        )
        self.frame_atual = 0
        self.image = self.frames[self.frame_atual]
        self.rect = self.image.get_rect(center=jogador.rect.center)
        self.jogador = jogador
        self.angulo_offset = angulo_offset
        self.raio = raio
        self.dano = dano
        self.perfurante = True
        self.persistente = True
        self.atingidos = {}
        self.angulo_global = 0
        self.tipo_impacto = "orbe"

    def update(self):
        self.angulo_global = (self.angulo_global + 3) % 360
        self.frame_atual = (self.frame_atual + 1) % len(self.frames)
        centro_anterior = self.rect.center
        self.image = self.frames[self.frame_atual]
        self.rect = self.image.get_rect(center=centro_anterior)
        ang = math.radians(self.angulo_global + self.angulo_offset)
        cx, cy = self.jogador.rect.center
        self.rect.centerx = cx + math.cos(ang) * self.raio
        self.rect.centery = cy + math.sin(ang) * self.raio


class Impacto(pygame.sprite.Sprite):
    """Anima o efeito visual quando um projétil acerta um inimigo."""
    def __init__(self, centro, tipo="triplo"):
        super().__init__()
        prefixo = {
            "laser": "impacto_laser",
            "orbe": "impacto_orbe",
        }.get(tipo, "impacto_triplo")
        quantidade = 4 if tipo == "orbe" else 5
        self.frames = carregar_frames_poder(prefixo, quantidade)
        self.indice = 0
        self.timer = 0
        self.image = pygame.transform.scale(self.frames[0], (48, 48))
        self.rect = self.image.get_rect(center=centro)

    def update(self):
        self.timer += 1
        if self.timer % 3 == 0:
            self.indice += 1
            if self.indice >= len(self.frames):
                self.kill()
                return
            centro = self.rect.center
            self.image = pygame.transform.scale(
                self.frames[self.indice], (48, 48)
            )
            self.rect = self.image.get_rect(center=centro)
                                       
class Espada(pygame.sprite.Sprite):
    def __init__(self, jogador, dano, raio, duracao, angulo_arco,
                 angulo_inicial, tier=0, angulo_mira=0):
        super().__init__()
        self.jogador = jogador
        self.dano = dano
        self.raio = raio
        self.duracao = duracao
        self.tempo = 0
        self.angulo_arco = angulo_arco
        self.angulo_inicial = angulo_inicial
        self.angulo_mira = angulo_mira
        self.tier = max(0, min(tier, len(FOLHAS_ESPADA) - 1))
        self.perfurante = True
        self.persistente = False
        self.atingidos = {}
        self.mask = pygame.mask.Mask((1, 1))
        self.jogador.ataque_espada_ativo = True
        self._montar()

    def _montar(self):
        pose = min(
            POSES_ESPADA - 1,
            int(self.tempo / max(1, self.duracao) * POSES_ESPADA),
        )
        espelhado = not self.jogador.virado_esquerda
        quadros, pivo = _quadros_espada(self.tier, espelhado)

        referencia = 0 if espelhado else 180
        delta = int(round(
            (self.angulo_mira - referencia + 180) % 360 - 180
        ))
        chave = (self.tier, espelhado, pose, delta)
        if chave not in _cache_imagens_espada:
            imagem, novo_pivo = _girar_em_torno(quadros[pose], pivo, delta)
            mascara = pygame.mask.from_surface(imagem, 127)
            _cache_imagens_espada[chave] = (imagem, novo_pivo, mascara)
        imagem, novo_pivo, mascara = _cache_imagens_espada[chave]

        origem_x, origem_y = self.jogador.origem_canvas()
        ombro_x = origem_x + (
            128 - OMBRO[0] if espelhado else OMBRO[0]
        ) * 2
        ombro_y = origem_y + OMBRO[1] * 2

        self.image = imagem
        self.mask = mascara
        self.rect = imagem.get_rect(
            topleft=(
                round(ombro_x - novo_pivo[0]),
                round(ombro_y - novo_pivo[1]),
            )
        )

    def update(self):
        self.tempo += 1
        self._montar()

        if self.tempo >= self.duracao:
            self.kill()

    def kill(self):
        super().kill()
        self.jogador.ataque_espada_ativo = False

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

    def update(self, jogador, todos_sprites, tiros, inimigos):
        self.timer -= 1
        if self.timer > 0:
            return

        # A arma atualiza antes do grupo de sprites remover golpes expirados.
        # Aguarda a remoção para não desenhar dois golpes sobrepostos.
        if any(isinstance(tiro, Espada) for tiro in tiros):
            return

        self.disparar(jogador, todos_sprites, tiros, inimigos)
        self.timer = self.cooldown()

    def disparar(self, jogador, todos_sprites, tiros, inimigos):
        dano = 2 + self.nivel
        raio = 50 + self.nivel * 9      
        duracao = 14
        arco = 130 + self.nivel * 4

        dir_v = jogador.ultima_direcao
        angulo_base = math.degrees(math.atan2(dir_v.y, dir_v.x))
        angulo_inicial = angulo_base - arco / 2

        espada = Espada(jogador, dano=dano, raio=raio, duracao=duracao,
                        angulo_arco=arco, angulo_inicial=angulo_inicial,
                        tier=min(2, (self.nivel - 1) // 3),
                        angulo_mira=angulo_base)
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
                     dano=dano, velocidade=9, cor=(255, 150, 0))
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
                  cor=(255, 0, 255))
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

        # Direção de entrada: aponta do ponto de spawn (que fica fora da
        # tela, em qualquer uma das 4 bordas) para o centro da tela. Assim
        # os inimigos que só "descem" (Zumbi, Esqueleto, Tanque, Slime)
        # conseguem vir de cima, de baixo, da esquerda ou da direita sem
        # precisar de nenhuma lógica extra em cada classe.
        centro = pygame.Vector2(LARGURA / 2, ALTURA / 2)
        direcao = centro - pygame.Vector2(x, y)
        if direcao.length() > 0:
            direcao = direcao.normalize()
        else:
            direcao = pygame.Vector2(0, 1)
        self.direcao_entrada = direcao

    def atualizar_posicao(self):
        raise NotImplementedError

    def update(self):
        self.atualizar_posicao()
        margem = 80
        if (self.rect.right < -margem or self.rect.left > LARGURA + margem or
                self.rect.bottom < -margem or self.rect.top > ALTURA + margem):
            self.kill()

class RoboZigueZague(Robo):
    """Anda em zigue-zague vindo de qualquer borda da tela em direção ao centro."""
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=3, xp=15, vida=1,
                          cor=(255, 0, 0), tamanho=(9 * 3, 8 * 3), dano=1)

        folha = pygame.image.load(caminho_imagem('Slime.png')).convert_alpha()

        self.framesS = list()
        for i in range(3):
            frameS = folha.subsurface((i * 32, 0, 32, 32))
            frameS = pygame.transform.scale(frameS, (32 * 3, 32 * 3))
            self.framesS.append(frameS)

        self.parteS = 0
        self.contadorS = 0
        self.fase_zigue = random.uniform(0, math.tau)

        # Usa o primeiro frame já recortado (em vez da folha de sprites
        # inteira) e recria o rect no tamanho real da imagem, para o
        # hitbox de colisão bater com o desenho na tela.
        self.image = self.framesS[self.parteS]
        self.rect = self.image.get_rect(center=(x, y))

    def atualizar_posicao(self):
        # Avança na direção de entrada e balança de um lado para o outro
        # perpendicularmente a ela (zigue-zague), funcionando não importa
        # de qual borda o inimigo veio.
        self.fase_zigue += 0.15
        perp = pygame.Vector2(-self.direcao_entrada.y, self.direcao_entrada.x)
        balanco = perp * math.sin(self.fase_zigue) * 3
        self.rect.x += self.direcao_entrada.x * self.velocidade + balanco.x
        self.rect.y += self.direcao_entrada.y * self.velocidade + balanco.y

        self.contadorS += 1
        if self.contadorS >= 10:
            self.contadorS = 0
            self.parteS = (self.parteS + 1) % 3
            self.image = self.framesS[self.parteS]

class Zumbi(Robo):
  
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=5, xp=10, vida=1,
                          cor=(255, 140, 0), tamanho=(58, 36), dano=1)

        folha = pygame.image.load(caminho_imagem('Zumbi.png')).convert_alpha()

        self.framesZ = []
        for i in range(24):
            frameZ = folha.subsurface((i * 64, 0, 64, 64))
            frameZ = pygame.transform.scale(frameZ, (64 * 2, 64 * 2))
            self.framesZ.append(frameZ)

        self.parteZ = 0

        # Mesma correção do Slime: começa já no frame recortado e ajusta
        # o rect para o tamanho real da imagem (a imagem original informada
        # ao Robo.__init__ era só um placeholder menor que o sprite real).
        self.image = self.framesZ[self.parteZ]
        self.rect = self.image.get_rect(center=(x, y))

    def atualizar_posicao(self):
        self.rect.x += self.direcao_entrada.x * self.velocidade
        self.rect.y += self.direcao_entrada.y * self.velocidade

        self.parteZ = (self.parteZ + 1) % 24

        self.image = self.framesZ[self.parteZ]

class Esqueleto(Robo):
    """Anda vindo de qualquer borda da tela em direção ao centro."""
    def __init__(self, x, y):
        super().__init__(x, y, velocidade=3.6, xp=18, vida=2,
                          cor=(210, 210, 190), tamanho=(50, 50), dano=1)

        folha = pygame.image.load(caminho_imagem('Esqueleto.png')).convert_alpha()

        self.framesE = []
        for i in range(16):
            frameE = folha.subsurface((i * 64, 0, 64, 64))
            frameE = pygame.transform.scale(frameE, (64 * 2, 64 * 2))
            self.framesE.append(frameE)

        self.parteE = 0
        self.contadorE = 0

        self.image = self.framesE[self.parteE]
        self.rect = self.image.get_rect(center=(x, y))

    def atualizar_posicao(self):
        self.rect.x += self.direcao_entrada.x * self.velocidade
        self.rect.y += self.direcao_entrada.y * self.velocidade

        self.contadorE += 1
        if self.contadorE >= 6:
            self.contadorE = 0
            self.parteE = (self.parteE + 1) % 16
            self.image = self.framesE[self.parteE]

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
        self.rect.x += self.direcao_entrada.x * self.velocidade
        self.rect.y += self.direcao_entrada.y * self.velocidade

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
    def __init__(self, x, y, raio=67, duracao=16):
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
