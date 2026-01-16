

Trò chơi Caro (Gomoku) cho 2 người chơi qua mạng, hỗ trợ giao diện GUI đẹp với Pygame.


- **Server** (`server.py`): Quản lý kết nối, ghép cặp người chơi, xử lý logic trò chơi
- **Client GUI** (`client_gui.py`): Giao diện đồ họa với Pygame, có chat và rematch
- **Client Console** (`client.py`): Giao diện dòng lệnh đơn giản



## Cài đặt

```bash
pip install pygame
```

---

## Cách Chạy

### **Bước 1: Mở 3 Terminal riêng biệt**

## Terminal 1 - Chạy Server:

```bash
python server.py
```

## Terminal 2 - Chạy Client GUI 1 (Người X):

```bash
python client_gui.py localhost 12345
```

## Terminal 3 - Chạy Client GUI 2 (Người O):

```bash
python client_gui.py localhost 12345
```

## Cấu trúc Dự Án

```
GameCaro/
├── server.py         # Server chính
├── client_gui.py     # Client GUI (Pygame)
├── client.py         # Client Console
├── game_logic.py     # Logic trò chơi (kiểm tra thắng, áp dụng nước đi)
└── README.md         # File này
```
