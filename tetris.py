import math
import random
import pygame

# Game constants
WIDTH, HEIGHT = 600, 780
PLAY_WIDTH, PLAY_HEIGHT = 10, 20
BLOCK_SIZE = 30
GRID_OFFSET_X = 60
GRID_OFFSET_Y = 80

FPS = 60
GRAVITY_DELAY = 700  # milliseconds between automatic drops
SOFT_DROP_DELAY = 40
HARD_DROP_BONUS = 2
LINE_CLEAR_SCORE = (100, 300, 500, 800)

# Tetromino definitions (rotation states)
SHAPES = {
    "I": [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)]],
    "J": [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
    "L": [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)], [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
    "O": [[(1, 0), (2, 0), (1, 1), (2, 1)]],
    "S": [[(1, 1), (2, 1), (0, 2), (1, 2)], [(1, 0), (1, 1), (2, 1), (2, 2)]],
    "T": [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
    "Z": [[(0, 1), (1, 1), (1, 2), (2, 2)], [(2, 0), (1, 1), (2, 1), (1, 2)]],
}

COLORS = {
    "I": (89, 215, 255),
    "J": (56, 118, 255),
    "L": (255, 184, 79),
    "O": (255, 239, 94),
    "S": (93, 255, 182),
    "T": (208, 116, 255),
    "Z": (255, 114, 138),
}


class Particle:
    def __init__(self, pos, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(0.5, 2.2)
        self.pos = list(pos)
        self.vel = [math.cos(angle) * speed, math.sin(angle) * speed - 1]
        self.life = random.randint(15, 30)
        self.color = color

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.vel[1] += 0.04
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = max(10, min(255, self.life * 8))
            glow = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color, alpha), (3, 3), 3)
            surface.blit(glow, (self.pos[0] - 3, self.pos[1] - 3))


class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.rotation = 0
        self.position = [3, -1]
        self.color = COLORS[shape]

    def blocks(self):
        return SHAPES[self.shape][self.rotation]

    def rotated(self, direction=1):
        rotations = len(SHAPES[self.shape])
        rotated_piece = Tetromino(self.shape)
        rotated_piece.rotation = (self.rotation + direction) % rotations
        rotated_piece.position = self.position.copy()
        return rotated_piece


class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris Glow")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.grid = [[None for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]
        self.current = self._new_piece()
        self.next_piece = self._new_piece()
        self.drop_timer = 0
        self.soft_drop = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.particles = []
        self.font = pygame.font.SysFont("Poppins", 26)
        self.big_font = pygame.font.SysFont("Poppins", 48, bold=True)

    def _new_piece(self):
        return Tetromino(random.choice(list(SHAPES)))

    def _valid_position(self, piece):
        for x, y in piece.blocks():
            px = piece.position[0] + x
            py = piece.position[1] + y
            if px < 0 or px >= PLAY_WIDTH or py >= PLAY_HEIGHT:
                return False
            if py >= 0 and self.grid[py][px] is not None:
                return False
        return True

    def _lock_piece(self):
        for x, y in self.current.blocks():
            px = self.current.position[0] + x
            py = self.current.position[1] + y
            if py < 0:
                self.game_over = True
            else:
                self.grid[py][px] = self.current.color
        self._clear_lines()
        self.current = self.next_piece
        self.next_piece = self._new_piece()

    def _clear_lines(self):
        cleared = 0
        for y in range(PLAY_HEIGHT - 1, -1, -1):
            if all(self.grid[y][x] is not None for x in range(PLAY_WIDTH)):
                cleared += 1
                line_color = self.grid[y][0]
                for x in range(PLAY_WIDTH):
                    self.particles.append(Particle((GRID_OFFSET_X + x * BLOCK_SIZE + BLOCK_SIZE / 2,
                                                    GRID_OFFSET_Y + y * BLOCK_SIZE + BLOCK_SIZE / 2), line_color))
                del self.grid[y]
                self.grid.insert(0, [None for _ in range(PLAY_WIDTH)])
        if cleared:
            self.score += LINE_CLEAR_SCORE[cleared - 1] * self.level
            self.lines += cleared
            self.level = 1 + self.lines // 10

    def _move(self, dx):
        moved = Tetromino(self.current.shape)
        moved.rotation = self.current.rotation
        moved.position = [self.current.position[0] + dx, self.current.position[1]]
        if self._valid_position(moved):
            self.current = moved

    def _rotate(self, direction=1):
        rotated = self.current.rotated(direction)
        kicks = [(0, 0), (-1, 0), (1, 0), (0, -1)]
        for dx, dy in kicks:
            rotated.position = [self.current.position[0] + dx, self.current.position[1] + dy]
            if self._valid_position(rotated):
                self.current = rotated
                return

    def _drop(self, hard=False):
        dy = 1
        delay = SOFT_DROP_DELAY if self.soft_drop else GRAVITY_DELAY
        if hard:
            while True:
                moved = Tetromino(self.current.shape)
                moved.rotation = self.current.rotation
                moved.position = [self.current.position[0], self.current.position[1] + dy]
                if not self._valid_position(moved):
                    break
                self.current = moved
                self.score += HARD_DROP_BONUS
            self._lock_piece()
            return

        moved = Tetromino(self.current.shape)
        moved.rotation = self.current.rotation
        moved.position = [self.current.position[0], self.current.position[1] + dy]
        if self._valid_position(moved):
            self.current = moved
        else:
            self._lock_piece()
        return delay

    def _ghost_position(self):
        ghost = Tetromino(self.current.shape)
        ghost.rotation = self.current.rotation
        ghost.position = self.current.position.copy()
        while True:
            ghost.position[1] += 1
            if not self._valid_position(ghost):
                ghost.position[1] -= 1
                break
        return ghost.position

    def _draw_background(self):
        for y in range(0, HEIGHT, 4):
            color = pygame.Color(0, 0, 0)
            color.hsla = (200 + y // 6, 70, 12 + y // 30, 100)
            pygame.draw.rect(self.screen, color, (0, y, WIDTH, 4))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (0, 200, 255, 35), (WIDTH // 4, HEIGHT // 3), 260)
        pygame.draw.circle(overlay, (255, 80, 180, 25), (WIDTH * 3 // 4, HEIGHT // 2), 260)
        self.screen.blit(overlay, (0, 0))

    def _draw_grid(self):
        glow = pygame.Surface((PLAY_WIDTH * BLOCK_SIZE + 6, PLAY_HEIGHT * BLOCK_SIZE + 6), pygame.SRCALPHA)
        pygame.draw.rect(glow, (255, 255, 255, 30), glow.get_rect(), border_radius=18)
        pygame.draw.rect(glow, (255, 255, 255, 10), glow.get_rect(), width=3, border_radius=18)
        self.screen.blit(glow, (GRID_OFFSET_X - 3, GRID_OFFSET_Y - 3))
        for x in range(PLAY_WIDTH + 1):
            pygame.draw.line(self.screen, (255, 255, 255, 25),
                             (GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y),
                             (GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y + PLAY_HEIGHT * BLOCK_SIZE), 1)
        for y in range(PLAY_HEIGHT + 1):
            pygame.draw.line(self.screen, (255, 255, 255, 25),
                             (GRID_OFFSET_X, GRID_OFFSET_Y + y * BLOCK_SIZE),
                             (GRID_OFFSET_X + PLAY_WIDTH * BLOCK_SIZE, GRID_OFFSET_Y + y * BLOCK_SIZE), 1)

    def _draw_piece(self, piece, ghost=False):
        color = piece.color
        for x, y in piece.blocks():
            px = GRID_OFFSET_X + (piece.position[0] + x) * BLOCK_SIZE
            py = GRID_OFFSET_Y + (piece.position[1] + y) * BLOCK_SIZE
            rect = pygame.Rect(px, py, BLOCK_SIZE, BLOCK_SIZE)
            if ghost:
                ghost_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(ghost_surf, (*color, 40), ghost_surf.get_rect(), border_radius=6)
                self.screen.blit(ghost_surf, rect)
            else:
                block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(block, (*color, 240), block.get_rect(), border_radius=8)
                pygame.draw.rect(block, (255, 255, 255, 60), block.get_rect(), 2, border_radius=8)
                shine = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(shine, (255, 255, 255, 60), (8, 8), 8)
                block.blit(shine, (0, 0))
                self.screen.blit(block, rect)

    def _draw_next(self):
        title = self.font.render("Próxima", True, (230, 240, 255))
        self.screen.blit(title, (390, 120))
        preview = pygame.Surface((140, 140), pygame.SRCALPHA)
        preview.fill((0, 0, 0, 40))
        pygame.draw.rect(preview, (255, 255, 255, 30), preview.get_rect(), 2, border_radius=12)
        temp_piece = Tetromino(self.next_piece.shape)
        for x, y in temp_piece.blocks():
            px = 50 + x * 24
            py = 40 + y * 24
            block = pygame.Rect(px, py, 24, 24)
            pygame.draw.rect(preview, (*temp_piece.color, 220), block, border_radius=6)
            pygame.draw.rect(preview, (255, 255, 255, 50), block, 2, border_radius=6)
        self.screen.blit(preview, (390, 150))

    def _draw_info(self):
        stats = [f"Score: {self.score}", f"Lines: {self.lines}", f"Level: {self.level}"]
        for i, text in enumerate(stats):
            surface = self.font.render(text, True, (230, 240, 255))
            self.screen.blit(surface, (390, 330 + i * 36))
        help_lines = ["←/→ mover", "↑ rotaciona", "↓ cair rápido", "Espaço: queda dura", "R: reiniciar"]
        for i, text in enumerate(help_lines):
            surface = self.font.render(text, True, (200, 210, 240))
            self.screen.blit(surface, (370, 500 + i * 28))

    def _draw_particles(self):
        for p in self.particles[:]:
            p.update()
            p.draw(self.screen)
            if p.life <= 0:
                self.particles.remove(p)

    def _reset(self):
        self.grid = [[None for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]
        self.current = self._new_piece()
        self.next_piece = self._new_piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.particles.clear()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        self._reset()
                    if self.game_over:
                        continue
                    if event.key == pygame.K_LEFT:
                        self._move(-1)
                    elif event.key == pygame.K_RIGHT:
                        self._move(1)
                    elif event.key == pygame.K_UP:
                        self._rotate()
                    elif event.key == pygame.K_SPACE:
                        self._drop(hard=True)
                    elif event.key == pygame.K_DOWN:
                        self.soft_drop = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_DOWN:
                        self.soft_drop = False

            if not self.game_over:
                self.drop_timer += dt
                delay = SOFT_DROP_DELAY if self.soft_drop else GRAVITY_DELAY // self.level
                if self.drop_timer >= delay:
                    self.drop_timer = 0
                    self._drop()

            self._draw_background()
            self._draw_grid()

            for y in range(PLAY_HEIGHT):
                for x in range(PLAY_WIDTH):
                    if self.grid[y][x]:
                        block = pygame.Rect(GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y + y * BLOCK_SIZE,
                                            BLOCK_SIZE, BLOCK_SIZE)
                        color = self.grid[y][x]
                        pygame.draw.rect(self.screen, color, block, border_radius=8)
                        pygame.draw.rect(self.screen, (255, 255, 255, 40), block, 2, border_radius=8)

            if not self.game_over:
                ghost_pos = self._ghost_position()
                ghost_piece = Tetromino(self.current.shape)
                ghost_piece.rotation = self.current.rotation
                ghost_piece.position = ghost_pos
                self._draw_piece(ghost_piece, ghost=True)
                self._draw_piece(self.current)

            self._draw_next()
            self._draw_info()
            self._draw_particles()

            if self.game_over:
                overlay = pygame.Surface((PLAY_WIDTH * BLOCK_SIZE, PLAY_HEIGHT * BLOCK_SIZE), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (GRID_OFFSET_X, GRID_OFFSET_Y))
                text = self.big_font.render("Game Over", True, (255, 255, 255))
                sub = self.font.render("Pressione R para recomeçar", True, (220, 230, 255))
                self.screen.blit(text, (GRID_OFFSET_X + 60, GRID_OFFSET_Y + 240))
                self.screen.blit(sub, (GRID_OFFSET_X + 32, GRID_OFFSET_Y + 300))

            pygame.display.flip()
        pygame.quit()


def main():
    game = TetrisGame()
    game.run()


if __name__ == "__main__":
    main()
