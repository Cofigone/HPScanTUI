"""Main entry point for the hpscancli package.
"""
from tui import hpscantui

app = hpscantui()

if __name__ == "__main__":
    app.run()