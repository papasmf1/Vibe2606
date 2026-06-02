#cmd
#pip install pygame 
import random
import sys
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class Direction:
    x: int
    y: int


UP = Direction(0, -1)
DOWN = Direction(0, 1)
LEFT = Direction(-1, 0)
RIGHT = Direction(1, 0)


class Snake:
    def __init__(self, start_pos: tuple[int, int], block_size: int) -> None:
        self.block_size = block_size
        self.body: list[tuple[int, int]] = [
            start_pos,
            (start_pos[0] - block_size, start_pos[1]),
            (start_pos[0] - (2 * block_size), start_pos[1]),
        ]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.grow_pending = 0

    def set_direction(self, direction: Direction) -> None:
        # Prevent direct 180-degree turns.
        if (self.direction.x + direction.x, self.direction.y + direction.y) == (0, 0):
            return
        self.next_direction = direction

    def move(self) -> None:
        self.direction = self.next_direction
        head_x, head_y = self.body[0]
        new_head = (
            head_x + self.direction.x * self.block_size,
            head_y + self.direction.y * self.block_size,
        )
        self.move_to(new_head)

    def next_head(self) -> tuple[int, int]:
        head_x, head_y = self.body[0]
        return (
            head_x + self.next_direction.x * self.block_size,
            head_y + self.next_direction.y * self.block_size,
        )

    def move_to(self, new_head: tuple[int, int]) -> None:
        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self) -> None:
        self.grow_pending += 1

    @property
    def head(self) -> tuple[int, int]:
        return self.body[0]

    def collided_with_self(self) -> bool:
        return self.head in self.body[1:]

    def draw(self, surface: pygame.Surface, color: tuple[int, int, int]) -> None:
        for segment in self.body:
            pygame.draw.rect(surface, color, pygame.Rect(*segment, self.block_size, self.block_size))


class Food:
    def __init__(self, block_size: int, width: int, height: int) -> None:
        self.block_size = block_size
        self.width = width
        self.height = height
        self.position = (0, 0)

    def spawn(self, occupied: set[tuple[int, int]]) -> None:
        cols = self.width // self.block_size
        rows = self.height // self.block_size

        while True:
            x = random.randint(0, cols - 1) * self.block_size
            y = random.randint(0, rows - 1) * self.block_size
            if (x, y) not in occupied:
                self.position = (x, y)
                return

    def draw(self, surface: pygame.Surface, color: tuple[int, int, int]) -> None:
        pygame.draw.rect(
            surface,
            color,
            pygame.Rect(self.position[0], self.position[1], self.block_size, self.block_size),
        )


class SnakeGame:
    WIDTH = 640
    HEIGHT = 480
    BLOCK_SIZE = 20
    FPS = 10
    FOOD_COUNT = 4

    BG_COLOR = (18, 22, 26)
    PLAYER_COLOR = (80, 210, 120)
    AI_COLOR = (90, 140, 245)
    FOOD_COLOR = (240, 80, 80)
    TEXT_COLOR = (240, 240, 240)

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Snake Battle: Human vs AI")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("malgungothic", 26)
        self.small_font = pygame.font.SysFont("malgungothic", 20)

        self.player_snake = Snake((0, 0), self.BLOCK_SIZE)
        self.ai_snake = Snake((0, 0), self.BLOCK_SIZE)
        self.foods = [Food(self.BLOCK_SIZE, self.WIDTH, self.HEIGHT) for _ in range(self.FOOD_COUNT)]
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.winner_text = ""

        self.reset()

    def reset(self) -> None:
        player_start = (self.BLOCK_SIZE * 8, self.HEIGHT // 2)
        ai_start = (self.WIDTH - (self.BLOCK_SIZE * 9), self.HEIGHT // 2)

        self.player_snake = Snake(player_start, self.BLOCK_SIZE)
        self.player_snake.direction = RIGHT
        self.player_snake.next_direction = RIGHT

        self.ai_snake = Snake(ai_start, self.BLOCK_SIZE)
        self.ai_snake.direction = LEFT
        self.ai_snake.next_direction = LEFT

        occupied = set(self.player_snake.body) | set(self.ai_snake.body)
        for food in self.foods:
            food.spawn(occupied)
            occupied.add(food.position)
        self.player_score = 0
        self.ai_score = 0
        self.game_over = False
        self.winner_text = ""

    def in_bounds(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def choose_ai_direction(self) -> None:
        directions = [UP, DOWN, LEFT, RIGHT]
        random.shuffle(directions)

        target_food = min(
            self.foods,
            key=lambda f: abs(self.ai_snake.head[0] - f.position[0]) + abs(self.ai_snake.head[1] - f.position[1]),
        )

        directions.sort(
            key=lambda d: abs(
                self.ai_snake.head[0] + d.x * self.BLOCK_SIZE - target_food.position[0]
            )
            + abs(self.ai_snake.head[1] + d.y * self.BLOCK_SIZE - target_food.position[1])
        )

        blocked = set(self.player_snake.body) | set(self.ai_snake.body[1:])
        for d in directions:
            if (self.ai_snake.direction.x + d.x, self.ai_snake.direction.y + d.y) == (0, 0):
                continue
            candidate = (
                self.ai_snake.head[0] + d.x * self.BLOCK_SIZE,
                self.ai_snake.head[1] + d.y * self.BLOCK_SIZE,
            )
            if self.in_bounds(candidate) and candidate not in blocked:
                self.ai_snake.set_direction(d)
                return

    def process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_q:
                        return False
                    continue

                if event.key in (pygame.K_UP, pygame.K_w):
                    self.player_snake.set_direction(UP)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.player_snake.set_direction(DOWN)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self.player_snake.set_direction(LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.player_snake.set_direction(RIGHT)

        return True

    def update(self) -> None:
        if self.game_over:
            return

        self.choose_ai_direction()

        player_next = self.player_snake.next_head()
        ai_next = self.ai_snake.next_head()

        player_dead = (
            (not self.in_bounds(player_next))
            or player_next in set(self.player_snake.body[1:])
            or player_next in set(self.ai_snake.body)
        )
        ai_dead = (
            (not self.in_bounds(ai_next))
            or ai_next in set(self.ai_snake.body[1:])
            or ai_next in set(self.player_snake.body)
        )

        if player_next == ai_next:
            player_dead = True
            ai_dead = True

        if player_dead or ai_dead:
            self.game_over = True
            if player_dead and ai_dead:
                if self.player_score > self.ai_score:
                    self.winner_text = "무승부 충돌! 점수 승리: 플레이어"
                elif self.ai_score > self.player_score:
                    self.winner_text = "무승부 충돌! 점수 승리: AI"
                else:
                    self.winner_text = "완전 무승부"
            elif player_dead:
                self.winner_text = "AI 승리"
            else:
                self.winner_text = "플레이어 승리"
            return

        self.player_snake.direction = self.player_snake.next_direction
        self.ai_snake.direction = self.ai_snake.next_direction

        food_positions = {food.position for food in self.foods}
        player_ate = player_next in food_positions
        ai_ate = ai_next in food_positions

        if player_ate:
            self.player_snake.grow()
            self.player_score += 1
        if ai_ate:
            self.ai_snake.grow()
            self.ai_score += 1

        self.player_snake.move_to(player_next)
        self.ai_snake.move_to(ai_next)

        eaten_positions: set[tuple[int, int]] = set()
        if player_ate:
            eaten_positions.add(player_next)
        if ai_ate:
            eaten_positions.add(ai_next)

        if eaten_positions:
            occupied = set(self.player_snake.body) | set(self.ai_snake.body)
            occupied |= {food.position for food in self.foods if food.position not in eaten_positions}
            for food in self.foods:
                if food.position in eaten_positions:
                    food.spawn(occupied)
                    occupied.add(food.position)

    def draw(self) -> None:
        self.screen.fill(self.BG_COLOR)

        for food in self.foods:
            food.draw(self.screen, self.FOOD_COLOR)
        self.player_snake.draw(self.screen, self.PLAYER_COLOR)
        self.ai_snake.draw(self.screen, self.AI_COLOR)

        player_score_text = self.small_font.render(f"플레이어: {self.player_score}", True, self.TEXT_COLOR)
        ai_score_text = self.small_font.render(f"AI: {self.ai_score}", True, self.TEXT_COLOR)
        control_text = self.small_font.render("이동: 방향키/WASD", True, self.TEXT_COLOR)
        self.screen.blit(player_score_text, (10, 10))
        self.screen.blit(ai_score_text, (10, 35))
        self.screen.blit(control_text, (10, 60))

        if self.game_over:
            over_text = self.font.render("게임 오버", True, self.TEXT_COLOR)
            winner_text = self.small_font.render(self.winner_text, True, self.TEXT_COLOR)
            retry_text = self.small_font.render("R: 재시작 / Q: 종료", True, self.TEXT_COLOR)
            self.screen.blit(over_text, (self.WIDTH // 2 - over_text.get_width() // 2, self.HEIGHT // 2 - 30))
            self.screen.blit(
                winner_text,
                (self.WIDTH // 2 - winner_text.get_width() // 2, self.HEIGHT // 2 + 2),
            )
            self.screen.blit(
                retry_text,
                (self.WIDTH // 2 - retry_text.get_width() // 2, self.HEIGHT // 2 + 28),
            )

        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            running = self.process_events()
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
