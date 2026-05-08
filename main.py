"""Classic Pong game implemented with pygame."""

from __future__ import annotations

import math
import random
import struct
from array import array
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# Game configuration
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540
PADDLE_WIDTH = 14
PADDLE_HEIGHT = 94
BALL_SIZE = 16
PADDLE_SPEED = 420  # pixels per second
BALL_SPEED = 340
SCORE_TO_WIN = 10
FONT_NAME = "freesansbold.ttf"
BACKGROUND_COLOR_TOP = (10, 15, 35)
BACKGROUND_COLOR_BOTTOM = (10, 45, 70)
FOREGROUND_COLOR = (245, 245, 245)
ACCENT_COLOR = (80, 180, 255)
GLOW_COLOR = (120, 220, 255, 80)


@dataclass
class Paddle:
    """Represents a player's paddle."""

    x: int
    y: int
    speed: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x), int(self.y), PADDLE_WIDTH, PADDLE_HEIGHT
        )

    def update(self, dt: float) -> None:
        self.y += self.speed * dt
        self.y = max(0, min(SCREEN_HEIGHT - PADDLE_HEIGHT, self.y))

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, FOREGROUND_COLOR, self.rect, border_radius=6)


@dataclass
class Ball:
    """Represents the game ball."""

    x: float
    y: float
    vx: float
    vy: float

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - BALL_SIZE / 2),
            int(self.y - BALL_SIZE / 2),
            BALL_SIZE,
            BALL_SIZE,
        )

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y <= BALL_SIZE / 2:
            self.y = BALL_SIZE / 2
            self.vy = abs(self.vy)
        elif self.y >= SCREEN_HEIGHT - BALL_SIZE / 2:
            self.y = SCREEN_HEIGHT - BALL_SIZE / 2
            self.vy = -abs(self.vy)

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, ACCENT_COLOR, self.rect, border_radius=6)


@dataclass
class Particle:
    pos: pygame.Vector2
    vel: pygame.Vector2
    size: float
    life: float

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.life -= dt
        self.size = max(0, self.size - 60 * dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.life <= 0 or self.size <= 0:
            return
        pygame.draw.circle(surface, ACCENT_COLOR, self.pos, int(self.size))


class Game:
    """Main Pong game controller."""

    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except pygame.error:
            # Sound is optional; continue silently if mixer fails to load.
            pass

        pygame.display.set_caption("Pong")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(FONT_NAME, 48)
        self.small_font = pygame.font.Font(FONT_NAME, 24)

        self.left_paddle = Paddle(40, SCREEN_HEIGHT / 2 - PADDLE_HEIGHT / 2)
        self.right_paddle = Paddle(
            SCREEN_WIDTH - 40 - PADDLE_WIDTH, SCREEN_HEIGHT / 2 - PADDLE_HEIGHT / 2
        )
        self.ball = self._create_ball(initial_direction=1)

        self.left_score = 0
        self.right_score = 0
        self.ai_enabled = True
        self.trail: List[Tuple[float, float]] = []
        self.particles: List[Particle] = []
        self.glow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.background = self._create_vertical_gradient(
            SCREEN_WIDTH, SCREEN_HEIGHT, BACKGROUND_COLOR_TOP, BACKGROUND_COLOR_BOTTOM
        )
        self.sounds = self._load_sounds()

    def _create_ball(self, initial_direction: int) -> Ball:
        angle = random.uniform(-0.35 * math.pi, 0.35 * math.pi)
        speed_x = math.cos(angle) * BALL_SPEED * initial_direction
        speed_y = math.sin(angle) * BALL_SPEED
        return Ball(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, speed_x, speed_y)

    def _create_vertical_gradient(
        self, width: int, height: int, top_color: Tuple[int, int, int], bottom_color: Tuple[int, int, int]
    ) -> pygame.Surface:
        surface = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            color = [
                int(top_color[i] * (1 - ratio) + bottom_color[i] * ratio) for i in range(3)
            ]
            pygame.draw.line(surface, color, (0, y), (width, y))
        return surface

    def _generate_tone(self, frequency: int, duration_ms: int, volume: float = 0.5) -> pygame.mixer.Sound | None:
        if not pygame.mixer.get_init():
            return None
        sample_rate = 44100
        length = int(sample_rate * duration_ms / 1000)
        amplitude = int(32767 * volume)
        samples = array("h")
        for i in range(length):
            sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples.append(sample)
        return pygame.mixer.Sound(buffer=struct.pack("<" + "h" * len(samples), *samples))

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound | None]:
        return {
            "hit": self._generate_tone(720, 60, 0.6),
            "score": self._generate_tone(260, 180, 0.5),
            "wall": self._generate_tone(520, 70, 0.4),
        }

    def _play_sound(self, key: str) -> None:
        sound = self.sounds.get(key)
        if sound:
            sound.play()

    def _spawn_particles(self, position: Tuple[float, float], spread: float = 120.0) -> None:
        for _ in range(14):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, spread)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            self.particles.append(
                Particle(pos=pygame.Vector2(position), vel=vel, size=random.uniform(4, 8), life=0.4)
            )

    def _reset_round(self, scorer: str) -> None:
        if scorer == "left":
            self.left_score += 1
            direction = 1
        else:
            self.right_score += 1
            direction = -1
        self._play_sound("score")
        self._spawn_particles((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.ball = self._create_ball(initial_direction=direction)
        self.trail.clear()

    def _handle_input(self) -> None:
        keys = pygame.key.get_pressed()
        self.left_paddle.speed = 0
        self.right_paddle.speed = 0

        if keys[pygame.K_w]:
            self.left_paddle.speed -= PADDLE_SPEED
        if keys[pygame.K_s]:
            self.left_paddle.speed += PADDLE_SPEED

        if not self.ai_enabled:
            if keys[pygame.K_UP]:
                self.right_paddle.speed -= PADDLE_SPEED
            if keys[pygame.K_DOWN]:
                self.right_paddle.speed += PADDLE_SPEED

    def _predict_ball_y(self) -> float:
        if self.ball.vx <= 0:
            return SCREEN_HEIGHT / 2
        time_to_reach = (self.right_paddle.x - self.ball.x) / self.ball.vx
        projected_y = self.ball.y + self.ball.vy * time_to_reach
        # account for vertical bounces
        bounces = 0
        while projected_y < 0 or projected_y > SCREEN_HEIGHT:
            if projected_y < 0:
                projected_y = -projected_y
            elif projected_y > SCREEN_HEIGHT:
                projected_y = 2 * SCREEN_HEIGHT - projected_y
            bounces += 1
            if bounces > 10:
                break
        return projected_y

    def _update_ai(self, dt: float) -> None:
        if not self.ai_enabled or self.ball.vx <= 0:
            return
        target_y = self._predict_ball_y()
        center = self.right_paddle.y + PADDLE_HEIGHT / 2
        error = target_y - center
        reaction = 0.8
        self.right_paddle.speed = max(-PADDLE_SPEED, min(PADDLE_SPEED, error * reaction))
        if abs(error) < 18:
            self.right_paddle.speed = 0

    def _check_collisions(self) -> None:
        ball_rect = self.ball.rect

        if ball_rect.colliderect(self.left_paddle.rect) and self.ball.vx < 0:
            offset = (self.ball.y - self.left_paddle.y - PADDLE_HEIGHT / 2) / (
                PADDLE_HEIGHT / 2
            )
            bounce_angle = offset * (math.pi / 3)
            speed = math.hypot(self.ball.vx, self.ball.vy)
            self.ball.vx = math.cos(bounce_angle) * speed
            self.ball.vy = math.sin(bounce_angle) * speed
            self.ball.x = self.left_paddle.x + PADDLE_WIDTH + BALL_SIZE / 2
            self._play_sound("hit")
            self._spawn_particles((self.ball.x, self.ball.y), spread=180)
        elif ball_rect.colliderect(self.right_paddle.rect) and self.ball.vx > 0:
            offset = (self.ball.y - self.right_paddle.y - PADDLE_HEIGHT / 2) / (
                PADDLE_HEIGHT / 2
            )
            bounce_angle = offset * (math.pi / 3)
            speed = math.hypot(self.ball.vx, self.ball.vy)
            self.ball.vx = -math.cos(bounce_angle) * speed
            self.ball.vy = math.sin(bounce_angle) * speed
            self.ball.x = self.right_paddle.x - BALL_SIZE / 2
            self._play_sound("hit")
            self._spawn_particles((self.ball.x, self.ball.y), spread=180)

        if self.ball.y <= BALL_SIZE / 2 or self.ball.y >= SCREEN_HEIGHT - BALL_SIZE / 2:
            self._play_sound("wall")

        if self.ball.x < -BALL_SIZE:
            self._reset_round("right")
        elif self.ball.x > SCREEN_WIDTH + BALL_SIZE:
            self._reset_round("left")

    def _draw_center_line(self) -> None:
        dash_length = 22
        gap = 14
        y = 0
        pulse = (math.sin(pygame.time.get_ticks() * 0.004) + 1) / 2
        color = (
            200 + int(40 * pulse),
            200 + int(40 * pulse),
            255,
        )
        while y < SCREEN_HEIGHT:
            pygame.draw.rect(
                self.screen,
                color,
                (SCREEN_WIDTH // 2 - 3, y, 6, dash_length),
                border_radius=4,
            )
            y += dash_length + gap

    def _draw_scores(self) -> None:
        left_text = self.font.render(str(self.left_score), True, FOREGROUND_COLOR)
        right_text = self.font.render(str(self.right_score), True, FOREGROUND_COLOR)

        shadow_color = (10, 10, 10)
        self.screen.blit(left_text, (SCREEN_WIDTH / 2 - 82, 24))
        self.screen.blit(right_text, (SCREEN_WIDTH / 2 + 48, 24))
        self.screen.blit(left_text, (SCREEN_WIDTH / 2 - 80, 20))
        self.screen.blit(right_text, (SCREEN_WIDTH / 2 + 50, 20))

    def _draw_instructions(self) -> None:
        lines = [
            "W/S para mover | Espaço: alternar IA | ESC: sair",
            "Flechas para controlar a direita quando a IA estiver desativada",
        ]
        for i, text in enumerate(lines):
            surf = self.small_font.render(text, True, FOREGROUND_COLOR)
            self.screen.blit(
                surf, (SCREEN_WIDTH / 2 - surf.get_width() / 2, 10 + i * 24)
            )

    def _draw_trail(self) -> None:
        for index, (x, y) in enumerate(reversed(self.trail[-12:])):
            alpha = max(0, 180 - index * 16)
            size = max(2, BALL_SIZE - index)
            trail_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            trail_surface.fill((*ACCENT_COLOR, alpha))
            self.screen.blit(trail_surface, (x - size / 2, y - size / 2))

    def _draw_glow(self) -> None:
        self.glow_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.glow_surface,
            GLOW_COLOR,
            (int(self.ball.x), int(self.ball.y)),
            38,
        )
        pygame.draw.rect(self.glow_surface, (*ACCENT_COLOR, 70), self.left_paddle.rect.inflate(8, 8), border_radius=8)
        pygame.draw.rect(
            self.glow_surface,
            (*ACCENT_COLOR, 70),
            self.right_paddle.rect.inflate(8, 8),
            border_radius=8,
        )
        self.screen.blit(self.glow_surface, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)

    def _draw(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_center_line()
        self._draw_trail()
        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        self.ball.draw(self.screen)

        for particle in list(self.particles):
            particle.draw(self.screen)
            if particle.life <= 0 or particle.size <= 0:
                self.particles.remove(particle)

        self._draw_scores()
        self._draw_instructions()
        self._draw_glow()
        pygame.display.flip()

    def _check_win(self) -> bool:
        if self.left_score >= SCORE_TO_WIN or self.right_score >= SCORE_TO_WIN:
            winner = "Jogador" if self.left_score > self.right_score else "Computador"
            message = self.font.render(f"{winner} venceu!", True, FOREGROUND_COLOR)
            prompt = self.small_font.render(
                "Espaço: reiniciar | ESC: sair", True, FOREGROUND_COLOR
            )
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(170)
            overlay.fill((6, 6, 12))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(
                message,
                (SCREEN_WIDTH / 2 - message.get_width() / 2, SCREEN_HEIGHT / 2 - 40),
            )
            self.screen.blit(
                prompt,
                (SCREEN_WIDTH / 2 - prompt.get_width() / 2, SCREEN_HEIGHT / 2 + 10),
            )
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return True
                        if event.key == pygame.K_SPACE:
                            self.left_score = 0
                            self.right_score = 0
                            self.ball = self._create_ball(initial_direction=1)
                            self.trail.clear()
                            self.particles.clear()
                            waiting = False
                self.clock.tick(30)
        return False

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(75) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_SPACE:
                        self.ai_enabled = not self.ai_enabled

            self._handle_input()
            self._update_ai(dt)
            self.left_paddle.update(dt)
            self.right_paddle.update(dt)
            self.ball.update(dt)
            self._check_collisions()

            self.trail.append((self.ball.x, self.ball.y))
            if len(self.trail) > 30:
                self.trail.pop(0)

            for particle in list(self.particles):
                particle.update(dt)
                if particle.life <= 0 or particle.size <= 0:
                    self.particles.remove(particle)

            self._draw()

            if self._check_win():
                running = False

        pygame.quit()


def main() -> None:
    """Start the Pong game."""

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
