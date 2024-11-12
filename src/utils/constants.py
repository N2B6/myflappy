# constants.py

# Base URL for S3 assets
S3_BASE_URL = "https://23202513b.s3.eu-west-1.amazonaws.com/assets/"

# List of all possible players (tuple of 3 positions of flap)
PLAYERS = (
    # red bird
    (
        f"sprites/redbird-upflap.png",
        f"sprites/redbird-midflap.png",
        f"sprites/redbird-downflap.png",
    ),
    # blue bird
    (
        f"sprites/bluebird-upflap.png",
        f"sprites/bluebird-midflap.png",
        f"sprites/bluebird-downflap.png",
    ),
    # yellow bird
    (
        f"sprites/yellowbird-upflap.png",
        f"sprites/yellowbird-midflap.png",
        f"sprites/yellowbird-downflap.png",
    ),
)

# List of backgrounds
BACKGROUNDS = (
    f"sprites/background-day.png",
    f"sprites/background-night.png",
)

# List of pipes
PIPES = (
    f"sprites/pipe-green.png",
    f"sprites/pipe-red.png",
)