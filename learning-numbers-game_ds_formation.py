import pygame
import os
import random
import math
from gtts import gTTS
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Constants
SCREEN_SIZE = (1920, 1080)  # Updated screen size
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "green": (0, 255, 0),
    "red": (255, 0, 0),
    "overlay": (255, 255, 255, 180)
}
FONT_SETTINGS = (None, 72)  # Increased font size
ANIMATION = {
    "hover_scale": 1.2,
    "ball_speed": 1.5,
    "transition_speed": 2.0,
    "feedback_speed": 5.0
}

@dataclass
class GameState:
    score: int = 0
    rounds_played: int = 0
    target_number: int = 0
    feedback_text: str = ""
    feedback_alpha: float = 0
    is_active: bool = True
    transition_progress: float = 0

class Ball:
    def __init__(self, bounds: Tuple[int, int], index: int, total: int, accel_factor: float = 0):
        self.radius = 30  # Increased ball radius
        self.color = tuple(random.randint(0, 255) for _ in range(3))
        self.bounds = bounds
        self.index = index
        self.total = total
        self._reset_position()
        self.accel_factor = accel_factor

    def _reset_position(self):
        i = self.index
        n = self.total
        # Calculate row and position for pyramid
        r = int((math.sqrt(8 * i + 1) - 1) // 2)
        p = i - (r * (r + 1)) // 2

        # Calculate maximum row to determine top_y
        last_i = n - 1
        r_max = (math.sqrt(8 * last_i + 1) - 1) // 2
        number_of_rows = r_max + 1

        spacing = 60  # Spacing between ball centers
        top_y = (self.bounds[1] - (number_of_rows * spacing)) // 2

        # Calculate balls_in_row for this row
        balls_in_row = min(r + 1, n - (r * (r + 1) // 2))

        # Calculate x and y
        center_x = self.bounds[0] // 2
        start_x = center_x - ((balls_in_row - 1) * spacing) // 2
        x = start_x + p * spacing
        y = top_y + r * spacing

        self.x = x
        self.y = y

        # Random movement direction
        move_angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(move_angle) * ANIMATION["ball_speed"]
        self.dy = math.sin(move_angle) * ANIMATION["ball_speed"]

    def update(self):
        # Keep within bounds (40px padding)
        self.x += self.dx * self.accel_factor
        self.y += self.dy * self.accel_factor
        
        if self.x <= 40 or self.x >= self.bounds[0]-40:
            self.dx *= -1
        if self.y <= 40 or self.y >= self.bounds[1]-40:
            self.dy *= -1

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

class NumberOption:
    def __init__(self, number: int):
        self.number = number
        self.balls = [Ball((360, 360), i, number, 0) for i in range(number)] # increased bounds
        self.scale = 1.0
        self.rect: Optional[pygame.Rect] = None
        self.accel_factor = 0

    def update(self):
        for ball in self.balls:
            ball.accel_factor = self.accel_factor
            ball.update()

    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> pygame.Rect:
        container = pygame.Surface((400, 400), pygame.SRCALPHA) # Increased size
        
        # Draw balls
        for ball in self.balls:
            ball.draw(container)
        
        # Draw border
        pygame.draw.rect(container, COLORS["black"], (0, 0, 400, 400), 4) # Increased border width
        
        # Scale and position
        scaled_size = int(400 * self.scale) # increased size
        scaled_img = pygame.transform.smoothscale(container, (scaled_size, scaled_size))
        self.rect = scaled_img.get_rect(center=(position[0] + 200, position[1] + 200)) # Adjusting offset
        surface.blit(scaled_img, self.rect)
        return self.rect

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Number Ball Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(*FONT_SETTINGS)
        self.state = GameState()
        self.options: List[NumberOption] = []
        self._load_assets()
        self._setup_directories()

    def _load_assets(self):
        try:
            self.sounds = {
                "correct": pygame.mixer.Sound("assets/good.wav"),
                "incorrect": pygame.mixer.Sound("assets/bad.wav")
            }
        except FileNotFoundError as e:
            raise SystemExit(f"Missing sound file: {e}")

    def _setup_directories(self):
        os.makedirs("temp", exist_ok=True)

    def new_round(self):
        self.state.target_number = random.randint(1, 10)
        self.state.rounds_played += 1
        self._generate_options()
        self._play_question_audio()
        self._reset_round_state()

    def _generate_options(self):
        numbers = [self.state.target_number] + random.sample(
            [n for n in range(1, 11) if n != self.state.target_number], 2)
        random.shuffle(numbers)
        self.options = [NumberOption(n) for n in numbers]

    def _play_question_audio(self):
        tts = gTTS(text=f"Where are {self.state.target_number} balls?", lang='en')
        tts.save("temp/question.mp3")
        pygame.mixer.Sound("temp/question.mp3").play()

    def _reset_round_state(self):
        self.state.feedback_text = ""
        self.state.feedback_alpha = 0
        self.state.transition_progress = 0

    def run(self):
        self.new_round()
        while True:
            self._handle_input()
            self._update_state()
            self._draw_frame()
            self.clock.tick(30)

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._cleanup()
                raise SystemExit
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._process_click(pygame.mouse.get_pos())
            
            if event.type == pygame.USEREVENT:
                self.new_round()
                pygame.time.set_timer(pygame.USEREVENT, 0)

    def _process_click(self, pos: Tuple[int, int]):
        if self.state.is_active:
            self._handle_game_click(pos)
        else:
            self._handle_restart_click(pos)

    def _handle_game_click(self, pos: Tuple[int, int]):
        for option in self.options:
            if option.rect and option.rect.collidepoint(pos):
                self._validate_answer(option.number)
                if "Correct" in self.state.feedback_text:
                    option.accel_factor = 1
                else:
                    option.accel_factor = 0
                # option.update()
                break

    def _validate_answer(self, answer: int):
        if answer == self.state.target_number:
            self.state.score += 10
            self.state.feedback_text = "Correct! +10 points"
            self.sounds["correct"].play()
        else:
            self.state.feedback_text = f"Wrong! It was {self.state.target_number}"
            self.sounds["incorrect"].play()

        self.state.is_active = self.state.rounds_played < 5
        pygame.time.set_timer(pygame.USEREVENT, 2000)

    def _handle_restart_click(self, pos: Tuple[int, int]):
        if self._restart_button_rect.collidepoint(pos):
            self.state = GameState()
            self.new_round()

    def _update_state(self):
        delta = self.clock.get_time() / 1000
        self._update_animations(delta)
        self._update_options(delta)

    def _update_animations(self, delta: float):
        self.state.feedback_alpha = min(self.state.feedback_alpha + delta * ANIMATION["feedback_speed"], 1)
        self.state.transition_progress = min(self.state.transition_progress + delta * ANIMATION["transition_speed"], 1)

    def _update_options(self, delta: float):
        # mouse_pos = pygame.mouse.get_pos()
        for option in self.options:
            # target_scale = ANIMATION["hover_scale"] if option.rect and option.rect.collidepoint(mouse_pos) else 1.0
            # option.scale += (target_scale - option.scale) * delta * 15
            option.update()

    def _draw_frame(self):
        self.screen.fill(COLORS["white"])
        
        if self.state.is_active:
            self._draw_active_game()
        else:
            self._draw_game_over()
        
        pygame.display.flip()

    def _draw_active_game(self):
        self._draw_options()
        self._draw_prompt()
        self._draw_score()
        self._draw_feedback()
        self._draw_transition()

    def _draw_options(self):
        # Adjusted option positions
        for i, option in enumerate(self.options):
            option.draw(self.screen, (100 + i * 600, 300))

    def _draw_prompt(self):
        text = self.font.render(f"Find {self.state.target_number} balls", True, COLORS["black"])
        self.screen.blit(text, text.get_rect(center=(SCREEN_SIZE[0]//2, 100))) # Adjusted Y position

    def _draw_score(self):
        text = self.font.render(f"Score: {self.state.score}", True, COLORS["black"])
        self.screen.blit(text, (20, 20))

    def _draw_feedback(self):
        if self.state.feedback_text:
            y = self._interpolate(SCREEN_SIZE[1] + 100, 800, self.state.feedback_alpha) # Adjusted Y postions
            self._draw_text_with_background(
                self.state.feedback_text, 
                (SCREEN_SIZE[0]//2, y),
                COLORS["green"] if "Correct" in self.state.feedback_text else COLORS["red"]
            )

    def _draw_transition(self):
        if self.state.transition_progress < 1:
            alpha = int(self._interpolate(0, 255, self.state.transition_progress))
            overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((*COLORS["white"][:3], alpha))
            self.screen.blit(overlay, (0, 0))

    def _draw_game_over(self):
        self._draw_overlay()
        self._draw_final_score()
        self._restart_button_rect = self._draw_restart_button()

    def _draw_overlay(self):
        overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        radius = self._interpolate(0, math.hypot(*SCREEN_SIZE), self.state.transition_progress)
        pygame.draw.circle(overlay, COLORS["overlay"], 
                         (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2), int(radius))
        self.screen.blit(overlay, (0, 0))

    def _draw_final_score(self):
        text = self.font.render(f"Final Score: {self.state.score}", True, COLORS["black"])
        self.screen.blit(text, text.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2)))

    def _draw_restart_button(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, 400, 120) # Increased button size
        rect.center = (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 + 160) # Adjust button Y position
        pygame.draw.rect(self.screen, COLORS["green"], rect, border_radius=10)
        text = self.font.render("Restart", True, COLORS["black"])
        self.screen.blit(text, text.get_rect(center=rect.center))
        return rect

    def _draw_text_with_background(self, text: str, center: Tuple[int, int], color: Tuple[int, int, int]):
        text_surf = self.font.render(text, True, COLORS["black"])
        bg_rect = text_surf.get_rect().inflate(40, 20) # Increased background padding
        bg_rect.center = center
        pygame.draw.rect(self.screen, color, bg_rect, border_radius=5)
        self.screen.blit(text_surf, text_surf.get_rect(center=center))

    @staticmethod
    def _interpolate(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def _cleanup(self):
        pygame.quit()
        try:
            os.remove("temp/question.mp3")
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    Game().run()
