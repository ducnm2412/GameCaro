# client_gui.py
import socket
import sys
import threading
import pygame
import time

# --- Game Settings ---
GRID_SIZE = 15
CELL_SIZE = 40
MARGIN = 20
INFO_HEIGHT = 60
BOARD_WIDTH = GRID_SIZE * CELL_SIZE + MARGIN * 2
CHAT_WIDTH = 300
SCREEN_WIDTH = BOARD_WIDTH + CHAT_WIDTH
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + MARGIN * 2 + INFO_HEIGHT

# --- Colors (CYBER DARK THEME - CUSTOM) ---
COLOR_BG = (18, 22, 30)
COLOR_GRID = (60, 70, 90)
COLOR_X = (0, 220, 255)
COLOR_O = (255, 150, 60)
COLOR_HIGHLIGHT = (80, 80, 120)
COLOR_TEXT = (220, 220, 230)
COLOR_INFO_BG = (25, 30, 45)
COLOR_CHAT_BG = (30, 36, 55)
COLOR_INPUT_BG = (20, 25, 40)
COLOR_BORDER = (90, 100, 130)

COLOR_BTN_NORMAL = (0, 160, 200)
COLOR_BTN_HOVER = (0, 200, 255)
COLOR_OVERLAY = (0, 0, 0, 180)

# --- Global State ---
board = [['.' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
my_symbol = None
is_my_turn = False
game_over = False
status_message = "Connecting to server..."
last_player_move = None
last_optimistic_move = None
sock = None

# --- Rematch State ---
game_over_time = 0
rematch_sent = False
TIMEOUT_SECONDS = 15

# --- Chat State ---
chat_history = []
input_text = ""
MAX_CHAT_LINES = 18

# --- Drawing Functions ---
def draw_button(screen, font, rect, text, is_hover):
    color = COLOR_BTN_HOVER if is_hover else COLOR_BTN_NORMAL
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, COLOR_BORDER, rect, 2, border_radius=12)
    txt = font.render(text, True, (255, 255, 255))
    screen.blit(txt, txt.get_rect(center=rect.center))

def draw_X(screen, center):
    offset = CELL_SIZE // 4
    pygame.draw.line(screen, COLOR_X,
                     (center[0]-offset, center[1]-offset),
                     (center[0]+offset, center[1]+offset), 6)
    pygame.draw.line(screen, COLOR_X,
                     (center[0]-offset, center[1]+offset),
                     (center[0]+offset, center[1]-offset), 6)

def draw_O(screen, center):
    radius = CELL_SIZE // 3
    pygame.draw.circle(screen, COLOR_O, center, radius, width=6)

def draw_game(screen, font_game, font_chat):
    screen.fill(COLOR_BG)

    if last_player_move:
        r, c = last_player_move
        pygame.draw.rect(
            screen, COLOR_HIGHLIGHT,
            (MARGIN + c * CELL_SIZE, MARGIN + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        )

    for i in range(GRID_SIZE + 1):
        pygame.draw.line(screen, COLOR_GRID,
            (MARGIN + i * CELL_SIZE, MARGIN),
            (MARGIN + i * CELL_SIZE, MARGIN + GRID_SIZE * CELL_SIZE), 2)
        pygame.draw.line(screen, COLOR_GRID,
            (MARGIN, MARGIN + i * CELL_SIZE),
            (MARGIN + GRID_SIZE * CELL_SIZE, MARGIN + i * CELL_SIZE), 2)

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            center = (
                MARGIN + c * CELL_SIZE + CELL_SIZE // 2,
                MARGIN + r * CELL_SIZE + CELL_SIZE // 2
            )
            if board[r][c] == 'X': draw_X(screen, center)
            elif board[r][c] == 'O': draw_O(screen, center)

    info_rect = (0, SCREEN_HEIGHT - INFO_HEIGHT, BOARD_WIDTH, INFO_HEIGHT)
    if not (game_over and not status_message.startswith("Opponent Left")):
        pygame.draw.rect(screen, COLOR_INFO_BG, info_rect)

    pygame.draw.line(screen, COLOR_GRID,
        (0, SCREEN_HEIGHT - INFO_HEIGHT),
        (BOARD_WIDTH, SCREEN_HEIGHT - INFO_HEIGHT), 1)

    txt = font_game.render(status_message, True, COLOR_TEXT)
    screen.blit(txt, txt.get_rect(
        center=(BOARD_WIDTH // 2, SCREEN_HEIGHT - INFO_HEIGHT // 2)))

    pygame.draw.rect(screen, COLOR_CHAT_BG,
        (BOARD_WIDTH, 0, CHAT_WIDTH, SCREEN_HEIGHT))
    pygame.draw.line(screen, COLOR_BORDER,
        (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 2)

    title = font_game.render("CHAT ROOM", True, COLOR_X)
    screen.blit(title, (BOARD_WIDTH + 20, 10))

    y = 50
    for line in chat_history[-MAX_CHAT_LINES:]:
        color = COLOR_X if line.startswith("Me:") else COLOR_O
        screen.blit(font_chat.render(line, True, color),
                    (BOARD_WIDTH + 10, y))
        y += 25

    input_rect = (BOARD_WIDTH + 10, SCREEN_HEIGHT - 40, CHAT_WIDTH - 20, 30)
    pygame.draw.rect(screen, COLOR_INPUT_BG, input_rect)
    pygame.draw.rect(screen, COLOR_BORDER, input_rect, 1)
    screen.blit(font_chat.render(input_text, True, COLOR_TEXT),
                (input_rect[0] + 5, input_rect[1] + 5))

    if game_over and not status_message.startswith("Opponent Left"):
        elapsed = (pygame.time.get_ticks() - game_over_time) / 1000
        remaining = max(0, TIMEOUT_SECONDS - elapsed)
        if remaining > 0:
            overlay = pygame.Surface((BOARD_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(COLOR_OVERLAY)
            screen.blit(overlay, (0, 0))

            btn_rect = pygame.Rect(
                (BOARD_WIDTH - 180)//2,
                (SCREEN_HEIGHT - INFO_HEIGHT)//2,
                180, 60
            )
            mouse_pos = pygame.mouse.get_pos()
            hover = btn_rect.collidepoint(mouse_pos)
            label = "WAITING..." if rematch_sent else f"PLAY AGAIN ({int(remaining)})"
            draw_button(screen, font_game, btn_rect, label, hover)

    pygame.display.flip()

def pixel_to_grid(pos):
    x, y = pos
    if x > BOARD_WIDTH: return None
    if x < MARGIN or y < MARGIN or y > SCREEN_HEIGHT - INFO_HEIGHT - MARGIN:
        return None
    return (y - MARGIN) // CELL_SIZE, (x - MARGIN) // CELL_SIZE

# --- Network Thread ---
def network_thread():
    global board, my_symbol, is_my_turn, game_over, status_message
    global last_optimistic_move, last_player_move, chat_history
    global game_over_time, rematch_sent

    try:
        while True:
            data = sock.recv(1024).decode().strip()
            if not data:
                status_message = "Disconnected."
                game_over = True
                break

            for line in data.split('\n'):
                parts = line.split()
                if not parts: continue
                cmd = parts[0]

                if cmd == "START":
                    my_symbol = parts[1]
                    status_message = f"You are '{my_symbol}'"
                elif cmd == "YOUR":
                    is_my_turn = True
                    status_message = "Your move ⚡"
                elif cmd == "OPPONENT":
                    r, c = int(parts[1]), int(parts[2])
                    board[r][c] = 'O' if my_symbol == 'X' else 'X'
                    last_player_move = (r, c)
                    status_message = "Opponent moved"
                elif cmd == "INVALID":
                    status_message = "Invalid move!"
                    if last_optimistic_move:
                        r, c = last_optimistic_move
                        board[r][c] = '.'
                        last_optimistic_move = None
                    is_my_turn = True
                elif cmd == "CHAT":
                    chat_history.append("Opp: " + " ".join(parts[1:]))
                elif cmd == "RESET":
                    board[:] = [['.' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    game_over = False
                    rematch_sent = False
                    status_message = "New Game Started!"
                elif cmd in ("WIN", "LOSE", "DRAW", "OPPONENT_LEFT"):
                    game_over = True
                    game_over_time = pygame.time.get_ticks()
                    status_message = {
                        "WIN": "YOU WIN 🔥",
                        "LOSE": "YOU LOSE ❌",
                        "DRAW": "DRAW GAME",
                        "OPPONENT_LEFT": "Opponent Left"
                    }[cmd]
    except:
        game_over = True
        status_message = "Connection error"

# --- Main Loop ---
def main():
    global sock, input_text, rematch_sent, last_player_move, is_my_turn

    if len(sys.argv) != 3:
        print("Usage: python client_gui.py <host> <port>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    pygame.init()
    font_game = pygame.font.SysFont("Consolas", 22, bold=True)
    font_chat = pygame.font.SysFont("Arial", 16)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyber Caro Online")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    threading.Thread(target=network_thread, daemon=True).start()

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and input_text.strip():
                    sock.sendall(f"CHAT {input_text}\n".encode())
                    chat_history.append("Me: " + input_text)
                    input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    if len(input_text) < 30:
                        input_text += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over and not rematch_sent:
                    bx = (BOARD_WIDTH - 180)//2
                    by = (SCREEN_HEIGHT - INFO_HEIGHT)//2
                    if bx < event.pos[0] < bx+180 and by < event.pos[1] < by+60:
                        sock.sendall("REMATCH\n".encode())
                        rematch_sent = True

                elif not game_over and is_my_turn:
                    pos = pixel_to_grid(event.pos)
                    if pos:
                        r, c = pos
                        if board[r][c] == '.':
                            board[r][c] = my_symbol
                            last_player_move = (r, c)
                            sock.sendall(f"MOVE {r} {c}\n".encode())
                            is_my_turn = False
                            status_message = "Opponent thinking..."

        draw_game(screen, font_game, font_chat)
        clock.tick(60)

    pygame.quit()
    sock.close()

if __name__ == "__main__":
    main()
