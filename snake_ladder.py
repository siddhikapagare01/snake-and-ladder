# snack and ladders simulation game
# Features :
# - Board design (10*10)
# - Dice roll simulation
# - snack and ladders placement
# - Multiplayers support
# - optional: CLI-based; GUI can be added with Tkinter/pygame

import tkinter as tk 
import tkinter.simpledialog as simpledialog 
from tkinter import messagebox 
import random 
import json 
import os 
import threading 
import time 
import pygame 
import sys 
 
# Ini alize Pygame's mixer to play sound effects 
pygame.mixer.init() 
 
# Load a sound safely; return None if loading fails 
def load_sound(path): 
    try: 
        return pygame.mixer.Sound(path) 
    except Exception as e: 
        print(f"Warning: could not load sound '{path}': {e}") 
        return None 
 
# Load sound effects for snakes, ladders, and winning 
snake_sfx = load_sound("snake_hiss.mp3") 
ladder_sfx = load_sound("ladder_climb.mp3") 
win_sfx = load_sound("win_fanfare.mp3") 
 
 
 
# Constants for board layout 
CELL_WIDTH = 90 
CELL_HEIGHT = 70 
BOARD_SIZE = 10  # 10x10 board 
LEADERBOARD_FILE = "leaderboard.json"  # File to store top scores 
 
# Dic onary for snake start and end posi ons 
SNAKES = { 
    16: 6, 47: 26, 49: 11, 56: 53, 
    62: 19, 64: 60, 87: 24, 93: 73, 
    95: 75, 98: 78 
} 
 
# Dic onary for ladder start and end posi ons 
LADDERS = { 
    1: 38, 4: 14, 9: 31, 21: 42, 
    28: 84, 36: 44, 51: 67, 71: 91, 
    80: 100 
} 
 
# Main Game GUI class 
class GameGUI(tk.Tk): 
    def __init__(self, players): 
        super().__init__() 
        self.title("Snake & Ladders") 
        self.configure(bg="#e6f2ff")  # Light blue background 
        self.players = players 
        self.positions = {p: 0 for p in players}  # Start all players at cell 0 
        self.current = 0  # Index of current player 
        self.start_time =time.time()  # Record game start me 
 
        # Create main layout frame 
        main_frame = tk.Frame(self, bg="#e6f2ff") 
        main_frame.pack(padx=10, pady=10) 
 
        # Canvas for drawing the board 
        self.canvas = tk.Canvas( 
            main_frame, 
            width=CELL_WIDTH * BOARD_SIZE, 
            height=CELL_HEIGHT * BOARD_SIZE, 
            bg="#ffffff", highlightthickness=0 
        ) 
        self.canvas.grid(row=0, column=0) 
 
 #print("--------------------------------------------------------------------------------------------")
 
 
        self.draw_board()  # Draw grid, numbers, snakes & ladders 
        self.load_dice_images()  # Load dice images for animation 
 
        # Dice display area 
        self.dice_label = tk.Label(main_frame, bg="#e6f2ff") 
        self.dice_label.grid(row=0, column=1, padx=15) 
        self.dice_img_id = tk.Label( 
            self.dice_label, 
            image=self.dice_images[0],  # Default dice face 
            bg="#e6f2ff" 
        ) 
        self.dice_img_id.pack(pady=(CELL_HEIGHT * 2.5, 0))  # Ver cally centered 
 
        # Right-side control panel 
        ctrl = tk.Frame(main_frame, bg="#d9ead3", width=300, height=600) 
        ctrl.grid(row=0, column=2, sticky="ns") 
        ctrl.grid_propagate(False)  # Fix size 
 
        # Player turn info display 
        self.info = tk.Label( 
            ctrl, text="", font=("Helve ca", 14, "bold"), 
            bg="#d9ead3", fg="#333", wraplength=250, justify="center" 
        ) 
        self.info.pack(pady=30) 
 
        # Dice roll button 
        self.btn = tk.Button( 
            ctrl, 
            text=" Roll Dice", 
            command=self.roll_dice, 
            font=("Helvetica", 13, "bold"), 
            bg="#6fa8dc", fg="white", 
            activebackground="#3d85c6", 
            relief="raised", 
            padx=15, pady=10, 
            bd=3, cursor="hand2" 
        ) 
        self.btn.pack(pady=10) 
 
        # Assign colors and create player tokens 
        colors = ["red", "blue", "green", "orange", "purple"] 
        self.tokens = { 
            p: self.canvas.create_oval(-10, -10, -10, -10, fill=c) 
            for p, c in zip(players, colors) 
        } 
 
        self.update_info()  # Show ini al player turn 
 
    # Draw the game board with numbers, snakes, and ladders 
    def draw_board(self): 
        colors = ["#fce5cd", "#ffd966"]  # Alternate cell colors 
        for r in range(BOARD_SIZE): 
            for c in range(BOARD_SIZE): 
                x1, y1 = c * CELL_WIDTH, (BOARD_SIZE - 1 - r) * CELL_HEIGHT 
                x2, y2 = x1 + CELL_WIDTH, y1 + CELL_HEIGHT 
                fill_color = colors[(r + c) % 2] 
                self.canvas.create_rectangle( 
                    x1, y1, x2, y2, 
                    fill=fill_color, 
                    outline="black", width=2 
                ) 
                # Calculate cell number based on zigzag pa ern 
                num = r * BOARD_SIZE + (c + 1 if r % 2 == 0 else BOARD_SIZE - c) 
                self.canvas.create_text( 
                    x1 + CELL_WIDTH / 2, 
                    y1 + CELL_HEIGHT / 2, 
                    text=str(num), 
                    font=("Arial", 12, "bold") 
                ) 
 
        # Draw ladder lines 
        for s, e in LADDERS.items(): 
            self.draw_connector(s, e, "green") 
        # Draw snake lines 
        for s, e in SNAKES.items(): 
            self.draw_connector(s, e, "red") 
 
    # Draw arrow from start to end for ladders/snakes 
    def draw_connector(self, start, end, color): 
        x1, y1 = self.get_coords(start) 
        x2, y2 = self.get_coords(end) 
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=4, arrow=tk.LAST) 
 
    # Convert a board cell number to (x, y) pixel coordinates 
    def get_coords(self, pos): 
        r = (pos - 1) // BOARD_SIZE 
        i = (pos - 1) % BOARD_SIZE 
        c = i if r % 2 == 0 else BOARD_SIZE - 1 - i  # Zigzag column indexing 
        x = c * CELL_WIDTH + CELL_WIDTH // 2 
        y = (BOARD_SIZE - 1 - r) * CELL_HEIGHT + CELL_HEIGHT // 2 
        return x, y 
 
    # Load dice images from files named dice1.png to dice6.png 
    def load_dice_images(self): 
        self.dice_images = [tk.PhotoImage(file=f"dice{i}.png") for i in range(1, 7)] 
 
    # Handle dice rolling anima on and movement logic 
    def roll_dice(self): 
        self.btn.config(state=tk.DISABLED)  # Disable bu on during roll 
 
        # Animate dice roll in a separate thread 
        def animate(): 
            for _ in range(10):  # Fake spin 
                face = random.randint(1, 6) 
                self.dice_img_id.config(image=self.dice_images[face - 1]) 
                time.sleep(0.10) 
            roll = random.randint(1, 6) 
            self.dice_img_id.config(image=self.dice_images[roll - 1]) 
            self.after(100, lambda: self.after_roll(roll))  # Continue a er roll 
        threading.Thread(target=animate, daemon=True).start() 
 
    # A er dice is rolled, move player and check game logic 
    def after_roll(self, roll): 
        player = self.players[self.current] 
        start = self.positions[player] 
        end = start + roll 
 
        if end > 100: 
            # Cannot move beyond cell 100 
            self.btn.config(state=tk.NORMAL) 
            self.next_turn() 
            return 
 
        # Handle move anima on then check for snake/ladder/win 
        def after_normal_move(): 
            if end == 100: 
                self.positions[player] = end 
                self.update_token_position(player) 
                if win_sfx: 
                    win_sfx.play() 
                messagebox.showinfo(" Congratulations!", f"{player} won the game!") 
                duration = int( time.time() - self.start_me) 
                self.save_score(player, duration) 
                self.show_leaderboard() 
                return 
 
            # Check if landed on snake 
            if end in SNAKES: 
                if snake_sfx: 
                    snake_sfx.play() 
                self.animate_jump(player, end, SNAKES[end], callback=self.next_turn) 
            # Check if landed on ladder 
            elif end in LADDERS: 
                if ladder_sfx: 
                    ladder_sfx.play() 
                self.animate_jump(player, end, LADDERS[end], callback=self.next_turn) 
            else: 
                self.next_turn() 
 
        self.animate_movement(player, start, end, callback=after_normal_move) 
 
    # Animate player's normal forward movement 
    def animate_movement(self, player, start, end, callback=None): 
        path = list(range(start + 1, end + 1))  # Cells to move 
 
        def step(i): 
            if i >= len(path): 
                if callback: 
                    callback() 
                return 
            self.positions[player] = path[i] 
            self.update_token_position(player) 
            self.after(150, lambda: step(i + 1)) 
 
        step(0) 
 
    # Animate a jump due to snake or ladder 
    def animate_jump(self, player, from_pos, to_pos, callback=None): 
        x1, y1 = self.get_coords(from_pos) 
        x2, y2 = self.get_coords(to_pos) 
        steps = 10 
        dx = (x2 - x1) / steps 
        dy = (y2 - y1) / steps 
 
        def step(i): 
            if i > steps: 
                self.positions[player] = to_pos 
                self.update_token_position(player) 
                if self.positions[player] == 100: 
                    if win_sfx: 
                        win_sfx.play() 
                    messagebox.showinfo(" Congratulations!", f"{player} won the game!") 
                    duration = int(time.time() - self.start_time) 
                    self.save_score(player, duration) 
                    self.show_leaderboard() 
                    return 
                if callback: 
                    callback() 
                return 
            x = x1 + dx * i - CELL_WIDTH / 4 
            y = y1 + dy * i - CELL_HEIGHT / 4 
            self.canvas.coords( 
                self.tokens[player], x, y, x + CELL_WIDTH / 2, y + CELL_HEIGHT / 2 
            ) 
            self.after(100, lambda: step(i + 1)) 
 
        step(0) 
 
    # Update player token's position on board 
    def update_token_position(self, player): 
        pos = self.positions[player] 
        if pos == 0: 
            x = y = -10  # Start off-screen 
        else: 
            r = (pos - 1) // BOARD_SIZE 
            i = (pos - 1) % BOARD_SIZE 
            c = i if r % 2 == 0 else BOARD_SIZE - 1 - i 
            x = c * CELL_WIDTH + CELL_WIDTH / 4 
            y = (BOARD_SIZE - 1 - r) * CELL_HEIGHT + CELL_HEIGHT / 4 
        self.canvas.coords(self.tokens[player], x, y, x + CELL_WIDTH / 2, y + CELL_HEIGHT / 2) 
 
    # Update info label to show whose turn it is 
    def update_info(self): 
        self.info.config(text=f"{self.players[self.current]}'s turn") 
 
    # Move to next player's turn 
    def next_turn(self): 
        self.current = (self.current + 1) % len(self.players) 
        self.update_info() 
        self.btn.config(state=tk.NORMAL) 
 
    # Save the winning score to leaderboard JSON file 
    def save_score(self, player, duration): 
        entry = {"player": player, "me": duration} 
        lb = [] 
        if os.path.exists(LEADERBOARD_FILE): 
            lb = json.load(open(LEADERBOARD_FILE)) 
        lb.append(entry) 
        lb = sorted(lb, key=lambda e: e["me"])[:5]  # Top 5 scores 
        json.dump(lb, open(LEADERBOARD_FILE, "w"), indent=2) 
 
    # Display leaderboard in popup 
    def show_leaderboard(self): 
        lb = json.load(open(LEADERBOARD_FILE)) 
        text = " Leaderboard \n\n" 
        for i, e in enumerate(lb, 1): 
            text += f"{i}. {e['player']} — {e[' me']}s\n" 
        messagebox.showinfo("Leaderboard", text) 
        self.btn.config(state=tk.DISABLED) 
        self.show_end_options() 
 
    # Show restart option when game is over 
    def show_end_opotins(self): 
        response = messagebox.askquestion("Game Over", "Do you want to restart the game?") 
        if response == 'yes': 
            self.destroy() 
            os.execl(sys.executable, sys.executable, *sys.argv) 
        else: 
            self.quit() 
 
# Prompt user for player count and names, then start the game 
if __name__ == "__main__": 
    root = tk.Tk() 
    root.withdraw() 
    n = simpledialog.askinteger("Players", "Enter number of players (2–5):", minvalue=2, maxvalue=5) 
    names = [simpledialog.askstring("Name", f"Name for player {i+1}") or f"Player{i+1}" for i in range(n)] 
    root.destroy() 
    app = GameGUI(names) 
    app.mainloop()