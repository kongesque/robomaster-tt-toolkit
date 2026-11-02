import threading
import socket
import sys
from time import  sleep
import keyboard

host = ''
port = 9000
locaddr = (host,port)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

tello_address = ('192.168.10.1', 8889)

sock.bind(locaddr)

def recv():
    count = 0
    while True:
        try:
            data, server = sock.recvfrom(1518)
            print(data.decode(encoding="utf-8"))
        except Exception:
            print ('\nExit . . .\n')
            break

print ('Python Tello Keyboard Control')
print ('c - command, t - takeoff, l - land, w - forward')

recvThread = threading.Thread(target=recv, daemon=True)
recvThread.start()

def sendmsg(msg):
    msg = msg.encode(encoding="utf-8")
    sent = sock.sendto(msg, tello_address)

def start():
    sendmsg('command')

def takeoff():
    sendmsg('takeoff')

def land():
    sendmsg('land')

def forward():
    sendmsg('forward 20')

def back():
    sendmsg('back 20')

def up():
    sendmsg('up 20')

def down():
    sendmsg('down 20')

def cw():
    sendmsg('cw 5')

def ccw():
    sendmsg('ccw 5')

def battery():
    sendmsg('battery?')

KEYS = {
    'w': ('forward 20', forward), 's': ('back 20', back),
    'up': ('up 20', up), 'down': ('down 20', down),
    'right': ('cw 5', cw), 'left': ('ccw 5', ccw),
    't': ('takeoff', takeoff), 'l': ('land', land),
    'c': ('command', start), 'b': ('battery?', battery),
}

start()  # enter SDK mode, required before any other command

while True:  # making a loop
    try:
        for key, (name, action) in KEYS.items():
            if keyboard.is_pressed(key):
                print(name)
                action()
                sleep(0.5)  # one command per press, not one per loop
                break
    except KeyboardInterrupt:
        break
    sleep(0.05)

sock.close()
