from rp2 import PIO, StateMachine, asm_pio
from machine import Pin
import time

# Import the PIO program (assuming it's in the same file or imported)
# from blink import blink # If blink() is in a separate file

# Define the PIO program (as above)
@asm_pio(set_init=PIO.OUT_LOW)
def blink():
    wrap_target()
    pull()
    mov(x, osr)
    set(pins, 1)[x]
    set(pins, 0)[x]
    in_(osr,32)
    push()
    wrap()

# Initialize a state machine on PIO 0, state machine 0
# with the blink program, on Pin 25 (onboard LED)
sm = StateMachine(0, blink, freq=2000, set_base=Pin(25))

# Start the state machine
sm.active(1)

# Send data to the PIO's TX FIFO
# The PIO program will pull these values and use them as delay counts
sm.put(500000000) # Fast blink
time.sleep(1)
print(sm.get())
sm.put(40000000000) # Slower blink
time.sleep(1)
print(sm.get())
sm.put(1000000) # Even slower blink
time.sleep(1)
print(sm.get())
# Stop the state machine
sm.active(0)
