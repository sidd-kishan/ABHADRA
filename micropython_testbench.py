import rp2
from machine import Pin

# Define the blink program.  It has one GPIO to bind to on the set instruction, which is an output pin.
# Use lots of delays to make the blinking visible by eye.
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    set(x,1)           #00
    jmp("main")        #01
    set(x,2)		   #02
    jmp("main")		   #03
    set(x,3)		   #04
    jmp("main")		   #05
    set(x,4)		   #06
    jmp("main")		   #07
    set(x,5)		   #08
    jmp("main")		   #09
    set(x,6)		   #0a
    jmp("main")		   #0b
    set(x,7)		   #0c
    jmp("main")		   #0d
    set(x,8)		   #0e
    jmp("main")		   #0f
    wrap_target()
    pull()
    mov(pc,invert(osr))
    out(null,4)
    label("main")
    in_(x,32)
    push()
    wrap()

# Instantiate a state machine with the blink program, at 2000Hz, with set bound to Pin(25) (LED on the Pico board)
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(25))

# Run the state machine for 3 seconds.  The LED should blink.
sm.active(1)
print(sm.get()) # gives 1 as output as the program executes from the top and set 1 in the queue
sm.put(0x00000000)
print(sm.get())
sm.put(0xeeeeeeee)
print(sm.get())
#sm.put(0xdddddddd) d's are crashing
#print(sm.get())
sm.put(0xcccccccc)
print(sm.get())
#sm.put(0xbbbbbbbb) b's are crashing
#print(sm.get())
sm.put(0xaaaaaaaa)
print(sm.get())
sm.put(0x99999999)
print(sm.get())
sm.put(0x88888888)
print(sm.get())
sm.put(0x77777777)
print(sm.get())
sm.put(0x66666666)
print(sm.get())
sm.put(0x55555555)
print(sm.get())
#sm.put(0x44444444) 4s are crashing it
sm.put(0x33333333)
print(sm.get())
sm.put(0x22222222)
print(sm.get())
sm.put(0x11111111)
print(sm.get())
sm.active(0)
