""" This is a beginner's game for learning numbers """

import os
import io
import pygame
import random
import math
import numpy as np
from typing import Optional, Tuple
from gtts import gTTS

# --- Global Constants and Configuration ---
SCREEN_SIZE = (1920, 1080)
FULLSCREEN_RESOLUTION = (1920, 1080)
WINDOWED_RESOLUTION = (1024, 768)
MAX_LEVEL = 2
COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "lightgray": (200, 200, 200),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "darkred": (128, 0, 0),
    "darkgreen": (0, 128, 0),
    "darkblue": (0, 0, 128),
    "darkgray": (64, 64, 64),
    "overlay": (255, 255, 255, 180),
    "lightyellow": (255, 255, 200)
}
BALL_COLORS = [COLORS["red"], COLORS["green"], COLORS["blue"], COLORS["yellow"], COLORS["white"], COLORS["lightyellow"], COLORS["darkred"], COLORS["darkgreen"], COLORS["darkblue"], COLORS["darkgray"]]
NUMBERS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
FONT_SETTINGS = ("arial", 36)
LARGE_FONT_SETTINGS = ("arial", 84)
EXTRA_LARGE_FONT_SETTINGS = ("arial", 120)
ANIMATION = {"hover_scale": 1.2, "ball_speed": 3, "transition_speed": 2.0, "feedback_speed": 5.0}

# --- Helper Functions ---
def toggle_fullscreen(screen, screen_width, screen_height, fullscreen):
    """Toggles between fullscreen and windowed mode."""
    is_fullscreen = screen.get_flags() & pygame.FULLSCREEN
    if not is_fullscreen:
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((screen_width, screen_height))
    fullscreen = not is_fullscreen
    return fullscreen, screen

def generate_speech_sound(text):
    """Generates and returns a Pygame sound object from text using gTTS."""
    buffer = io.BytesIO()
    tts = gTTS(text=text, lang='en')
    tts.write_to_fp(buffer)
    buffer.seek(0)
    sound = pygame.mixer.Sound(buffer)
    return sound

class Button:
    """Button UI element."""
    def __init__(self, x, y, text, width=200, height=50, color=COLORS["darkgreen"]):
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.color = color
        self.text_color = COLORS["white"]
        self.text = text
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect)
        rendered_text = font.render(self.text, True, self.text_color)
        text_rect = rendered_text.get_rect(center=self.rect.center) # Center the text in the button
        screen.blit(rendered_text, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

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

class NumberOption:
    def __init__(self, number: int):
        self.number = number
        self.scale = 1.0
        self.rect: Optional[pygame.Rect] = None
        self.accel_factor = 0
        self.text_image = None
        self.normal_font = pygame.font.SysFont(*FONT_SETTINGS)
        self.large_font = pygame.font.SysFont(*LARGE_FONT_SETTINGS)
        self.extra_large_font = pygame.font.SysFont(*EXTRA_LARGE_FONT_SETTINGS)
        self.highlight_good = False
        self.highlight_bad = False
        self.visible = True
        self.visible_end_time = None

    def update(self):
        accel_factor = self.accel_factor

    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> pygame.Rect:
        container = pygame.Surface((300, 300), pygame.SRCALPHA)
        
        if not self.visible:
            # return None
            if self.visible_end_time is None:
                self.visible_end_time = pygame.time.get_ticks()
            self.visible_end_elapse = pygame.time.get_ticks() - self.visible_end_time
            if self.visible_end_elapse > 1000:
                return None
        
        # Draw rectangle
        if self.highlight_good:
            pygame.draw.rect(container, COLORS["darkgreen"], (0, 0, 300, 300), border_radius=10)

        if self.highlight_bad:
            pygame.draw.rect(container, COLORS["darkred"], (0, 0, 300, 300), border_radius=10)
        
        # Draw border
        pygame.draw.rect(container, COLORS["yellow"], (0, 0, 300, 300), 4, border_radius=10)
        
        # Blit text
        self.text_image = self.extra_large_font.render(str(self.number), True, COLORS["white"])
        container.blit(self.text_image, (150 - self.text_image.get_width() // 2, 150 - self.text_image.get_height() // 2))
        
        # Scale and position
        scaled_size = int(300 * self.scale)
        scaled_img = pygame.transform.smoothscale(container, (scaled_size, scaled_size))        
        self.rect = scaled_img.get_rect(center=(position[0] + 150, position[1] + 150))
        surface.blit(scaled_img, self.rect)
        return self.rect

class Ball:
    def __init__(self, bounds: Tuple[int, int], index: int, total: int, accel_factor: float = 0):
        self.radius = 30
        # self.color = random.choice([COLORS["red"], COLORS["green"], COLORS["blue"], COLORS["yellow"], COLORS["white"], COLORS["lightyellow"], COLORS["darkred"], COLORS["darkgreen"], COLORS["darkblue"], COLORS["darkgray"]])
        # self.color = BALL_COLORS[index]
        self.color = COLORS["lightyellow"]
        self.bounds = bounds
        self.index = index
        self.total = total
        self._reset_position()
        self.accel_factor = accel_factor

    def _reset_position(self):
        # Bottom-up, left-aligned, max 5 per row
        row = self.index // 3  # Determine row (0 = bottom)
        pos_in_row = self.index % 3  # Position in row (0-4)

        # X position: left-aligned with spacing
        x = 90 + pos_in_row * 65  # 30=radius, 60=diameter (spacing=5)
        
        # Y position: start from bottom (270 = 300 - radius)
        y = 240 - row * 65  # 60=diameter (5 vertical spacing)
        
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
        
        if self.x <= 30 or self.x >= self.bounds[0]-90:
            self.dx *= -1
        if self.y <= 30 or self.y >= self.bounds[1]-90:
            self.dy *= -1

    def draw(self, surface: pygame.Surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, COLORS["black"], (int(self.x), int(self.y)), self.radius, 2)

class BallOption:
    def __init__(self, number: int):
        self.number = number
        self.balls = [Ball((360, 360), i, number, 0) for i in range(number)] # increased bounds
        self.scale = 1.0
        self.rect: Optional[pygame.Rect] = None
        self.accel_factor = 0
        self.visible = True
        self.visible_end_time = None

    def update(self):
        for b in self.balls:
            b.accel_factor = self.accel_factor
            b.update()

    def draw(self, surface: pygame.Surface, position: Tuple[int, int]) -> pygame.Rect:
        container = pygame.Surface((300, 300), pygame.SRCALPHA)
        
        if not self.visible:
            # return None
            if self.visible_end_time is None:
                self.visible_end_time = pygame.time.get_ticks()
            self.visible_end_elapse = pygame.time.get_ticks() - self.visible_end_time
            if self.visible_end_elapse > 1000:
                return None
        
        # Draw rectangle
        if self.highlight_good:
            pygame.draw.rect(container, COLORS["darkgreen"], (0, 0, 300, 300), border_radius=10)

        if self.highlight_bad:
            pygame.draw.rect(container, COLORS["darkred"], (0, 0, 300, 300), border_radius=10)
        
        # Draw border
        pygame.draw.rect(container, COLORS["yellow"], (0, 0, 300, 300), 4, border_radius=10)

        # Draw balls
        for b in self.balls:
            b.draw(container)
        
        # Draw border
        pygame.draw.rect(container, COLORS["yellow"], (0, 0, 300, 300), 4, border_radius=10)
        
        # Scale and position
        scaled_size = int(300 * self.scale)
        scaled_img = pygame.transform.smoothscale(container, (scaled_size, scaled_size))        
        self.rect = scaled_img.get_rect(center=(position[0] + 150, position[1] + 150))
        surface.blit(scaled_img, self.rect)
        return self.rect

class MainGame:
    """Main class to manage the Game."""
    def __init__(self):
        pygame.init()

        # graphics init
        self.screen_width = FULLSCREEN_RESOLUTION[0]
        self.screen_height = FULLSCREEN_RESOLUTION[1]
        # self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Game Title")
        self.fullscreen = self.screen.get_flags() & pygame.FULLSCREEN

        # fonts init
        self.title_font = pygame.font.Font(None, 48)
        self.text_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 36)
        self.game_font = pygame.font.SysFont("arial", 52)

        # common variables init
        pygame.mixer.init()
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_mode = "menu"
        self.play_welcome_sound = True

        # --- start of game variables ---

        # Fonts
        self.normal_font = pygame.font.SysFont(*FONT_SETTINGS)
        self.large_font = pygame.font.SysFont(*LARGE_FONT_SETTINGS)
        self.extra_large_font = pygame.font.SysFont(*EXTRA_LARGE_FONT_SETTINGS)
        self.state = GameState()
        self.game_level = 1
        self.max_game_level = MAX_LEVEL
        self._load_assets()
        self.number_options = 5
        os.makedirs("temp", exist_ok=True)
        self.channel_sfx = pygame.mixer.Channel(0)
        self.channel_music = pygame.mixer.Channel(1)
        self.channel_sfx.set_volume(0.75)
        self.channel_music.set_volume(0.25)
        self.new_sfx = None
        self.new_music = None

        self.click_sound = pygame.mixer.Sound("assets/mouse_click.mp3")

        # --- end of game variables ---

        # --- Background Music ---
        self.menu_music = "assets/bgm_medium.mp3" 
        self.options_music = "assets/bgm_medium.mp3" 
        self.colors_music = "assets/bgm_strong.mp3" 
        self.current_music = None
        self.play_music(self.menu_music)

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
                "1": [self._get_audio("number one"), self._get_audio("one ball")],
                "2": [self._get_audio("number two"), self._get_audio("two balls")],
                "3": [self._get_audio("number three"), self._get_audio("three balls")],
                "4": [self._get_audio("number four"), self._get_audio("four balls")],
                "5": [self._get_audio("number five"), self._get_audio("five balls")],
                "6": [self._get_audio("number six"), self._get_audio("six balls")],
                "7": [self._get_audio("number seven"), self._get_audio("seven balls")],
                "8": [self._get_audio("number eight"), self._get_audio("eight balls")],
                "9": [self._get_audio("number nine"), self._get_audio("nine balls")],
                "10": [self._get_audio("number ten"), self._get_audio("ten balls")],
                "good_job": self._get_audio("good job"),
                "no_good": self._get_audio("no good"),
                "good": self._get_audio("good"),
                "you_did_it": self._get_audio("you did it")
            }
        except FileNotFoundError as e:
            raise SystemExit(f"Missing sound file: {e}")

    def _new_round(self):
        # Set target number sequentially (1-10)
        self.state.rounds_played += 1
        self.state.target_number = self.state.rounds_played
        if self.state.rounds_played % 5 == 1:
            self._generate_options()

        for opt in self.options:
            opt.highlight_bad = False
            opt.highlight_good = False
            
        if self.state.is_active:
            snd_arr1 = pygame.sndarray.array(self.sounds["point_to"])
            if self.game_level == 2:
                snd_arr2 = pygame.sndarray.array(self.sounds[str(self.state.target_number)][1])
            elif self.game_level == 1:
                snd_arr2 = pygame.sndarray.array(self.sounds[str(self.state.target_number)][0])
            combined_arr = np.concatenate((snd_arr1, snd_arr2))
            combined_sound = pygame.sndarray.make_sound(combined_arr)
            self.new_sfx = combined_sound

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
        if self.game_level == 1:
            self.options = [NumberOption(n) for n in numbers]
        elif self.game_level == 2:
            self.options = [BallOption(n) for n in numbers]

    def _reset_round_state(self):
        self.state.feedback_text = ""
        self.state.feedback_alpha = 0
        self.state.transition_progress = 0
        self.state.answer_is_correct = False
        self.state.answered_incorrectly = False

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # self._cleanup()
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Toggle between fullscreen and windowed modes
                if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                    self.fullscreen, self.screen = toggle_fullscreen(self.screen, self.screen_width, self.screen_height, self.fullscreen)
                elif event.key == pygame.K_ESCAPE:
                    self.game_mode = "menu"
           
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.state.is_active:
                    if self.numbers_back_button.is_clicked(pos):
                        self.state = GameState()
                        self.game_mode = "menu"
                    self._handle_game_click(pos)
                else:
                    self._handle_restart_click(pos)
            
            if event.type == pygame.USEREVENT:
                self._new_round()
                pygame.time.set_timer(pygame.USEREVENT, 0)

    def _handle_game_click(self, pos: Tuple[int, int]):
        for option in self.options:
            if option.rect and option.rect.collidepoint(pos):
                if option.number == self.state.target_number and not self.state.answer_is_correct and not self.channel_sfx.get_busy():
                    self.state.score += 10
                    self.state.feedback_text = "Good! +10 points"
                    self.new_sfx = self.sounds["good"]
                    self.state.answer_is_correct = True
                    option.accel_factor = 1
                    if self.state.rounds_played < 10:
                        self.state.is_active = True
                    else:
                        self.new_sfx = self.sounds["you_did_it"]
                        self.state.is_active = False
                        self.game_level += 1
                        if self.game_level > self.max_game_level:
                            self.game_level = 1
                        self.state.rounds_played = 0
                    option.visible = False
                    option.highlight_good = True

                    # this below starts _new_round()
                    pygame.time.set_timer(pygame.USEREVENT, 1000)
                elif option.number != self.state.target_number and not self.state.answer_is_correct and not self.channel_sfx.get_busy():
                    self.state.feedback_text = f"No good!"
                    self.new_sfx = self.sounds["no_good"]
                    self.state.answered_incorrectly = True
                    option.highlight_bad = True
                    #

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
        if self.new_sfx:
            self.channel_sfx.play(self.new_sfx)
            self.new_sfx = None
        if self.new_music:
            self.channel_music.play(self.new_music)
            self.new_music = None
    
    def _draw_frame(self):
        self.screen.fill(COLORS["lightgray"])
        
        if self.state.is_active:
            # common screen assets
            self.screen.blit(self.prompt_text, self.prompt_rect)
            self.numbers_back_button.draw(self.screen, self.button_font)

            self._draw_options()
            self._draw_prompt()
            self._draw_score()
            self._draw_feedback()
            self._draw_transition(pygame.Rect(0, 0, self.screen_width, self.screen_height))
        else:
            # self._draw_overlay()
            self._draw_final_score()
            # self._restart_button_rect = self._draw_restart_button()
            self._restart_button_rect = self._draw_next_level_button()
        
        pygame.display.flip()

    def _draw_options(self):
        for i, option in enumerate(self.options):
            option.draw(self.screen, (100 + i * 350, 300))

    def _draw_prompt(self):
        prompt_head = ""
        prompt_tail = ""
        if self.game_level == 2 and self.state.target_number == 1:
            prompt_tail = " ball"
        elif self.game_level == 2 and self.state.target_number > 1:
            prompt_tail = " balls"
        elif self.game_level == 1:
            prompt_head = "number "
        else:
            prompt_tail = " number and balls"
        text = self.extra_large_font.render(f"{prompt_head}{NUMBERS.get(self.state.target_number)}{prompt_tail}", True, COLORS["red"])
        pygame.draw.rect(self.screen, COLORS["darkgray"], text.get_rect(center=(SCREEN_SIZE[0]//2, 100)).inflate(60, 0), border_radius=10)
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

    def _draw_transition(self, rect: pygame.Rect):
        if self.state.transition_progress < 1:
            alpha = int(self._interpolate(0, 255, self.state.transition_progress))
            # overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            print(overlay.get_size())
            overlay.fill((*COLORS["lightgray"][:3], alpha))
            # self.screen.blit(overlay, (0, 0))
            self.screen.blit(overlay, rect.topleft)

    # def _draw_overlay(self):
    #     overlay = pygame.Surface(SCREEN_SIZE, pygame.SRCALPHA)
    #     radius = self._interpolate(0, math.hypot(*SCREEN_SIZE), self.state.transition_progress)
    #     pygame.draw.circle(overlay, COLORS["overlay"], (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2), int(radius))
    #     self.screen.blit(overlay, (0, 0))

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
    
    def _draw_next_level_button(self) -> pygame.Rect:

        rect = pygame.Rect(0, 0, 400, 120)
        rect.center = (SCREEN_SIZE[0]//2, SCREEN_SIZE[1]//2 + 160)
        pygame.draw.rect(self.screen, COLORS["green"], rect, border_radius=10)
        text = self.normal_font.render("Next Level", True, COLORS["black"])
        self.screen.blit(text, text.get_rect(center=rect.center)) # type: ignore
        return rect

    def _draw_text_with_background(self, text: str, center: Tuple[int, int], color: Tuple[int, int, int]):
        text_surf = self.large_font.render(text, True, COLORS["black"])
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

    def play_music(self, music_file):
        """Plays background music, ensuring only one track is playing at a time."""
        if self.current_music != music_file:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(0.1)
                pygame.mixer.music.play(-1, fade_ms=1000)
                self.current_music = music_file
            except pygame.error as e:
                print(f"Error playing music {music_file}: {e}")

    def run_options(self):
        """Options screen place holder"""
        self.play_music(self.options_music)

        # Prompt text lower left corner
        prompt_text = self.text_font.render("Hint: Adjust the goal of the game.", True, COLORS["white"])
        prompt_rect = prompt_text.get_rect(bottomleft=(20, self.screen_height - 20))
        options_back_button = Button(self.screen_width - 200 - 20, 20, "Back", 200, 50, COLORS["darkred"])

        # --- Start of game mode init section ---

        # --- End of game mode init section ---

        while self.game_mode == "options" and self.running:
            self.clock.tick(60)
            self.screen.fill(COLORS["lightgray"])

            # --- Start of frame creation ---

            self.screen.blit(prompt_text, prompt_rect)
            options_back_button.draw(self.screen, self.button_font)

            # --- Start of frame creation ---

            # --- End of frame creation ---

            pygame.display.flip()

            # --- Event handlers ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # Toggle between fullscreen and windowed modes
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                        self.fullscreen, self.screen = toggle_fullscreen(self.screen, self.screen_width, self.screen_height, self.fullscreen)
                    elif event.key == pygame.K_ESCAPE:
                            self.game_mode = "menu"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if options_back_button.is_clicked(event.pos):
                        self.click_sound.play()
                        self.game_mode = "menu"

    def run_numbers(self):
        """Handles the words mode loop."""
        self.play_music(self.colors_music)
        
        # Back button upper right corner
        self.numbers_back_button = Button(self.screen_width - 200 - 20, 20, "Back", 200, 50, COLORS["darkred"])

        # Prompt text lower left corner        
        self.prompt_text = self.text_font.render("Hint: do this and that...", True, COLORS["white"])
        self.prompt_rect = self.prompt_text.get_rect(bottomleft=(20, self.screen_height - 20))

        # --- Start of game mode init section ---

        # --- End of game mode init section ---

        self._new_round()
        while (self.game_mode == "numbers" or self.game_mode == "balls") and self.running:
            self.clock.tick(60)
            self.screen.fill(COLORS["lightgray"])

            # --- Start of frame creation ---

            self._handle_input()
            self._update_state()
            self._draw_frame()
            self._process_audio()
            self.clock.tick(30)

            pygame.display.flip()

    def run_menu(self):
        """Handles the main menu loop."""
        self.play_music(self.menu_music)

        # Title text top center
        title_text = self.title_font.render("The Learning Numbers Game", True, COLORS["darkblue"])
        title_rect = title_text.get_rect(center=(self.screen_width // 2, self.screen_height // 8))

        # Prompt text lower left corner
        prompt_text = self.text_font.render("Hint: Tap or click on a button to start.", True, COLORS["white"])        
        prompt_rect = prompt_text.get_rect(bottomleft=(20, self.screen_height - 20))

        # Arrange buttons in a vertical stack centered on screen
        button_width = 300
        button_height = 50
        spacing = 20
        total_height = 4 * button_height + 3 * spacing
        start_y = self.screen_height // 2 - total_height // 2
        center_x = self.screen_width // 2 - button_width // 2

        menu_numbers_button = Button(center_x, start_y, "Numbers", button_width, button_height, COLORS["darkgreen"])
        menu_balls_button = Button(center_x, start_y + (button_height + spacing), "Balls", button_width, button_height, COLORS["darkgreen"])
        menu_quit_button = Button(center_x, start_y + (button_height + spacing) * 2, "Quit", button_width, button_height, COLORS["darkred"])

        play_menu_sound = False
        while self.game_mode == "menu" and self.running:
            self.clock.tick(60)
            self.screen.fill(COLORS["lightgray"])

            # Draw title and prompt at the top
            pygame.draw.rect(self.screen, COLORS["lightyellow"], title_rect.inflate(20, 10))
            self.screen.blit(title_text, title_rect)
            self.screen.blit(prompt_text, prompt_rect)

            # Draw buttons in center
            menu_numbers_button.draw(self.screen, self.button_font)
            menu_balls_button.draw(self.screen, self.button_font)
            menu_quit_button.draw(self.screen, self.button_font)

            pygame.display.flip()

            # Play welcome sound once
            if self.play_welcome_sound:
                welcome_sound = generate_speech_sound("Welcome to Learning Numbers Game!")
                welcome_sound.play()
                self.play_welcome_sound = False

            if play_menu_sound:
                menu_sound = generate_speech_sound("Menu screen sound goes here...")
                menu_sound.play()
                play_menu_sound = False
                while pygame.mixer.get_busy():
                    self.clock.tick(10)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                        self.fullscreen, self.screen = toggle_fullscreen(self.screen, self.screen_width, self.screen_height, self.fullscreen)
                    elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_numbers_button.is_clicked(event.pos):
                        self.click_sound.play()
                        self.game_mode = "numbers"
                    elif menu_balls_button.is_clicked(event.pos):
                        self.click_sound.play()
                        self.game_mode = "balls"
                    elif menu_quit_button.is_clicked(event.pos):
                        self.click_sound.play()
                        self.running = False

    def run(self):
        """Main game loop."""
        while self.running:
            if self.game_mode == "menu":
                self.run_menu()
            elif self.game_mode == "numbers":
                self.game_level = 1
                self.run_numbers()
            elif self.game_mode == "balls":
                self.game_level = 2
                self.run_numbers()
            self.clock.tick(60)
        pygame.quit()

if __name__ == '__main__':
    game = MainGame()
    game.run()
