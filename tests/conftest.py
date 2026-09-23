import os

# Render plots off-screen: tests must not open windows or require a display.
os.environ.setdefault("MPLBACKEND", "Agg")
