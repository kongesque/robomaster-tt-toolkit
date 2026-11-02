# Example: control Tello with SDK commands typed on the keyboard, using Python
import socket
import threading
import time
import sys

# IP and port of Tello
tello_address = ('192.168.10.1', 8889)

# IP and port of local computer
local_address = ('', 9000)

# Create a UDP connection to send commands
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind to the local address and port
sock.bind(local_address)


# Function: send a message to Tello
def send(message,delay):
  # Try to send the message, otherwise show the error
  try:
    sock.sendto(message.encode(), tello_address)
    print("Sending message: " + message)
  except Exception as e:
    print("Error sending: " + str(e))
  # Wait for a reply: takeoff 8 sec, flip 5 sec, land 5 sec
  if message=='takeoff':  
    delay=8
  elif message.find('flip')>=0:  
    delay=5
  elif message=='land':  
    delay=5
  time.sleep(delay)
  
# Function: receive messages from Tello
def receive():
  # Keep receiving messages in a loop
  while True:
    # Try to receive a message, otherwise show the error
    try:
      response, ip_address = sock.recvfrom(128)
      print("Received message: " + response.decode(encoding='utf-8'))
    except Exception as e:
      # If there's an error close the socket and break out of the loop
      sock.close()
      print("socket closed ==>Error receiving: " + str(e))
      break
      
# Create and run the listening thread in the background
# This thread uses the receive function above
# It keeps running
receiveThread = threading.Thread(target=receive)
receiveThread.daemon = True
receiveThread.start()

# Instructions
print("Enter a Tello SDK command and press 'Enter', or type 'quit' to leave.")

# Enter SDK mode, required before any other command
send("command", 1)

# Keep waiting for input until 'quit' or Ctrl+C
while True:
  try:
    # Read keyboard input
    message = input('')
    # On 'quit', end the program and close the connection
    if 'quit' in message:
      print("Program exited sucessfully")
      sock.close()
      break
    
    # Send the command
    send(message,3)
    
  # Handle Ctrl+C
  except KeyboardInterrupt as e:
    sock.close()
    break





