import numpy as np
import socket
from _thread import *
from snake import SnakeGame
import uuid
import time 
import threading
import rsa

# server = "10.11.250.207"
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0 
rows = 20 

connections = []

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
# s.settimeout(0.5)
print("Waiting for a connection, Server Started")


game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()


def game_thread() : 
    global game, moves_queue, game_state 
    while True :
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval : 
            time.sleep(0.1) 


rgb_colors = {
    "red" : (255, 0, 0),
    "green" : (0, 255, 0),
    "blue" : (0, 0, 255),
    "yellow" : (255, 255, 0),
    "orange" : (255, 165, 0),
} 
rgb_colors_list = list(rgb_colors.values())

def main() : 
    global counter, game

    start_new_thread(game_thread, ())

    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)

        pubKey, privKey = rsa.newkeys(512)
        clientn = int(conn.recv(1024).decode())
        cliente = int(conn.recv(1024).decode())
        
        clientkey = rsa.PublicKey(clientn, cliente)
        conn.send(str(pubKey.n).encode())
        conn.send(str(pubKey.e).encode())

        connections.append((conn, clientkey))

        threading.Thread(target = run, args = (conn, clientkey, privKey), daemon = True).start()

def run(conn, clientkey, privKey):
    global counter, game

    unique_id = str(uuid.uuid4())
    color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
    game.add_player(unique_id, color = color) 
    
    while True : 
        data = rsa.decrypt(conn.recv(500), privKey).decode()
        conn.send(game_state.encode())
        
        move = None 
        if not data :
            print("no data from player :(")
            break 
        elif data in ["m:left", "m:right", "m:up", "m:down"] : 
            move = data[2:]
            moves_queue.add((unique_id, move))
        elif data == "k:get" : 
            print("received get")
            pass 
        elif data == "quit" :
            print("received quit")
            game.remove_player(unique_id)
            connections.remove((conn, clientkey))
            break
        elif data == "reset" : 
            game.reset_player(unique_id)
        elif 'msg' in data:
            print('recieved message: ' + data[4:])
            for i in connections:
                i[0].send(rsa.encrypt(data[4:].encode(), i[1]))
        else :
            print("Invalid data received from client:", data)
            
    conn.close()

if __name__ == "__main__" : 
    main()