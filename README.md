# Legião do Mal

Um shooter 2D estilo *survivors* (inspirado em Vampire Survivors), feito em Python com Pygame. Sobreviva a ondas de robôs, ganhe experiência e escolha como evoluir seu arsenal.

## Pré-requisitos

- Python 3.9+
- Pygame

Instalar o Pygame:

```bash
pip install pygame
```

## Como rodar

```bash
python legiao_do_mal.py
```

## Controles

| Tecla | Ação |
|---|---|
| `W` `A` `S` `D` | Mover o personagem |
| `1` `2` `3` | Escolher uma arma/upgrade na tela de nível |
| Clique do mouse | Também pode ser usado para escolher a arma/upgrade |

Não é preciso apertar nada para atirar — todas as armas disparam automaticamente.

## Como funciona

- **XP e Nível**: destruir robôs concede experiência. Ao encher a barra de XP, o jogador sobe de nível e o jogo pausa para você escolher uma nova arma, um upgrade de uma arma que já possui (até 8 níveis por arma), ou aumentar sua vida máxima.
- **Vida**: o jogador começa com 5 pontos de vida (mostrados como atual/máximo no HUD) e perde 1 a cada colisão com um inimigo ou explosão. Ao chegar a 0, é game over. A cada upgrade de "Vitalidade" escolhido na tela de nível, a vida máxima sobe e o jogador é curado na mesma quantidade.
- **Dificuldade progressiva**: o intervalo entre spawns normais diminui aos poucos com o tempo de jogo (os robôs vão aparecendo cada vez mais rápido).
- **Ondas especiais**: a cada 30 segundos chega uma rajada grande de inimigos de uma vez, com um aviso na tela ("ONDA X CHEGANDO!"). Cada onda traz mais inimigos que a anterior.

### Armas

| Arma | Comportamento |
|---|---|
| Espada Giratória | Golpe corpo a corpo: a lâmina varre um arco na direção para onde você está olhando, acertando todos os inimigos no caminho. Nos níveis mais altos o arco fica mais largo, o dano aumenta e surgem lâminas extras golpeando ao mesmo tempo em outros ângulos. |
| Rajada Tripla | Dispara vários tiros ao mesmo tempo em um leque mais amplo. |
| Laser Perfurante | Projétil rápido que atravessa vários inimigos sem ser destruído. |
| Orbe Girante | Um ou mais orbes giram continuamente ao redor do jogador, causando dano a quem tocar. |

### Inimigos

| Inimigo | Comportamento | Quando aparece |
|---|---|---|
| Robô Zigue-Zague | Desce quicando de um lado para o outro | Desde o início |
| Robô Reto | Desce rápido em linha reta, frágil | Desde o início |
| Robô Perseguidor | Persegue a posição do jogador | A partir de 5 pontos |
| Robô Kamikaze | Persegue rápido e pisca em branco/laranja como aviso; morre em 1 golpe, mas ao tocar o jogador (ou ser destruído por uma arma) explode, causando dano numa área bem maior que o seu corpo | A partir de 8 pontos |
| Robô Tanque | Lento, muito resistente (barra de vida visível), dá bastante XP | A partir de 15 pontos |

## Estrutura do código

- `Entidade`: classe base com posição e movimento.
- `Jogador`: controla movimento, vida, XP e as armas equipadas.
- `Tiro` / `Orbe` / `Espada`: projéteis e golpes usados pelas armas (a `Espada` varre um arco ao redor do jogador).
- `Explosao`: área de dano temporária deixada pelo Robô Kamikaze ao explodir.
- `Arma` (e subclasses `ArmaEspada`, `ArmaTripla`, `ArmaLaser`, `ArmaOrbital`): lógica de disparo e evolução de cada arma.
- `Robo` (e subclasses `RoboZigueZague`, `RoboReto`, `RoboPerseguidor`, `RoboKamikaze`, `RoboTanque`): comportamento de cada tipo de inimigo.
- Escolha de nível: além das armas, `gerar_opcoes`/`aplicar_escolha` também podem oferecer o upgrade de "Vitalidade" (+ vida máxima).
- Loop principal: spawn de inimigos, atualização de armas, colisões, HUD e a tela de escolha de arma ao subir de nível.

## Criadores do projeto 

- 'Raviel (João Felipe)'
- 'Christophe'
- 'Marcos Felipe'
- 'Tallys Rafael'
- 'Victor Gabriel'
- 'Apolo Gabriel'