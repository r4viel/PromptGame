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

- **XP e Nível**: destruir robôs concede experiência. Ao encher a barra de XP, o jogador sobe de nível e o jogo pausa para você escolher uma nova arma ou um upgrade de uma arma que já possui (até 8 níveis por arma).
- **Vida**: o jogador começa com 5 pontos de vida e perde 1 a cada colisão com um inimigo. Ao chegar a 0, é game over.

### Armas

| Arma | Comportamento |
|---|---|
| Tiro Reto | Dispara na última direção que você andou. Nos níveis mais altos, atira múltiplos projéteis em leque. |
| Rajada Tripla | Dispara vários tiros ao mesmo tempo em um leque mais amplo. |
| Laser Perfurante | Projétil rápido que atravessa vários inimigos sem ser destruído. |
| Orbe Girante | Um ou mais orbes giram continuamente ao redor do jogador, causando dano a quem tocar. |

### Inimigos

| Inimigo | Comportamento | Quando aparece |
|---|---|---|
| Robô Zigue-Zague | Desce quicando de um lado para o outro | Desde o início |
| Robô Reto | Desce rápido em linha reta, frágil | Desde o início |
| Robô Perseguidor | Persegue a posição do jogador | A partir de 5 pontos |
| Robô Tanque | Lento, muito resistente (barra de vida visível), dá bastante XP | A partir de 15 pontos |

## Estrutura do código

- `Entidade`: classe base com posição e movimento.
- `Jogador`: controla movimento, vida, XP e as armas equipadas.
- `Tiro` / `Orbe`: projéteis usados pelas armas.
- `Arma` (e subclasses `ArmaTiroReto`, `ArmaTripla`, `ArmaLaser`, `ArmaOrbital`): lógica de disparo e evolução de cada arma.
- `Robo` (e subclasses `RoboZigueZague`, `RoboReto`, `RoboPerseguidor`, `RoboTanque`): comportamento de cada tipo de inimigo.
- Loop principal: spawn de inimigos, atualização de armas, colisões, HUD e a tela de escolha de arma ao subir de nível.

## Criadores do projeto 

- 'Raviel (João Felipe)'
- 'Christophe'
- 'Marcos Felipe'
- 'Tallys Rafael'
- 'Victor Gabriel'
- 'Apolo Gabriel'
