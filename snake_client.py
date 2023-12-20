import socket
import snake
import pygame
from _thread import *
import threading
import rsa

rgb_colors = {
    "red" : (255, 0, 0),
    "blue" : (0, 0, 255),
    "yellow" : (255, 255, 0),
    "orange" : (255, 165, 0),
} 
rgb_colors_list = list(rgb_colors.values())

def drawGrid(w, rows, surface):
    sizeBtwn = w // rows

    x = 0
    y = 0
    for l in range(rows):
        x = x + sizeBtwn
        y = y + sizeBtwn
        pygame.draw.line(surface, (255, 255, 255), (x, 0), (x, w))
        pygame.draw.line(surface, (255, 255, 255), (0, y), (w, y))


def redrawWindow(surface):
    global rows, width, snakes, snacks

    surface.fill((0, 0, 0))

    for i in snacks:
        i.draw(surface)

    for i in range(len(snakes)):
        snakes[i][0].draw(surface, True)
        for j in snakes[i][1:]:
            j.draw(surface)
    
    drawGrid(width, rows, surface)
    pygame.display.update()

def parseState(state):

    state = state.split('|')

    snakes = state[0].split('**')
    for i in range(len(snakes)):
        snakes[i] = snakes[i].split('*')
        for j in range(len(snakes[i])):
            snakes[i][j] = snake.cube(eval(snakes[i][j].strip("()")), 1, 0, rgb_colors_list[i])

    snacks = state[1].split("**")
    for i in range(len(snacks)):
        snacks[i] = snake.cube(eval(snacks[i].strip("()")), 1, 0, (0, 255, 0))

    return snakes, snacks

def recv(conn, privKey, serverKey):
    global width, rows, snakes, snacks, win

    while True:
        received = conn.recv(500)
        try:
            decrypted = rsa.decrypt(received, privKey).decode()
            print(decrypted)
        except:
            snakes, snacks = parseState(received.decode())
            redrawWindow(win)

def run(clientSocket, privKey, serverKey):
    global width, rows, snakes, snacks, win

    clock = pygame.time.Clock()
    
    while True:
        pygame.time.delay(50)
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                dir = 'quit'
                pygame.quit()
                break
            keys = pygame.key.get_pressed()
            for key in keys:
                if keys[pygame.K_LEFT]:
                    dir = 'm:left'
                elif keys[pygame.K_RIGHT]:
                    dir = 'm:right'
                elif keys[pygame.K_UP]:
                    dir = 'm:up'
                elif keys[pygame.K_DOWN]:
                    dir = 'm:down'
                elif keys[pygame.K_r]:
                    dir = 'reset'
                elif keys[pygame.K_ESCAPE]:
                    dir = 'quit'
                    pygame.quit()
                    break
                elif keys[pygame.K_1]:
                    dir = 'msg:HELLO!'
                elif keys[pygame.K_2]:
                    dir = 'msg:GOODBYE!'
                elif keys[pygame.K_3]:
                    dir = 'msg:WELL PLAYED!'
                else:
                    dir = 'k:get'

        clientSocket.send(rsa.encrypt(dir.encode(), serverKey))
        
if __name__ == "__main__":

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP
    client_socket.connect(("localhost", 5555))

    width = 500
    rows = 20
    win = pygame.display.set_mode((width, width))

    pubKey, privKey = rsa.newkeys(512)
    client_socket.send(str(pubKey.n).encode())
    client_socket.send(str(pubKey.e).encode())
    servern = int(client_socket.recv(1024).decode())
    servere = int(client_socket.recv(1024).decode())
    serverKey = rsa.PublicKey(servern, servere)

    threading.Thread(target = recv, args = (client_socket, privKey, serverKey), daemon = True).start()
    run(client_socket, privKey, serverKey)