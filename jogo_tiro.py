import pygame
import random
import math


from classes import (
    Entidade, Jogador, Tiro, Orbe, Espada,
    Arma, ArmaEspada, ArmaTripla, ArmaLaser, ArmaOrbital, TODAS_AS_ARMAS,
    Robo, RoboZigueZague, RoboReto, RoboPerseguidor, RoboTanque, RoboKamikaze,
    Boss, Explosao,
    LARGURA, ALTURA,
)

pygame.init()

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Legião do mal - Mecanica")

FPS = 60
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 30)
font_pequena = pygame.font.SysFont(None, 22)
font_titulo = pygame.font.SysFont(None, 46)
font_titulo_grande = pygame.font.SysFont(None, 70)

TEMPO_BOSS_MS = 7 * 60 * 1000


def criar_inimigo(pontos_atual, jogador):
    tipos = [RoboZigueZague, RoboReto]
    pesos = [3, 3]
    if pontos_atual >= 5:
        tipos.append(RoboPerseguidor)
        pesos.append(2)
    if pontos_atual >= 8:
        tipos.append(RoboKamikaze)
        pesos.append(2)
    if pontos_atual >= 15:
        tipos.append(RoboTanque)
        pesos.append(1)

    cls = random.choices(tipos, weights=pesos, k=1)[0]
    x = random.randint(40, LARGURA - 40)
    y = -40
    if cls is RoboPerseguidor or cls is RoboKamikaze:
        return cls(x, y, jogador)
    return cls(x, y)

def explodir_kamikaze(robo, todos_sprites, explosoes):
    """Cria a área de explosão na posição do kamikaze."""
    explosao = Explosao(robo.rect.centerx, robo.rect.centery)
    todos_sprites.add(explosao)
    explosoes.add(explosao)

def spawn_onda_especial(numero_onda, pontos_atual, jogador, todos_sprites, inimigos):
    """Cria uma rajada de inimigos de uma vez, ficando maior a cada onda."""
    quantidade = 5 + numero_onda * 2
    for i in range(quantidade):
        robo = criar_inimigo(pontos_atual, jogador)
        robo.rect.y -= random.randint(0, 220)
        todos_sprites.add(robo)
        inimigos.add(robo)
                                                  
VIDA_POR_UPGRADE = 2

def gerar_opcoes(jogador):
    candidatos = []
    for cls in TODAS_AS_ARMAS:
        nome_cls = cls.__name__
        if nome_cls in jogador.armas:
            arma = jogador.armas[nome_cls]
            if arma.nivel < arma.nivel_max:
                candidatos.append(("upar", nome_cls))
        else:
            candidatos.append(("nova", nome_cls))

    candidatos.append(("vida", "VidaMaxima"))

    random.shuffle(candidatos)
    return candidatos[:3]

def aplicar_escolha(opcao, jogador, todos_sprites, tiros):
    tipo, nome_cls = opcao

    if tipo == "vida":
        jogador.vida_maxima += VIDA_POR_UPGRADE
        jogador.vida = min(jogador.vida_maxima, jogador.vida + VIDA_POR_UPGRADE)
        return

    cls = {c.__name__: c for c in TODAS_AS_ARMAS}[nome_cls]

    if tipo == "nova":
        nova = cls()
        jogador.armas[nome_cls] = nova
        nova.ao_upar(jogador, todos_sprites, tiros)
    else:
        arma = jogador.armas[nome_cls]
        arma.upar()
        arma.ao_upar(jogador, todos_sprites, tiros)

def desenhar_tela_escolha(opcoes, jogador):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    TELA.blit(overlay, (0, 0))

    titulo = font_titulo.render(f"Nível {jogador.nivel}! Escolha um upgrade", True, (255, 255, 255))
    TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 60))

    caixas = []
    largura_caixa = 220
    altura_caixa = 260
    espaco = 30
    total_largura = len(opcoes) * largura_caixa + (len(opcoes) - 1) * espaco
    x_inicial = LARGURA // 2 - total_largura // 2
    y = ALTURA // 2 - altura_caixa // 2

    for i, (tipo, nome_cls) in enumerate(opcoes):
        x = x_inicial + i * (largura_caixa + espaco)
        rect = pygame.Rect(x, y, largura_caixa, altura_caixa)
        caixas.append(rect)

        if tipo == "vida":
            cor_fundo = (60, 30, 30)
        else:
            cor_fundo = (40, 40, 60) if tipo == "nova" else (40, 60, 40)
        pygame.draw.rect(TELA, cor_fundo, rect, border_radius=12)
        pygame.draw.rect(TELA, (255, 255, 255), rect, 3, border_radius=12)

        numero = font_titulo.render(str(i + 1), True, (255, 255, 0))
        TELA.blit(numero, (x + largura_caixa // 2 - numero.get_width() // 2, y + 10))

        if tipo == "vida":
            nome_txt = font.render("Vitalidade", True, (255, 255, 255))
            TELA.blit(nome_txt, (x + largura_caixa // 2 - nome_txt.get_width() // 2, y + 70))
            tag = font_pequena.render("VIDA MÁXIMA", True, (255, 150, 150))
            nivel_txt = font_pequena.render(
                f"{jogador.vida_maxima} -> {jogador.vida_maxima + VIDA_POR_UPGRADE}", True, (200, 200, 200))
        else:
            classe = {c.__name__: c for c in TODAS_AS_ARMAS}[nome_cls]
            nome_txt = font.render(classe.nome_arma, True, (255, 255, 255))
            TELA.blit(nome_txt, (x + largura_caixa // 2 - nome_txt.get_width() // 2, y + 70))

            if tipo == "nova":
                tag = font_pequena.render("NOVA ARMA", True, (150, 200, 255))
                nivel_txt = font_pequena.render("Nível 1", True, (200, 200, 200))
            else:
                arma_atual = jogador.armas[nome_cls]
                tag = font_pequena.render("MELHORAR", True, (150, 255, 150))
                nivel_txt = font_pequena.render(
                    f"Nível {arma_atual.nivel} -> {arma_atual.nivel + 1}", True, (200, 200, 200))

        TELA.blit(tag, (x + largura_caixa // 2 - tag.get_width() // 2, y + 110))
        TELA.blit(nivel_txt, (x + largura_caixa // 2 - nivel_txt.get_width() // 2, y + 140))

        dica = font_pequena.render("clique ou tecle " + str(i + 1), True, (170, 170, 170))
        TELA.blit(dica, (x + largura_caixa // 2 - dica.get_width() // 2, y + altura_caixa - 30))

    return caixas
                                              
def rect_botao(y, largura=300, altura=70):
    return pygame.Rect(LARGURA // 2 - largura // 2, y, largura, altura)

def rects_menu():
    return {
        "jogar": rect_botao(250),
        "creditos": rect_botao(340),
        "sair": rect_botao(430),
    }

def rects_pausado():
    return {
        "continuar": rect_botao(230),
        "menu": rect_botao(320),
        "sair": rect_botao(410),
    }

def rects_creditos():
    return {"voltar": rect_botao(500)}

def desenhar_botao(rect, texto):
    mouse_pos = pygame.mouse.get_pos()
    hover = rect.collidepoint(mouse_pos)
    cor_fundo = (100, 100, 150) if hover else (60, 60, 90)
    pygame.draw.rect(TELA, cor_fundo, rect, border_radius=10)
    pygame.draw.rect(TELA, (255, 255, 255), rect, 2, border_radius=10)
    txt = font.render(texto, True, (255, 255, 255))
    TELA.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

def desenhar_menu():
    TELA.fill((15, 15, 25))
    titulo = font_titulo_grande.render("LEGIÃO DO MAL", True, (255, 255, 255))
    TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 120))

    subtitulo = font_pequena.render("Sobreviva às ondas, evolua suas armas e derrote o chefe!",
                                     True, (170, 170, 200))
    TELA.blit(subtitulo, (LARGURA // 2 - subtitulo.get_width() // 2, 190))

    r = rects_menu()
    desenhar_botao(r["jogar"], "Jogar")
    desenhar_botao(r["creditos"], "Créditos")
    desenhar_botao(r["sair"], "Sair")
    return r

def desenhar_creditos(vitoria=False):
    TELA.fill((15, 15, 25))

    if vitoria:
        titulo = font_titulo_grande.render("VOCÊ VENCEU!", True, (255, 215, 0))
    else:
        titulo = font_titulo_grande.render("CRÉDITOS", True, (255, 255, 255))
    TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 60))

    linhas = []
    if vitoria:
        linhas.append("Você derrotou o chefe da Legião do Mal!")
        linhas.append("")
    linhas += [
        "Legião do Mal",
        "",
        "Desenvolvido em conjunto por:",
        "",
        "Raviel (João Felipe)",
        "Christophe",
        "Apolo",
        "Marcos",
        "Victor",
        "Tallys",
    ]

    y = 170
    for linha in linhas:
        if linha:
            txt = font.render(linha, True, (220, 220, 220))
            TELA.blit(txt, (LARGURA // 2 - txt.get_width() // 2, y))
        y += 34

    r = rects_creditos()
    desenhar_botao(r["voltar"], "Voltar ao Menu")
    return r

def desenhar_pausado():
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    TELA.blit(overlay, (0, 0))

    titulo = font_titulo.render("PAUSADO", True, (255, 255, 255))
    TELA.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 140))

    r = rects_pausado()
    desenhar_botao(r["continuar"], "Continuar (ESC)")
    desenhar_botao(r["menu"], "Sair para o Menu")
    desenhar_botao(r["sair"], "Sair do Jogo")
    return r
                      
def nova_partida():
    global jogador, todos_sprites, inimigos, tiros, explosoes
    global pontos, spawn_timer, tempo_inicio
    global numero_onda, banner_timer, banner_texto, banner_cor
    global boss_apareceu, boss_ativo
    global opcoes_atuais, caixas_opcoes

    todos_sprites = pygame.sprite.Group()
    inimigos = pygame.sprite.Group()
    tiros = pygame.sprite.Group()
    explosoes = pygame.sprite.Group()

    jogador = Jogador(LARGURA // 2, ALTURA - 60)
    todos_sprites.add(jogador)

    arma_inicial = ArmaEspada()
    jogador.armas[ArmaEspada.__name__] = arma_inicial
    arma_inicial.ao_upar(jogador, todos_sprites, tiros)

    pontos = 0
    spawn_timer = 0
    tempo_inicio = pygame.time.get_ticks()

    numero_onda = 0
    banner_timer = 0
    banner_texto = ""
    banner_cor = (255, 60, 60)

    boss_apareceu = False
    boss_ativo = False

    opcoes_atuais = []
    caixas_opcoes = []


INTERVALO_ONDA_MS = 30000
DURACAO_BANNER = FPS * 3
SPAWN_INTERVALO_MIN = 12
SPAWN_INTERVALO_INICIAL = 40

nova_partida()
estado = "menu"                                                              
vitoria = False                                                                        

rects_menu_atual = {}
rects_pausado_atual = {}
rects_creditos_atual = {}

rodando = True
while rodando:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
                                                
        if estado == "menu" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rects_menu_atual.get("jogar") and rects_menu_atual["jogar"].collidepoint(event.pos):
                nova_partida()
                vitoria = False
                estado = "jogando"
            elif rects_menu_atual.get("creditos") and rects_menu_atual["creditos"].collidepoint(event.pos):
                estado = "creditos"
            elif rects_menu_atual.get("sair") and rects_menu_atual["sair"].collidepoint(event.pos):
                rodando = False
                                                    
        elif estado == "creditos" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rects_creditos_atual.get("voltar") and rects_creditos_atual["voltar"].collidepoint(event.pos):
                estado = "menu"
                                                   
        elif estado == "jogando" and event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            estado = "pausado"
                                                   
        elif estado == "pausado":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                estado = "jogando"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if rects_pausado_atual.get("continuar") and rects_pausado_atual["continuar"].collidepoint(event.pos):
                    estado = "jogando"
                elif rects_pausado_atual.get("menu") and rects_pausado_atual["menu"].collidepoint(event.pos):
                    estado = "menu"
                elif rects_pausado_atual.get("sair") and rects_pausado_atual["sair"].collidepoint(event.pos):
                    rodando = False
                                                           
        elif estado == "escolhendo":
            escolhido = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 and len(opcoes_atuais) > 0:
                    escolhido = 0
                elif event.key == pygame.K_2 and len(opcoes_atuais) > 1:
                    escolhido = 1
                elif event.key == pygame.K_3 and len(opcoes_atuais) > 2:
                    escolhido = 2
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, caixa in enumerate(caixas_opcoes):
                    if caixa.collidepoint(event.pos):
                        escolhido = i
                        break

            if escolhido is not None:
                aplicar_escolha(opcoes_atuais[escolhido], jogador, todos_sprites, tiros)
                if jogador.level_ups_pendentes > 0:
                    jogador.level_ups_pendentes -= 1

                if jogador.level_ups_pendentes > 0:
                    opcoes_atuais = gerar_opcoes(jogador)
                    if not opcoes_atuais:
                        estado = "jogando"
                    caixas_opcoes = []
                else:
                    estado = "jogando"
       
    if estado == "jogando":
        tempo_ms_atual = pygame.time.get_ticks() - tempo_inicio
        segundos_totais_atual = tempo_ms_atual // 1000

        if not boss_ativo:
                                                                    
            spawn_intervalo = max(SPAWN_INTERVALO_MIN,
                                   SPAWN_INTERVALO_INICIAL - segundos_totais_atual // 8)
            spawn_timer += 1
            if spawn_timer > spawn_intervalo:
                robo = criar_inimigo(pontos, jogador)
                todos_sprites.add(robo)
                inimigos.add(robo)
                spawn_timer = 0
                           
            if tempo_ms_atual >= (numero_onda + 1) * INTERVALO_ONDA_MS:
                numero_onda += 1
                banner_timer = DURACAO_BANNER
                banner_texto = f"ONDA {numero_onda} CHEGANDO!"
                banner_cor = (255, 60, 60)
                spawn_onda_especial(numero_onda, pontos, jogador, todos_sprites, inimigos)
                                      
        if not boss_apareceu and tempo_ms_atual >= TEMPO_BOSS_MS:
            boss_apareceu = True
            boss_ativo = True
            banner_timer = DURACAO_BANNER
            banner_texto = "O CHEFE CHEGOU!"
            banner_cor = (255, 215, 0)
            chefe = Boss(LARGURA // 2, -80, jogador)
            todos_sprites.add(chefe)
            inimigos.add(chefe)

        if banner_timer > 0:
            banner_timer -= 1
                                          
        for arma in jogador.armas.values():
            arma.update(jogador, todos_sprites, tiros, inimigos)
                                                     
        for tiro in list(tiros):
            atingidos = pygame.sprite.spritecollide(tiro, inimigos, False)
            for robo in atingidos:
                rid = id(robo)
                if tiro.perfurante or tiro.persistente:
                    if tiro.atingidos.get(rid, 0) > 0:
                        continue
                    tiro.atingidos[rid] = 25 if tiro.persistente else 1
                else:
                    tiro.atingidos[rid] = 1

                robo.vida -= tiro.dano
                if robo.vida <= 0:
                    pontos += 1
                    jogador.ganhar_xp(robo.xp)
                    era_chefe = isinstance(robo, Boss)
                    if isinstance(robo, RoboKamikaze):
                        explodir_kamikaze(robo, todos_sprites, explosoes)
                    robo.kill()
                    if era_chefe:
                        boss_ativo = False
                        vitoria = True
                        estado = "creditos"

                if not tiro.perfurante and not tiro.persistente:
                    tiro.kill()
                    break

            if tiro.persistente:
                for rid in list(tiro.atingidos.keys()):
                    tiro.atingidos[rid] -= 1
                    if tiro.atingidos[rid] <= 0:
                        del tiro.atingidos[rid]
                                                                              
        colididos = pygame.sprite.spritecollide(jogador, inimigos, False)
        if colididos:
            if jogador.dano_cooldown <= 0:
                jogador.vida -= 1
                jogador.dano_cooldown = FPS
            for robo in colididos:
                if isinstance(robo, RoboKamikaze):
                    explodir_kamikaze(robo, todos_sprites, explosoes)
                if not isinstance(robo, Boss):
                    robo.kill()

        if pygame.sprite.spritecollide(jogador, explosoes, False):
            if jogador.dano_cooldown <= 0:
                jogador.vida -= 1
                jogador.dano_cooldown = FPS

        if jogador.vida <= 0:
            print("GAME OVER!")
            vitoria = False
            estado = "menu"

                                                                           
        if estado == "jogando":
            todos_sprites.update()

            if jogador.level_ups_pendentes > 0:
                opcoes_atuais = gerar_opcoes(jogador)
                if opcoes_atuais:
                    estado = "escolhendo"
                    jogador.level_ups_pendentes -= 1
                else:
                    jogador.level_ups_pendentes = 0
                                          
    if estado == "menu":
        rects_menu_atual = desenhar_menu()

    elif estado == "creditos":
        rects_creditos_atual = desenhar_creditos(vitoria)

    else:
                                                                                
        TELA.fill((20, 20, 20))
        todos_sprites.draw(TELA)

        for robo in inimigos:
            if robo.vida_max > 1:
                largura_barra = robo.rect.width
                pygame.draw.rect(TELA, (80, 0, 0), (robo.rect.x, robo.rect.y - 8, largura_barra, 5))
                pygame.draw.rect(TELA, (0, 255, 0),
                                  (robo.rect.x, robo.rect.y - 8,
                                   largura_barra * (robo.vida / robo.vida_max), 5))

        texto = font.render(
            f"Vida: {jogador.vida}/{jogador.vida_maxima}  |  Pontos: {pontos}  |  Nivel: {jogador.nivel}",
            True, (255, 255, 255))
        TELA.blit(texto, (10, 10))

        y_arma = 40
        for arma in jogador.armas.values():
            txt_arma = font_pequena.render(arma.descricao(), True, (200, 220, 255))
            TELA.blit(txt_arma, (10, y_arma))
            y_arma += 20

        tempo_ms = pygame.time.get_ticks() - tempo_inicio
        segundos_totais = tempo_ms // 1000
        minutos = segundos_totais // 60
        segundos = segundos_totais % 60
        texto_tempo = font.render(f"{minutos:02}:{segundos:02}", True, (255, 255, 255))
        TELA.blit(texto_tempo, (LARGURA - texto_tempo.get_width() - 10, 10))

        barra_largura = LARGURA - 20
        barra_altura = 20
        barra_x = 10
        barra_y = ALTURA - barra_altura - 10

        proporcao = jogador.xp / jogador.xp_necessario
        proporcao = max(0, min(proporcao, 1))

        pygame.draw.rect(TELA, (60, 60, 60), (barra_x, barra_y, barra_largura, barra_altura))
        pygame.draw.rect(TELA, (0, 150, 255), (barra_x, barra_y, barra_largura * proporcao, barra_altura))
        pygame.draw.rect(TELA, (255, 255, 255), (barra_x, barra_y, barra_largura, barra_altura), 2)

        texto_xp = font.render(f"XP: {jogador.xp} / {jogador.xp_necessario}", True, (255, 255, 255))
        TELA.blit(texto_xp, (barra_x + barra_largura // 2 - texto_xp.get_width() // 2, barra_y - 2))

        if banner_timer > 0:
            alpha = min(255, banner_timer * 4)
            texto_banner = font_titulo.render(banner_texto, True, banner_cor)
            texto_banner.set_alpha(alpha)
            TELA.blit(texto_banner, (LARGURA // 2 - texto_banner.get_width() // 2, 120))

        if estado == "escolhendo":
            caixas_opcoes = desenhar_tela_escolha(opcoes_atuais, jogador)
        elif estado == "pausado":
            rects_pausado_atual = desenhar_pausado()

    pygame.display.flip()
