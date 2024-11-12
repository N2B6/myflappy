import sys
import pygame
import requests
from io import BytesIO
from .constants import S3_BASE_URL  # Import the base URL from your constants

class Sounds:
    die: pygame.mixer.Sound
    hit: pygame.mixer.Sound
    point: pygame.mixer.Sound
    swoosh: pygame.mixer.Sound
    wing: pygame.mixer.Sound

    def __init__(self) -> None:
        # Initialize the mixer
        pygame.mixer.init()

        # Determine the audio file extension based on the platform
        ext = "wav" if "win" in sys.platform else "ogg"

        # Load sounds from S3 using the base URL
        self.die = self.load_sound(f"{S3_BASE_URL}audio/die.{ext}")
        self.hit = self.load_sound(f"{S3_BASE_URL}audio/hit.{ext}")
        self.point = self.load_sound(f"{S3_BASE_URL}audio/point.{ext}")
        self.swoosh = self.load_sound(f"{S3_BASE_URL}audio/swoosh.{ext}")
        self.wing = self.load_sound(f"{S3_BASE_URL}audio/wing.{ext}")

    def load_sound(self, url: str) -> pygame.mixer.Sound:
        """Load a sound file from a URL with error handling."""
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            sound_data = BytesIO(response.content)  # Create a byte stream from the response content
            return pygame.mixer.Sound(sound_data)  # Load the sound from byte data
        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred while loading sound from {url}: {e}")
        return None  # Return None if loading fails

    def play_sound(self, sound: pygame.mixer.Sound):
        """Play a sound if it was loaded successfully."""
        if sound:
            sound.play()