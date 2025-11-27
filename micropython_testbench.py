import rp2
from machine import Pin

# Define the blink program.  It has one GPIO to bind to on the set instruction, which is an output pin.
# Use lots of delays to make the blinking visible by eye.
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    set(x,1)           #00
    in_(x,4)           #01
    set(x,2)		   #02
    in_(x,4)		   #03
    set(x,3)		   #04
    in_(x,4)		   #05
    set(x,4)		   #06
    in_(x,4)		   #07
    set(x,5)		   #08
    in_(x,4)		   #09
    set(x,6)		   #0a
    in_(x,4)		   #0b
    set(x,7)		   #0c
    in_(x,4)		   #0d
    set(x,8)		   #0e
    in_(x,4)		   #0f
    push()
    set(x,0)
    #out(null,4)
    #in_(osr,28)
    #push()
    wrap_target()
    pull()
    mov(pc,osr)
    wrap()

# Instantiate a state machine with the blink program, at 2000Hz, with set bound to Pin(25) (LED on the Pico board)
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(25),out_shiftdir=rp2.PIO.SHIFT_RIGHT)

# Run the state machine for 3 seconds.  The LED should blink.
sm.active(1)
print(hex(sm.get())) # gives 1 as output as the program executes from the top and set 1 in the queue
sm.put(0xfffffff0)
print(hex(sm.get()))
sm.put(0xfffffff1)
print(hex(sm.get()))
sm.put(0xfffffff2)
print(hex(sm.get()))
sm.put(0xfffffff3)
print(hex(sm.get()))
sm.put(0xfffffff4)
print(hex(sm.get()))
sm.put(0xfffffff5)
print(hex(sm.get()))
sm.put(0xfffffff6)
print(hex(sm.get()))
sm.put(0xfffffff7)
print(hex(sm.get()))
sm.put(0xfffffff8)
print(hex(sm.get()))
sm.put(0xfffffff9)
print(hex(sm.get()))
sm.put(0xfffffffa)
print(hex(sm.get()))
sm.put(0xfffffffb)
print(hex(sm.get()))
sm.put(0xfffffffc)
print(hex(sm.get()))
sm.put(0xfffffffd)
print(hex(sm.get()))
sm.put(0xfffffffe)
print(hex(sm.get()))
sm.put(0xffffffff)
print(hex(sm.get()))
sm.active(0)
machine.reset()
