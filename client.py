import socket
import sys
import os 


def clear_screen():
    """Clears the terminal screen."""
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')

def print_board(board):
    """Prints the 2D board list to the console beautifully."""
    size = len(board)
    # Tạo header cột với căn trái khoảng 2 ký tự cho từng chỉ số cột
    header = "   " + " ".join([f"{i:<2}" for i in range(size)])
    print(header)
    
    for r_idx, row in enumerate(board):
        # In chỉ số hàng, sau đó là trạng thái từng ô
        print(f"{r_idx:<2} " + " ".join(row))

def redraw_screen(board, message=""):
    """Clears the screen and redraws the entire UI."""
    clear_screen()
    print("--- WELCOME TO GOMOKU (CARO) ---")
    if message:
        print(f"\n[STATUS]: {message}\n")
    else:
        print("\n") 
    
    print_board(board)
    print("\n") 

def get_move_and_send(s, board, my_symbol):
    """
    Loops until the user enters valid syntax AND valid board coordinates.
    """
    size = len(board) 
    
    while True:
        try:
            move = input("Enter move (row col): ")
            x, y = map(int, move.strip().split())

            if not (0 <= x < size and 0 <= y < size):
                print(f"[INPUT ERROR]: Coordinates must be between 0 and {size-1}. Try again.")
                continue 

            previous_value = board[x][y]

            if previous_value != '.':
                print("[INPUT ERROR]: Cell is already occupied. Try again.")
                continue

            # Gửi lệnh định dạng đơn giản tới server: "MOVE x y"
            # (Server chịu trách nhiệm kiểm tra hợp lệ/kiểm tra luật)
            s.sendall(f"MOVE {x} {y}\n".encode())
            
            # Optimistic update: cập nhật bàn cờ bên client ngay lập tức
            # để người chơi thấy kết quả ngay, trước khi server xác nhận.
            # Nếu server trả INVALID, chúng ta sẽ hoàn tác lại (revert).
            board[x][y] = my_symbol
            
            # Trả về tọa độ và giá trị trước đó để có thể hoàn tác khi cần
            return x, y, previous_value 
        
        except ValueError: 
            print("[INPUT ERROR]: Please enter two NUMBERS separated by a space. Try again.")


def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <host> <port>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    my_symbol = None
    # Khởi tạo bàn 15x15 với '.' biểu thị ô trống
    board = [['.' for _ in range(15)] for _ in range(15)]
    last_move_info = None
    
    status_message = "Connecting to server..." 

    try:
        while True:
            # Nhận dữ liệu từ server. Lưu ý: đây đọc tối đa 1024 byte mỗi lần
            data = s.recv(1024).decode().strip()
            if not data:
                print("Disconnected from server.")
                break

            for line in data.split('\n'):
                parts = line.strip().split()
                if not parts:
                    continue

                cmd = parts[0]

                if cmd == "START":
                    # START <symbol>: server thông báo ký hiệu của client ('X' hoặc 'O')
                    my_symbol = parts[1]
                    status_message = f"Game started! You are '{my_symbol}'."
                    redraw_screen(board, status_message) 

                elif cmd == "YOUR":
                    # Đến lượt client: hiển thị trạng thái và gọi hàm nhập nước đi
                    status_message = "It's your turn."
                    redraw_screen(board, status_message) 
                    
                    # Hàm trả về (x, y, previous_value) để có thể revert nếu INVALID
                    last_move_info = get_move_and_send(s, board, my_symbol)
                    
                    status_message = "Move sent, waiting for opponent..."
                    redraw_screen(board, status_message) 

                elif cmd == "OPPONENT":
                    # OPPONENT x y: server thông báo nước đi của đối thủ
                    x, y = int(parts[1]), int(parts[2])
                    opp_symbol = 'O' if my_symbol == 'X' else 'X'
                    board[x][y] = opp_symbol 
                    
                    status_message = f"Opponent moved to ({x}, {y})"
                    redraw_screen(board, status_message) 

                elif cmd == "INVALID":
                    # INVALID <reason>: server từ chối nước đi vừa gửi.
                    # Lý do có thể là vi phạm luật hoặc trùng ô do cạnh tranh đồng thời.
                    invalid_reason = ' '.join(parts[1:])
                    
                    # Nếu trước đó chúng ta đã làm optimistic update, hoàn tác lại
                    if last_move_info:
                        lx, ly, previous_value = last_move_info
                        board[lx][ly] = previous_value 
                        last_move_info = None
                    
                    status_message = f"Invalid move: {invalid_reason}. Your last move was reverted."
                    redraw_screen(board, status_message) 
                    
                    # Yêu cầu người chơi nhập lại ngay lập tức (vẫn lượt của họ)
                    status_message = "It's still your turn. Please enter a valid move."
                    print(f"\n[STATUS]: {status_message}\n") 
                    
                    last_move_info = get_move_and_send(s, board, my_symbol)
                    
                    status_message = "New move sent, waiting for opponent..."
                    redraw_screen(board, status_message) 

                elif cmd == "WIN":
                    clear_screen() 
                    print_board(board)
                    print("\n================\n    You win!    \n================\n")
                    return 

                elif cmd == "LOSE":
                    clear_screen() 
                    print_board(board)
                    print("\n================\n    You lose!   \n================\n")
                    return

                elif cmd == "DRAW":
                    clear_screen() 
                    print_board(board)
                    print("\n================\n  Game is a draw. \n================\n")
                    return

                elif cmd == "OPPONENT_LEFT":
                    clear_screen() 
                    print_board(board)
                    print("\n================\n Opponent disconnected. \n================\n")
                    return 
    
    except ConnectionAbortedError:
        print("Connection was aborted.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    main()