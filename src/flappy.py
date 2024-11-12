import asyncio
import sys
import time  # Import time for latency measurement
import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT
from prometheus_client import Gauge, start_http_server  # Import Prometheus client
import aiohttp  # Async HTTP client for network requests
import psutil  # To measure bandwidth usage
import boto3

from .entities import (
    Background,
    Floor,
    GameOver,
    Pipes,
    Player,
    PlayerMode,
    Score,
    WelcomeMessage,
)
from .utils import GameConfig, Images, Sounds, Window

class Flappy:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Flappy Bird")
        window = Window(288, 512)
        screen = pygame.display.set_mode((window.width, window.height))
        images = Images()

        self.config = GameConfig(
            screen=screen,
            clock=pygame.time.Clock(),
            fps=30,
            window=window,
            images=images,
            sounds=Sounds(),
        )

        # Initialize the font for the FPS display
        self.font = pygame.font.SysFont('Arial', 20)

        # Initialize Prometheus Gauges for FPS, Network Latency, and Bandwidth Usage
        self.fps_metric = Gauge('flappybird_fps', 'Frames Per Second of FlappyBird')
        self.network_latency_metric = Gauge('flappybird_network_latency', 'Network Latency in milliseconds')
        self.bandwidth_metric = Gauge('flappybird_bandwidth_usage', 'Bandwidth Usage in KB/s')

        # Start Prometheus HTTP server to serve metrics on port 8000
        start_http_server(8000)

        self.latency_check_interval = 5  # Measure network latency every 5 seconds
        self.last_latency_check = time.time()

        # Initialize variables for bandwidth usage calculation
        self.last_bytes_recv = 0
        self.last_bytes_sent = 0
        self.last_bandwidth_check = time.time()

    async def start(self):
        while True:
            self.background = Background(self.config)
            self.floor = Floor(self.config)
            self.player = Player(self.config)
            self.welcome_message = WelcomeMessage(self.config)
            self.game_over_message = GameOver(self.config)
            self.pipes = Pipes(self.config)
            self.score = Score(self.config)
            await self.splash()
            await self.play()
            await self.game_over()

    async def splash(self):
        """Shows welcome splash screen animation of flappy bird"""
        self.player.set_mode(PlayerMode.SHM)

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    return

            self.background.tick()
            self.floor.tick()
            self.player.tick()
            self.welcome_message.tick()

            # Display FPS on the screen and expose it to Prometheus
            self.display_and_track_fps()
            
            # Check if it's time to measure network latency
            if time.time() - self.last_latency_check >= self.latency_check_interval:
                asyncio.create_task(self.measure_network_latency())
                self.last_latency_check = time.time()

            # Check bandwidth usage every second
            if time.time() - self.last_bandwidth_check >= 1:
                await self.measure_bandwidth_usage()
                self.last_bandwidth_check = time.time()

            pygame.display.update()
            await asyncio.sleep(0)
            self.config.tick()

    def check_quit_event(self, event):
        if event.type == QUIT or (
            event.type == KEYDOWN and event.key == K_ESCAPE
        ):
            pygame.quit()
            sys.exit()

    def is_tap_event(self, event):
        m_left, _, _ = pygame.mouse.get_pressed()
        space_or_up = event.type == KEYDOWN and (
            event.key == K_SPACE or event.key == K_UP
        )
        screen_tap = event.type == pygame.FINGERDOWN
        return m_left or space_or_up or screen_tap

    async def play(self):
        self.score.reset()
        self.player.set_mode(PlayerMode.NORMAL)

        while True:
            if self.player.collided(self.pipes, self.floor):
                return

            for i, pipe in enumerate(self.pipes.upper):
                if self.player.crossed(pipe):
                    self.score.add()

            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    self.player.flap()  # Simulate action

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()
            self.player.tick()

            # Display FPS on the screen and expose it to Prometheus
            self.display_and_track_fps()

            # Check if it's time to measure network latency
            if time.time() - self.last_latency_check >= self.latency_check_interval:
                asyncio.create_task(self.measure_network_latency())
                self.last_latency_check = time.time()

            # Check bandwidth usage every second
            if time.time() - self.last_bandwidth_check >= 1:
                await self.measure_bandwidth_usage()
                self.last_bandwidth_check = time.time()

            pygame.display.update()
            await asyncio.sleep(0)  # Use a minimal delay to keep the loop responsive
            self.config.tick()

    async def game_over(self):
        """Crashes the player down and shows gameover image"""
        self.player.set_mode(PlayerMode.CRASH)
        self.pipes.stop()
        self.floor.stop()

        while True:
            for event in pygame.event.get():
                self.check_quit_event(event)
                if self.is_tap_event(event):
                    if self.player.y + self.player.h >= self.floor.y - 1:
                        return

            self.background.tick()
            self.floor.tick()
            self.pipes.tick()
            self.score.tick()
            self.player.tick()
            self.game_over_message.tick()

            # Display FPS on the screen and expose it to Prometheus
            self.display_and_track_fps()

            self.config.tick()
            pygame.display.update()
            await asyncio.sleep(0)

    async def measure_network_latency(self):
        """Measure the network latency by sending a request to a specified endpoint."""
        url = "http://localhost:8000/metrics"  # Change this to your target URL

        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()  # Start the timer
                async with session.get(url) as response:
                    await response.text()  # Await the response to complete
                    end_time = time.time()  # End the timer
                
                # Calculate latency in milliseconds
                latency = (end_time - start_time) * 1000
                self.network_latency_metric.set(latency)  # Set the network latency to Prometheus
        except Exception as e:
            print(f"Network request failed: {e}")  # Log the error

    async def measure_bandwidth_usage(self):
        """Measure the bandwidth usage by tracking bytes sent and received."""
        net_io = psutil.net_io_counters()
        current_bytes_recv = net_io.bytes_recv
        current_bytes_sent = net_io.bytes_sent

        # Calculate the difference since the last check
        bytes_recv = current_bytes_recv - self.last_bytes_recv
        bytes_sent = current_bytes_sent - self.last_bytes_sent

        # Update last bytes counters
        self.last_bytes_recv = current_bytes_recv
        self.last_bytes_sent = current_bytes_sent

        # Calculate bandwidth usage in KB/s
        bandwidth_usage = (bytes_recv + bytes_sent) / 1024  # Convert bytes to KB

        # Update the metric
        self.bandwidth_metric.set(bandwidth_usage)  # Set total bandwidth usage in KB/s

    def display_and_track_fps(self):
        """Renders the FPS on the screen and exposes it to Prometheus."""
        fps = int(self.config.clock.get_fps())
        fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 255))
        self.config.screen.blit(fps_text, (10, 10))  # Display FPS at top-left corner
        
        # Expose FPS to Prometheus
        self.fps_metric.set(fps)

# Start the game
if __name__ == "__main__":
    flappy_game = Flappy()
    asyncio.run(flappy_game.start())
