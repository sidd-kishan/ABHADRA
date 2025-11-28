import rp2
from machine import Pin


def pack_pio_jumps(pc1_index: int, pc2_index: int, pc3_index: int, pc4_index: int, pc5_index: int, pc6_index: int) -> int:
    """
    Packs six 5-bit PIO Program Counter (PC) jump targets into a single 32-bit word.

    This function assumes:
    1. The PIO state machine uses 'out(pc, 5)' to read the jump addresses.
    2. The addresses are shifted out from LSB to MSB (SHIFT_RIGHT).
    3. The absolute program offset is 11 (0x0B). This offset is added to each relative PC index.

    Args:
        pcN_index: The relative index (0-15) of the instruction to jump to.

    Returns:
        The single 32-bit integer ready to be sent to the PIO TX FIFO via sm.put().
    """
    
    # 1. Define the program offset (where the main instruction block starts in PIO memory)
    # This must be added to the relative index (0-15) to get the absolute address (11-26).
    # PROGRAM_OFFSET = 11

    # 2. Input Validation (Ensure all indices are within the 0-15 range)
    indices = [pc1_index, pc2_index, pc3_index, pc4_index, pc5_index, pc6_index]
    for i, pc in enumerate(indices, 1):
        if not (0 <= pc <= 15):
            raise ValueError(f"PC target {i} ({pc}) is outside the valid range (0-15).")

    # 3. Calculate the absolute addresses
    # This is necessary because 'out(pc, 5)' jumps to the absolute address stored in the OSR.
    abs_pc1 = pc1_index #+ PROGRAM_OFFSET
    abs_pc2 = pc2_index #+ PROGRAM_OFFSET
    abs_pc3 = pc3_index #+ PROGRAM_OFFSET
    abs_pc4 = pc4_index #+ PROGRAM_OFFSET
    abs_pc5 = pc5_index #+ PROGRAM_OFFSET
    abs_pc6 = pc6_index #+ PROGRAM_OFFSET

    # 4. Pack the 5-bit addresses into the 32-bit word using bit shifting and bitwise OR
    # PC1 is shifted by 0 (LSBs), PC2 by 5, PC3 by 10, etc., up to PC6 by 25.
    # The final 2 bits (bits 30 and 31) are left unused (0).
    packed_word = (
        (abs_pc1 << 0)   |  # Bits 0-4
        (abs_pc2 << 5)   |  # Bits 5-9
        (abs_pc3 << 10)  |  # Bits 10-14
        (abs_pc4 << 15)  |  # Bits 15-19
        (abs_pc5 << 20)  |  # Bits 20-24
        (abs_pc6 << 25)     # Bits 25-29
    )

    return packed_word


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
    out(null,5)
    jmp(not_osre,"next_instruction")
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    label("nop_label")
    nop()
    nop()
    nop()
    nop()
    nop()
    wrap_target()
    pull()
    label("next_instruction")
    mov(pc,osr)
    wrap()

# Instantiate a state machine with the blink program, at 2000Hz, with set bound to Pin(25) (LED on the Pico board)
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(25),out_shiftdir=rp2.PIO.SHIFT_RIGHT)

def program(istructs):
    sm.active(1)
    print(hex(sm.get())) # gives 1 as output as the program executes from the top and set 1 in the queue
    sm.put(word)
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    sm.active(0)
    #machine.reset()

pc_targets = [0, 2, 4, 6, 8, 10]

# Calculate the packed word
word = pack_pio_jumps(*pc_targets)

# Print the results in decimal and hexadecimal format
print(f"--- PIO Jump Packer Results ---")
print(f"Input PC Targets (Relative Index): {pc_targets}")
print(f"Packed 32-bit Word (Decimal): {word}")
print(f"Packed 32-bit Word (Hex): 0x{word:08X}")

program(word)
