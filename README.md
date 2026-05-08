# Codex Pong

Um pequeno jogo de Pong em Python usando `pygame`, agora com IA oponente, efeitos sonoros gerados dinamicamente e visual neon com partículas e trilhas.

## Como jogar
- Instale as dependências: `pip install pygame`.
- Execute o jogo: `python main.py`.
- Controles:
  - Jogador esquerdo: **W** e **S**.
  - **Espaço** alterna o modo IA para a raquete direita; quando desligado, controle-a com **Seta para cima/baixo**.
  - **Esc** fecha o jogo.
- O jogo termina quando alguém chega a 10 pontos; na tela final, **Espaço** reinicia ou **Esc** sai.

## Destaques visuais e sonoros
- Trilha luminosa e brilho em raquetes/bola para dar efeito neon.
- Partículas ao bater na raquete ou marcar ponto.
- Sons gerados em tempo de execução para batidas, paredes e pontos (não necessita arquivos de áudio externos).

## Tetris neon
- Execute o jogo: `python tetris.py` (é necessário `pygame`).
- Controles principais: setas para mover, **Z** ou seta para cima para rotacionar, **Espaço** para queda imediata e **R** para reiniciar.
- Para entender rapidamente como o código foi construído, veja o guia em PDF gerado pelo script `generate_tetris_pdf.py`:
  - Gere novamente se quiser: `python generate_tetris_pdf.py`.
  - O arquivo pronto fica em `tetris_guide.pdf`.
