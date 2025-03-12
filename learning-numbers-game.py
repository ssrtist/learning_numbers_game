import pygame
import os
import sys
import random
import math
from gtts import gTTS
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Constants
SCREEN_SIZE = (1920, 1080)
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "lightgray": (200, 200, 200),
    "blue": (0, 0, 255),
    "green": (0, 255, 0),
    "red": (255, 0, 0),
    "yellow": (255, 255, 0),
    "overlay": (255, 255, 255, 180)
}
FONT_SETTINGS = ("arial", 36)
LARGE_FONT_SETTINGS = ("arial", 84)
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
    answer_is_correct: bool = False
    answered_incorrectly: bool = False
    current_sfx: str = ""
    update_sfx: bool = False
    current_music: str = ""
    update_music: bool = False

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
        for b in self.balls:
            b.accel_factor = self.accel_factor
            b.update()

    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> pygame.Rect:
        container = pygame.Surface((300, 300), pygame.SRCALPHA)
        
        # Draw balls
        for b in self.balls:
            b.draw(container)
        
        # Draw border
        pygame.draw.rect(container, COLORS["yellow"], (0, 0, 300, 300), 4)
        
        # Scale and position
        scaled_size = int(300 * self.scale)
        scaled_img = pygame.transform.smoothscale(container, (scaled_size, scaled_size))        
        self.rect = scaled_img.get_rect(center=(position[0] + 150, position[1] + 150))
        surface.blit(scaled_img, self.rect)
        return self.rect

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Number Ball Game")
        self.clock = pygame.time.Clock()
        self.normal_font = pygame.font.SysFont(*FONT_SETTINGS)
        self.large_font = pygame.font.SysFont(*LARGE_FONT_SETTINGS)
        self.state = GameState()
        self.options: List[NumberOption] = []
        self._load_assets()
        self.number_options = 5
        # self._setup_temp_directory()
        # _setup_temp_directory(self):
        os.makedirs("temp", exist_ok=True)
        self.channel_sfx = pygame.mixer.Channel(0)
        self.channel_music = pygame.mixer.Channel(1)
        self.channel_sfx.set_volume(0.75)
        self.channel_music.set_volume(0.25)

    def _get_audio(self, text: str):
        filename = f"sfx_{text.replace(" ", "_")}.mp3"
        if os.path.exists(f"assets/{filename}"):
            return pygame.mixer.Sound(f"assets/{filename}")
        else:
            tts = gTTS(text=text, lang='en')
            tts.save(f"assets/{filename}")
            return pygame.mixer.Sound(f"assets/{filename}")

    def _load_assets(self):
        try:
            self.sounds = {
                "point_to": self._get_audio("point to"),
                "1": self._get_audio("point to one ball"),
                "2": self._get_audio("point to two balls"),
                "3": self._get_audio("point to three balls"),
                "4": self._get_audio("point to four balls"),
                "5": self._get_audio("point to five balls"),
                "6": self._get_audio("point to six balls"),
                "7": self._get_audio("point to seven balls"),
                "8": self._get_audio("point to eight balls"),
                "9": self._get_audio("point to nine balls"),
                "10": self._get_audio("point to ten balls"),
                "ball": self._get_audio("ball"),
                "balls": self._get_audio("balls"),
                "number": self._get_audio("number"),
                "good_job": self._get_audio("good job"),
                "no_good": self._get_audio("no good"),
                "good": self._get_audio("good"),
                "you_did_it": self._get_audio("you did it")
            }
        except FileNotFoundError as e:
            raise SystemExit(f"Missing sound file: {e}")

    def _new_round(self):
        # Set target number sequentially (1-10)
        self.state.target_number = self.state.rounds_played + 1
        self.state.rounds_played += 1
        if self.state.rounds_played % 5 == 1:
            self._generate_options()
        # play question audio
        if self.state.is_active:
            self.sounds[str(self.state.target_number)].play()
        self._reset_round_state()

    def _generate_options(self):
        # Determine current set based on target number
        if self.state.target_number <= 5:
            available_numbers = list(range(1, 6))
        else:
            available_numbers = list(range(6, 11))
        # Generate options from the current set
        other_numbers = [n for n in available_numbers if n != self.state.target_number]
        selected = random.sample(other_numbers, self.number_options - 1)
        numbers = [self.state.target_number] + selected
        random.shuffle(numbers)
        self.options = [NumberOption(n) for n in numbers]

    def _reset_round_state(self):
        self.state.feedback_text = ""
        self.state.feedback_alpha = 0
        self.state.transition_progress = 0
        self.state.answer_is_correct = False
        self.state.answered_incorrectly = False

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._cleanup()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._process_click(pygame.mouse.get_pos())
            
            if event.type == pygame.USEREVENT:
                self._new_round()
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
                # if "Correct" in self.state.feedback_text:
                if self.state.answer_is_correct:
                    option.accel_factor = 1
                break

    def _validate_answer(self, answer: int):
        if answer == self.state.target_number and not self.state.answer_is_correct:
            self.state.score += 10
            self.state.feedback_text = "Good! +10 points"
            self.sounds["good"].play()
            self.state.answer_is_correct = True
            if self.state.rounds_played < 10:
                self.state.is_active = True
            else:
                self.sounds["you_did_it"].play()
                self.state.is_active = False
                self.state.rounds_played = 0
            # this below starts _new_round()
            pygame.time.set_timer(pygame.USEREVENT, 1000)

        if answer != self.state.target_number:
            if not pygame.mixer.get_busy():
                self.state.feedback_text = f"No good!"
                self.sounds["no_good"].play()
                self.state.answered_incorrectly = True

        # Game ends after 10 rounds
    def _handle_restart_click(self, pos: Tuple[int, int]):
        if self._restart_button_rect.collidepoint(pos):
            self.state = GameState()
            self._new_round()

    def _update_state(self):
        delta = self.clock.get_time() / 1000
        self.state.feedback_alpha = min(self.state.feedback_alpha + delta * ANIMATION["feedback_speed"], 1)
        self.state.transition_progress = min(self.state.transition_progress + delta * ANIMATION["transition_speed"], 1)
        for option in self.options:
            option.update()

    def _process_audio(self):
        # place holder to trigger and process music and sound fx
        return
    
    def _draw_frame(self):
        self.screen.fill(COLORS["lightgray"])
        
        if self.state.is_active:
            self._draw_options()
            self._draw_prompt()
            self._draw_score()
            self._draw_feedback()
            self._draw_transition()
        else:
            self._draw_overlay()
            self._draw_final_score()
            self._restart_button_rect = self._draw_restart_button()
        
        pygame.display.flip()

    def _draw_options(self):
        for i, option in enumerate(self.options):
            option.draw(self.screen, (100 + i * 350, 300))

    def _draw_prompt(self):
        text = self.large_font.render(f"{self.state.target_number} Balls", True, COLORS["red"])
        self.screen.blit(text, text.get_rect(center=(SCREEN_SIZE[0]//2, 100)))

    def _draw_score(self):
        text = self.normal_font.render(f"Score: {self.state.score}", True, COLORS["white"])
        self.screen.blit(text, (20, 20))

    def _draw_feedback(self):
        if self.state.feedback_text:
            y = self._interpolate(SCREEN_SIZE[1] + 100, 800, self.state.feedback_alpha)
            self._draw_text_with_background(
                self.state.feedback_text, 
                (SCREEN_SIZE[0]//2, y),
                COLORS["green"] if self.state.answer_is_correct else COLORS["red"]
            )

    def _draw_transition(self):
        if self.state.transition_progress < 1:
            alpha = int(self._interpolate(0, 255, self.state.transition_progress))
            overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
            overlay.fill((*COLORS["lightgray"][:3], alpha))
            self.screen.blit(overlay, (0, 0))

    def _draw_overlay(self):
        overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
        radius = self._interpolate(0, math.hypot(*SCREEN_SIZE), self.state.transition_progress)
        pygame.draw.circle(overlay, COLORS["overlay"], 
                         (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2), int(radius))
        self.screen.blit(overlay, (0, 0))

    def _draw_final_score(self):
        text = self.normal_font.render(f"Final Score: {self.state.score}", True, COLORS["white"])
        self.screen.blit(text, text.get_rect(center=(SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2)))

    def _draw_restart_button(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, 400, 120)
        rect.center = (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 + 160)
        pygame.draw.rect(self.screen, COLORS["green"], rect, border_radius=10)
        text = self.normal_font.render("Restart", True, COLORS["black"])
        self.screen.blit(text, text.get_rect(center=rect.center)) # type: ignore
        return rect

    def _draw_text_with_background(self, text: str, center: Tuple[int, int], color: Tuple[int, int, int]):
        text_surf = self.normal_font.render(text, True, COLORS["black"])
        bg_rect = text_surf.get_rect().inflate(40, 20) # type: ignore
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

    def run(self):
        self._new_round()
        while True:
            self._handle_input()
            self._update_state()
            self._draw_frame()
            self._process_audio()
            self.clock.tick(30)

if __name__ == "__main__":
    Game().run()
