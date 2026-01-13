# game_logic.py

def Board(size=15):
    """Tạo bàn cờ rỗng kích thước size x size."""
    return [['.' for _ in range(size)] for _ in range(size)]

def in_bounds(size, x, y):
    """Kiểm tra tọa độ (x, y) có nằm trong bàn cờ không."""
    return 0 <= x < size and 0 <= y < size

def apply_move(board, x, y, symbol):
    """Cập nhật nước đi vào bàn cờ nếu hợp lệ."""
    size = len(board)
    if not in_bounds(size, x, y):
        return False, "Out of bounds"
    if board[x][y] != '.':
        return False, "Cell occupied"
    board[x][y] = symbol
    return True, None

def check_win(board, x, y):
    """
    Kiểm tra điều kiện thắng: Đủ 5 quân liên tiếp và không bị chặn 2 đầu.
    """
    size = len(board)
    sym = board[x][y]
    if sym == '.':
        return False
    
    # 4 hướng: Ngang, Dọc, Chéo Chính, Chéo Phụ
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dx, dy in directions:
        # Kiểm tra hướng dương
        count_pos = 0
        cx, cy = x + dx, y + dy
        while in_bounds(size, cx, cy) and board[cx][cy] == sym:
            count_pos += 1
            cx += dx
            cy += dy
        
        blocked_pos = False
        if in_bounds(size, cx, cy):
            cell_val = board[cx][cy]
            if cell_val != '.' and cell_val != sym:
                blocked_pos = True

        # Kiểm tra hướng âm
        count_neg = 0
        cx, cy = x - dx, y - dy
        while in_bounds(size, cx, cy) and board[cx][cy] == sym:
            count_neg += 1
            cx -= dx
            cy -= dy
        
        blocked_neg = False
        if in_bounds(size, cx, cy):
            cell_val = board[cx][cy]
            if cell_val != '.' and cell_val != sym:
                blocked_neg = True

        # Tổng số quân
        total = 1 + count_pos + count_neg
        
        # Điều kiện thắng: >= 5 quân và không bị chặn cả 2 đầu
        if total >= 5:
            if not (blocked_pos and blocked_neg):
                return True
                
    return False

def is_full(board):
    """Kiểm tra xem bàn cờ đã đầy chưa (Hòa)."""
    for row in board:
        if '.' in row:
            return False
    return True

def board_to_string(board):
    """Chuyển trạng thái bàn cờ thành chuỗi (để debug)."""
    size = len(board)
    lines = ["   " + " ".join([f"{i:2}" for i in range(size)])]
    for i, row in enumerate(board):
        lines.append(f"{i:2} " + " ".join(row))
    return "\n".join(lines)