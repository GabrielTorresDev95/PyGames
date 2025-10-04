Mini Roguelike — PgZero (sem pygame)

Um protótipo simples de jogo no PgZero que atende aos requisitos do projeto:

Bibliotecas usadas: apenas pgzero, math, random (sem pygame).

Gênero: Roguelike (top-down).

Menu: Start / Sound ON-OFF / Exit.

Música e sons: com fallback (se o arquivo não existir, o jogo não quebra).

Herói e inimigos com classes e animação (idle/walk).

Inimigos patrulham território e perseguem o herói.

Tiro: espaço ou clique esquerdo.

Vidas: a cada contato com inimigo conta 1 acerto; com 10 acertos → Game Over.

Vitória: ao eliminar todos os inimigos → Win.

Executando

Instale o PgZero (se ainda não tiver):

pip install pgzero


Rode o jogo:

pgzrun jogo.py


Windows/Erro de codificação: se aparecer UnicodeDecodeError (cp1252)
rode o comando no mesmo terminal antes:

set PYTHONUTF8=1
pgzrun jogo.py

Controles

Mover: WASD ou setas

Atirar: Espaço (atira para a direção do mouse) ou clique esquerdo

ESC: volta ao menu

Win: mata todas as caveiras

Game Over: ao levar 10 toques dos inimigos

Assets (opcional)

O jogo funciona sem imagens/sons (desenha formas e ignora áudio ausente).
Para ver animações e ouvir sons, crie as pastas e nomes abaixo:

images/
  hero_idle_0.png  hero_idle_1.png  hero_idle_2.png  hero_idle_3.png
  hero_walk_0.png  hero_walk_1.png  hero_walk_2.png  hero_walk_3.png
  enemy_idle_0.png enemy_idle_1.png enemy_idle_2.png enemy_idle_3.png
  enemy_walk_0.png enemy_walk_1.png enemy_walk_2.png enemy_walk_3.png

music/
  bgm.ogg

sounds/
  shoot.wav
  enemy_die.wav
  hit.wav
  game_over.wav
  win.wav


Dicas:

Tamanho sugerido: 32×32 px por frame (ou similar).

Se faltar qualquer arquivo, o jogo não quebra: mostra círculos e segue.

Estrutura

Projeto propositalmente simples (um arquivo):

jogo.py


Principais classes:

SpriteAnimator – alterna frames por FPS.

Entity – base para render/animação/dano.

Hero – movimento, tiro e cooldown.

Enemy – patrulha por território e perseguição.

Bullet – projétil com vida útil e colisão.

Estados do jogo:

menu → playing → win / gameover → (ENTER) volta ao menu.

Requisitos do trabalho — Checklist

 Somente PgZero, math, random (sem pygame).

 Gênero permitido (Roguelike).

 Menu com Start / Sound ON-OFF / Exit.

 Música e sons (com fallback).

 Vários inimigos perigosos.

 Inimigos se movem no seu território e perseguem o herói.

 Classes para movimento/animação.

 Herói e inimigos com animação (idle/walk).

 Nomes em inglês e estilo simples (PEP8).

 Mecânica lógica (vidas, vitória, derrota) e sem crashes conhecidos.

 Código único e autoral.

Parametrização rápida (opcional)

No topo do arquivo:

MAX_HITS = 10 → vidas do herói (número de toques até morrer).

Velocidades, raios de território e cooldowns podem ser ajustados em Hero/Enemy.

Solução de Problemas

Nada abre / fecha na hora: verifique erros no terminal após o banner do pygame (é normal aparecer o banner).

Erro de codificação no Windows: use set PYTHONUTF8=1 antes de rodar.

Sem sprites/sons: é normal ver círculos e silêncio; adicione os arquivos listados acima para visualizar/escutar.

Licença

Use e modifique livremente para fins educacionais/avaliativos.
Créditos de arte/música pertencem aos respectivos autores (se você usar assets de terceiros, cite-os aqui).

Próximos passos (ideias)

Corações gráficos no HUD.

Partículas de morte do inimigo.

Várias waves ou salas geradas (roguelike clássico).

Itens/power-ups (velocidade, spread de tiros etc.).
