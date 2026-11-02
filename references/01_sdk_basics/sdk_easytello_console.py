import easytello 
import time

# Set the text shown on the command line
def command_line():
    print('t: takeoff, l: land, ud: up then down, ba: check battery')

# Custom commands
def call_command(t,cmd):
   
        if cmd=='t':
            t.takeoff()
        elif cmd=='l':
            t.land()
        elif cmd=='ud':
            t.up(20)
            t.down(20)
        elif cmd=='ba':
            print('battery=%s' % t.get_battery())
        

def main():
    
    t=easytello.Tello()
    while True:
        # Error handling
        try:
            command_line()
            # Show battery level
            battery=int(t.get_battery())
            message=("Battery left %s%%>>" % battery)
            cmd = input(message)

            if cmd.lower() in ('end', 'exit', 'quit'):
                print ('Exit')
                break
            else:
                call_command(t,cmd)

            if(battery<10):
                print("Battery left %s%%, below 10" % battery)
                break
        except Exception as e:
            print('Err:',e)
        except KeyboardInterrupt:
            print ('\n KeyboardInterrupt\n')
            break


if __name__ == '__main__':
    main()
                



