# gepad - Xbox pad -> keyboard/mouse for the Google Earth flight sim (macOS)

# Default: list recipes
default:
    @just --list

# Install dependencies (creates .venv via uv)
install:
    uv sync

# Fly! (Google Earth Pro: Cmd+Opt+A, joystick unchecked, click the map)
fly:
    uv run gepad

# Live view of axis and button numbers - for tuning src/gepad/config.py
debug:
    uv run gepad --debug

# Check whether the gamepad is visible
check:
    uv run python -c "import pygame; pygame.init(); pygame.joystick.init(); n = pygame.joystick.get_count(); print(f'Gamepads found: {n}'); [print(' -', pygame.joystick.Joystick(i).get_name()) for i in range(n)]"

# Remove the virtual environment
clean:
    rm -rf .venv
