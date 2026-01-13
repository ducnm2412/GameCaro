import socket
import threading
import sys
from game_logic import Board, apply_move, check_win, is_full

# --- Cấu hình  ---
HOST = '0.0.0.0'
PORT = 12345

clients_lock = threading.Lock()
waiting = []

# --- Gửi thông điệp từ server đến client ---

def send(conn, msg):
    try:
        conn.sendall((msg + "\n").encode())
    except:
        pass
# --- Nhận thông điệp từ client đến server ---
def recv(conn):
    try:
        data = conn.recv(1024)
        if not data: return None
        return data.decode().strip()
    except:
        return None

# --- Xử lý kết nối giữa hai người chơi ---

def handle_match(p1, p2):
    conn1, addr1 = p1
    conn2, addr2 = p2
    
    symbols = {conn1: 'X', conn2: 'O'}
    rematch_status = {conn1: False, conn2: False}

    while True:
        board = Board(size=15)
        rematch_status[conn1] = False
        rematch_status[conn2] = False
        
        send(conn1, "START X")
        send(conn2, "START O")
        
        send(conn1, "RESET") 
        send(conn2, "RESET")

        current = conn1
        other = conn2
        send(current, "YOUR TURN")

        game_active = True 

        while True:
            data = recv(current)
            if data is None:
                send(other, "OPPONENT_LEFT")
                return 

            parts = data.split()
            if not parts: continue
            cmd = parts[0]

            if cmd == "CHAT":
                msg = " ".join(parts[1:])
                send(other, f"CHAT {msg}")

            elif cmd == "REMATCH":
                if not game_active:
                    rematch_status[current] = True
                    # Notify opponent via chat
                    send(other, "CHAT [System]: Opponent wants a rematch!")
                    
                    # Check if both accepted
                    if rematch_status[conn1] and rematch_status[conn2]:
                        break # Break Game Loop to restart Session Loop

            # 3. Handle Move
            elif cmd == "MOVE" and len(parts) == 3 and game_active:
                try:
                    x, y = int(parts[1]), int(parts[2])
                except: continue

                sym = symbols[current]
                ok, reason = apply_move(board, x, y, sym)
                
                if not ok:
                    send(current, f"INVALID {reason}")
                    continue

                send(other, f"OPPONENT {x} {y}")

                if check_win(board, x, y):
                    send(current, "WIN")
                    send(other, "LOSE")
                    game_active = False
                elif is_full(board):
                    send(current, "DRAW")
                    send(other, "DRAW")
                    game_active = False
                else:
                    send(other, "YOUR TURN")
                    current, other = other, current
            
            # 4. Handle Exit
            elif cmd == "EXIT":
                send(other, "OPPONENT_LEFT")
                return
            
            # Allow polling both clients when game is over
            if not game_active:
                current, other = other, current

    conn1.close()
    conn2.close()

# --- Xử lý kết nối từ client ---

def client_thread(conn, addr):
    print(f"[+] Connected {addr}")
    with clients_lock:
        waiting.append((conn, addr))
        if len(waiting) >= 2:
            p1 = waiting.pop(0)
            p2 = waiting.pop(0)
            threading.Thread(target=handle_match, args=(p1, p2), daemon=True).start()

# --- Chương trình chính ---

def main():
    global HOST, PORT
    if len(sys.argv) >= 2:
        PORT = int(sys.argv[1])
        
    print(f"Starting server on {HOST}:{PORT}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    
    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=client_thread, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server.")
    finally:
        s.close()

if __name__ == "__main__":
    main()