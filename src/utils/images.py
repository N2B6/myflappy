import random
from typing import List, Tuple
import pygame
import requests
from io import BytesIO
from .constants import BACKGROUNDS, PIPES, PLAYERS, S3_BASE_URL

class Images:
    def __init__(self) -> None:
        # Load number sprites from S3
        self.numbers = [
            self.load_image_from_url(f"{S3_BASE_URL}sprites/{num}.png")
            for num in range(10)
        ]

        # Load game over sprite
        self.game_over = self.load_image_from_url(f"{S3_BASE_URL}sprites/gameover.png")

        # Load welcome message sprite
        self.welcome_message = self.load_image_from_url(f"{S3_BASE_URL}sprites/message.png")

        # Load base (ground) sprite
        self.base = self.load_image_from_url(f"{S3_BASE_URL}sprites/base.png")

        # Randomize other sprites (background, player, pipe)
        self.randomize()

    def load_image_from_url(self, url: str) -> pygame.Surface:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            image_data = BytesIO(response.content)
            return pygame.image.load(image_data).convert_alpha()  # Load the image from byte data
        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred while loading image from {url}: {e}")
        return None  # Return None if there was an error

    def randomize(self):
        # Select random background, player, and pipe sprites
        rand_bg = random.randint(0, len(BACKGROUNDS) - 1)
        rand_player = random.randint(0, len(PLAYERS) - 1)
        rand_pipe = random.randint(0, len(PIPES) - 1)

        # Load background from S3
        self.background = self.load_image_from_url(f"{S3_BASE_URL}{BACKGROUNDS[rand_bg]}")

        # Load player sprites from S3
        self.player = (
            self.load_image_from_url(f"{S3_BASE_URL}{PLAYERS[rand_player][0]}"),
            self.load_image_from_url(f"{S3_BASE_URL}{PLAYERS[rand_player][1]}"),
            self.load_image_from_url(f"{S3_BASE_URL}{PLAYERS[rand_player][2]}"),
        )

        # Load pipe sprites from S3 and apply transformation for flipping
        pipe_surface = self.load_image_from_url(f"{S3_BASE_URL}{PIPES[rand_pipe]}")
        if pipe_surface is not None:
            self.pipe = (
                pygame.transform.flip(pipe_surface, False, True),
                pipe_surface,
            )
        else:
            self.pipe = (None, None)