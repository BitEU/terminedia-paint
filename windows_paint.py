#!/usr/bin/env python3
"""
Windows-compatible ASCII Art Paint Program
A simplified version of terminedia-paint that works on Windows
"""

import os
import sys
import time
import msvcrt
from typing import Tuple, List, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    import colorama
    from colorama import Fore, Back, Style
    colorama.init()
except ImportError:
    print("Please install colorama: pip install colorama")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Please install Pillow: pip install pillow")
    sys.exit(1)


@dataclass
class Point:
    x: int
    y: int
    
    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)


class Canvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.pixels = [[' ' for _ in range(width)] for _ in range(height)]
        self.colors = [[Fore.WHITE for _ in range(width)] for _ in range(height)]
        self.bg_colors = [[Back.BLACK for _ in range(width)] for _ in range(height)]
    
    def set_pixel(self, x: int, y: int, char: str = '█', color: str = Fore.WHITE, bg_color: str = Back.BLACK):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = char
            self.colors[y][x] = color
            self.bg_colors[y][x] = bg_color
    
    def get_pixel(self, x: int, y: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return ' '
    
    def clear(self):
        self.pixels = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.colors = [[Fore.WHITE for _ in range(self.width)] for _ in range(self.height)]
        self.bg_colors = [[Back.BLACK for _ in range(self.width)] for _ in range(self.height)]
    
    def draw_line(self, start: Point, end: Point, char: str = '█', color: str = Fore.WHITE):
        """Draw a line using Bresenham's algorithm"""
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        n = 1 + dx + dy
        x_inc = 1 if x1 > x0 else -1
        y_inc = 1 if y1 > y0 else -1
        error = dx - dy
        
        dx *= 2
        dy *= 2
        
        for _ in range(n):
            self.set_pixel(x, y, char, color)
            
            if error > 0:
                x += x_inc
                error -= dy
            else:
                y += y_inc
                error += dx
    
    def flood_fill(self, x: int, y: int, new_char: str = '█', new_color: str = Fore.WHITE):
        """Simple flood fill algorithm"""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        
        original_char = self.get_pixel(x, y)
        if original_char == new_char:
            return
        
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if cx < 0 or cx >= self.width or cy < 0 or cy >= self.height:
                continue
            if self.get_pixel(cx, cy) != original_char:
                continue
            
            self.set_pixel(cx, cy, new_char, new_color)
            stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])


class WindowsPainter:
    def __init__(self, width: int = 80, height: int = 24):
        self.canvas = Canvas(width, height)
        self.cursor = Point(0, 0)
        self.current_char = '█'
        self.current_color = Fore.WHITE
        self.current_bg = Back.BLACK
        self.drawing_mode = False
        self.last_point = None
        self.running = True
        
        # Available colors
        self.colors = [
            (Fore.WHITE, "White"),
            (Fore.RED, "Red"), 
            (Fore.GREEN, "Green"),
            (Fore.BLUE, "Blue"),
            (Fore.YELLOW, "Yellow"),
            (Fore.MAGENTA, "Magenta"),
            (Fore.CYAN, "Cyan"),
            (Fore.BLACK, "Black"),
        ]
        self.color_index = 0
        
        # Available characters
        self.chars = ['█', '▓', '▒', '░', '●', '○', '*', '#', '@', '+', '-', '|', '.', ' ']
        self.char_index = 0
        
        # Screen buffer to prevent flickering
        self.screen_buffer = []
        self.last_cursor = Point(-1, -1)
        self.needs_full_redraw = True
        
        # Initialize console
        os.system('cls')
        self.hide_cursor()
    
    def hide_cursor(self):
        """Hide the console cursor"""
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
    
    def show_cursor(self):
        """Show the console cursor"""
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
    
    def move_to(self, x: int, y: int):
        """Move cursor to specific position"""
        sys.stdout.write(f'\033[{y+1};{x+1}H')
        sys.stdout.flush()
    
    def clear_screen(self):
        """Clear the screen"""
        os.system('cls')
        self.needs_full_redraw = True
    
    def draw_canvas(self):
        """Draw the canvas to the screen with minimal flickering"""
        # Build current screen state
        current_screen = []
        
        # Draw the canvas
        for y in range(self.canvas.height):
            row = []
            for x in range(self.canvas.width):
                char = self.canvas.pixels[y][x]
                color = self.canvas.colors[y][x]
                bg_color = self.canvas.bg_colors[y][x]
                
                # Highlight cursor position
                if x == self.cursor.x and y == self.cursor.y:
                    if char == ' ':
                        char = '+'
                    cell = f"{Back.WHITE}{Fore.BLACK}{char}{Style.RESET_ALL}"
                else:
                    cell = f"{bg_color}{color}{char}{Style.RESET_ALL}"
                row.append(cell)
            current_screen.append(row)
        
        # Only redraw if this is the first time or if we need a full redraw
        if self.needs_full_redraw or not self.screen_buffer:
            self.move_to(0, 0)
            for y, row in enumerate(current_screen):
                self.move_to(0, y)
                print(''.join(row), end='')
            self.screen_buffer = [row[:] for row in current_screen]  # Deep copy
            self.needs_full_redraw = False
        else:
            # Only update changed cells
            for y in range(len(current_screen)):
                for x in range(len(current_screen[y])):
                    if (y >= len(self.screen_buffer) or 
                        x >= len(self.screen_buffer[y]) or 
                        current_screen[y][x] != self.screen_buffer[y][x]):
                        self.move_to(x, y)
                        print(current_screen[y][x], end='')
                        if y < len(self.screen_buffer) and x < len(self.screen_buffer[y]):
                            self.screen_buffer[y][x] = current_screen[y][x]
        
        # Update status line and help
        status_y = self.canvas.height + 1
        mode = "DRAW" if self.drawing_mode else "MOVE"
        color_name = self.colors[self.color_index][1]
        char_display = self.chars[self.char_index] if self.chars[self.char_index] != ' ' else 'SPACE'
        
        status_line = f"{Fore.CYAN}Mode: {mode} | Pos: ({self.cursor.x},{self.cursor.y}) | Color: {color_name} | Char: {char_display}{Style.RESET_ALL}"
        
        # Always update status line (but efficiently)
        self.move_to(0, status_y)
        print(' ' * 80, end='')  # Clear line
        self.move_to(0, status_y)
        print(status_line, end='')
        
        # Always show help text
        help_y = status_y + 2
        self.move_to(0, help_y)
        print(f"{Fore.YELLOW}Controls:{Style.RESET_ALL}")
        self.move_to(0, help_y + 1)
        print("Arrow Keys: Move cursor | Space: Toggle pixel | X: Toggle draw mode")
        self.move_to(0, help_y + 2)
        print("C: Change color | L: Change character | V: Line to last point")
        self.move_to(0, help_y + 3)
        print("F: Flood fill | S: Save | I: Load image | Q: Quit")
        
        self.last_cursor = Point(self.cursor.x, self.cursor.y)
        sys.stdout.flush()
    
    def handle_input(self):
        """Handle keyboard input"""
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            # Handle special keys (arrows, etc.)
            if key == b'\xe0':  # Special key prefix on Windows
                key = msvcrt.getch()
                if key == b'H':  # Up arrow
                    self.move_cursor(0, -1)
                elif key == b'P':  # Down arrow
                    self.move_cursor(0, 1)
                elif key == b'K':  # Left arrow
                    self.move_cursor(-1, 0)
                elif key == b'M':  # Right arrow
                    self.move_cursor(1, 0)
            else:
                # Handle regular keys
                key_char = key.decode('utf-8', errors='ignore').lower()
                
                if key_char == ' ':  # Space - toggle pixel
                    self.toggle_pixel()
                elif key_char == 'x':  # Toggle drawing mode
                    self.drawing_mode = not self.drawing_mode
                elif key_char == 'c':  # Change color
                    self.next_color()
                elif key_char == 'l':  # Change character
                    self.next_char()
                elif key_char == 'v':  # Line to last point
                    self.draw_line_to_last()
                elif key_char == 'f':  # Flood fill
                    self.flood_fill()
                elif key_char == 's':  # Save
                    self.save_canvas()
                elif key_char == 'i':  # Load image
                    self.load_image()
                elif key_char == 'q':  # Quit
                    self.running = False
                elif key_char == '\x1b':  # ESC
                    self.running = False
    
    def move_cursor(self, dx: int, dy: int):
        """Move the cursor"""
        new_x = max(0, min(self.canvas.width - 1, self.cursor.x + dx))
        new_y = max(0, min(self.canvas.height - 1, self.cursor.y + dy))
        
        # If in drawing mode, draw as we move
        if self.drawing_mode:
            self.canvas.draw_line(self.cursor, Point(new_x, new_y), self.current_char, self.current_color)
        
        self.cursor = Point(new_x, new_y)
    
    def toggle_pixel(self):
        """Toggle pixel at cursor position"""
        if self.canvas.get_pixel(self.cursor.x, self.cursor.y) == ' ':
            self.canvas.set_pixel(self.cursor.x, self.cursor.y, self.current_char, self.current_color, self.current_bg)
        else:
            self.canvas.set_pixel(self.cursor.x, self.cursor.y, ' ', Fore.WHITE, Back.BLACK)
        self.last_point = Point(self.cursor.x, self.cursor.y)
        # Mark canvas area for redraw
        self.invalidate_canvas_area()
    
    def invalidate_canvas_area(self):
        """Mark canvas area as needing redraw"""
        # Clear the screen buffer for the canvas area to force redraw
        if self.screen_buffer:
            for y in range(min(len(self.screen_buffer), self.canvas.height)):
                for x in range(min(len(self.screen_buffer[y]), self.canvas.width)):
                    self.screen_buffer[y][x] = None  # Mark as invalid
    
    def next_color(self):
        """Cycle to next color"""
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.current_color = self.colors[self.color_index][0]
    
    def next_char(self):
        """Cycle to next character"""
        self.char_index = (self.char_index + 1) % len(self.chars)
        self.current_char = self.chars[self.char_index]
    
    def draw_line_to_last(self):
        """Draw line to last point"""
        if self.last_point:
            self.canvas.draw_line(self.cursor, self.last_point, self.current_char, self.current_color)
            self.invalidate_canvas_area()
    
    def flood_fill(self):
        """Flood fill at cursor position"""
        self.canvas.flood_fill(self.cursor.x, self.cursor.y, self.current_char, self.current_color)
        self.invalidate_canvas_area()
    
    def save_canvas(self):
        """Save canvas to a text file"""
        try:
            filename = f"painting_{int(time.time())}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for y in range(self.canvas.height):
                    line = ''.join(self.canvas.pixels[y])
                    f.write(line.rstrip() + '\n')
            print(f"\n{Fore.GREEN}Saved to {filename}{Style.RESET_ALL}")
            time.sleep(1)
        except Exception as e:
            print(f"\n{Fore.RED}Error saving: {e}{Style.RESET_ALL}")
            time.sleep(1)
    
    def load_image(self):
        """Load an image and convert to ASCII"""
        try:
            filename = input(f"\n{Fore.CYAN}Enter image filename: {Style.RESET_ALL}")
            if not filename:
                return
            
            img = Image.open(filename)
            img = img.convert('L')  # Convert to grayscale
            
            # Resize to fit canvas
            img = img.resize((self.canvas.width, self.canvas.height))
            
            # Convert to ASCII
            chars = ' .:-=+*#%@'
            for y in range(img.height):
                for x in range(img.width):
                    pixel_value = img.getpixel((x, y))
                    char_index = int(pixel_value / 255 * (len(chars) - 1))
                    char = chars[char_index]
                    self.canvas.set_pixel(x, y, char, self.current_color, self.current_bg)
            
            self.needs_full_redraw = True  # Force full redraw
            print(f"\n{Fore.GREEN}Image loaded!{Style.RESET_ALL}")
            time.sleep(1)
        except Exception as e:
            print(f"\n{Fore.RED}Error loading image: {e}{Style.RESET_ALL}")
            time.sleep(1)
    
    def run(self):
        """Main game loop"""
        try:
            # Initial draw
            self.draw_canvas()
            
            while self.running:
                self.handle_input()
                self.draw_canvas()
                time.sleep(0.01)  # Reduced delay for more responsive cursor
        except KeyboardInterrupt:
            pass
        finally:
            self.show_cursor()
            self.clear_screen()
            print(f"{Fore.GREEN}Thanks for using Windows ASCII Paint!{Style.RESET_ALL}")


def run():
    """Entry point for the application"""
    try:
        painter = WindowsPainter(60, 20)  # Smaller default size for Windows console
        painter.run()
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    run()
