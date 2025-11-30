import rp2
from machine import Pin


def pack_pio_jumps(**kwargs) -> int:
    """
    Packs jump targets and data into a single 32-bit word, supporting two formats.

    Format 1 (JUMPS_6_X_5): 0x{unused - 2 bits}{pc6 - 5 bits}...{pc1 - 5 bits}
    Format 2 (DATA_16_JUMPS_3): 0x{unused - 1 bit}{pc3 - 5 bits}{pc2 - 5 bits}{data - 16 bits}{pc1 - 5 bits}

    Args (via kwargs):
        For Format 1: pc1, pc2, pc3, pc4, pc5, pc6 (0-15)
        For Format 2: pc1, data (0-65535), pc2, pc3 (0-15)

    Returns:
        The single 32-bit integer for sm.put().
    """
    
    packed_word = 0
    
    # --- Format 2 Check: If 'data' is provided, use the 3 Jumps + Data format ---
    if 'data' in kwargs:
        pc1 = kwargs.get('pc1', 0)
        pc2 = kwargs.get('pc2', 0)
        pc3 = kwargs.get('pc3', 0)
        data = kwargs.get('data', 0)

        # Validation
        #if not (0 <= pc1 <= 15 and 0 <= pc2 <= 15 and 0 <= pc3 <= 15):
        #     raise ValueError("Format 2: PC targets must be between 0 and 15.")
        #if not (0 <= data <= 65535):
        #     raise ValueError("Format 2: Data field must be between 0 and 65535 (16 bits).")

        # Packing Formula: 0x{unused - 1 bit}{pc3 - 5 bits}{pc2 - 5 bits}{data - 16 bits}{pc1 - 5 bits}
        # Total bits used: 5 (PC1) + 16 (Data) + 5 (PC2) + 5 (PC3) = 31 bits.
        packed_word = (
            (pc1 << 0)    |  # PC1: Bits 0-4 (LSB)
            (data << 5)   |  # Data: Bits 5-20
            (pc2 << 21)   |  # PC2: Bits 21-25
            (pc3 << 26)      # PC3: Bits 26-30
        )
        return packed_word

    # --- Format 1: Default to 6 Jumps format if 'data' is not provided ---
    else:
        # Expected keys: pc1 to pc6 (all 5-bit fields, 0-15)
        pcs = [
            kwargs.get('pc1', 0), kwargs.get('pc2', 0), kwargs.get('pc3', 0),
            kwargs.get('pc4', 0), kwargs.get('pc5', 0), kwargs.get('pc6', 0)
        ]

        # Validation
        #for i, pc in enumerate(pcs, 1):
        #    if not (0 <= pc <= 15):
        #        raise ValueError(f"Format 1: PC target {i} ({pc}) is outside the valid range (0-15).")
        
        # Packing Formula: PC_N << (5 * (N-1))
        # PC1: bits 0-4, PC6: bits 25-29. Bits 30-31 unused.
        packed_word = (
            (pcs[0] << 0)   |  # PC1
            (pcs[1] << 5)   |  # PC2
            (pcs[2] << 10)  |  # PC3
            (pcs[3] << 15)  |  # PC4
            (pcs[4] << 20)  |  # PC5
            (pcs[5] << 25)     # PC6
        )
        return packed_word


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    wrap_target()
    label("restart_loop")
    pull()
    label("next_instruction")
    mov(pc,osr)
    wrap()
    out(null,5)
    out(x,16)
    jmp("move_ahead")
    in_(x,16)
    jmp("consume_n_move_ahead")
    push()
    jmp("consume_n_move_ahead")
    set(x,5)
    in_(x,4)
    set(x,6)
    in_(x,4)
    set(x,7)
    in_(x,4)
    set(x,8)
    in_(x,4)
    push()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    label("consume_n_move_ahead")
    out(null,5)
    label("move_ahead")
    jmp(not_osre, "next_instruction")
    jmp("restart_loop")

# Instantiate a state machine with the blink program, at 2000Hz, with set bound to Pin(25) (LED on the Pico board)
sm = rp2.StateMachine(0, blink, freq=2000, set_base=Pin(25),out_shiftdir=rp2.PIO.SHIFT_RIGHT)
sm.active(1)
    
def program(istructs):
    print(hex(sm.get())) # gives 1 as output as the program executes from the top and set 1 in the queue
    sm.put(word)
    print(hex(sm.get()))
    print(hex(sm.get()))
    print(hex(sm.get()))
    #print(hex(sm.get()))
    #print(hex(sm.get()))
    #print(hex(sm.get()))
    #print(hex(sm.get()))
    #machine.reset()

#pc_targets = {'pc1': 16, 'data': 0xC0DE, 'pc2': 8, 'pc3': 7}
#word = pack_pio_jumps(**pc_targets)

# Print the results in decimal and hexadecimal format
#print(f"--- PIO Jump Packer Results ---")
#print(f"Input PC Targets (Relative Index): {pc_targets}")
#print(f"Packed 32-bit Word (Decimal): {word}")
#print(f"Packed 32-bit Word (Hex): 0x{word:08X}")

#print(hex(sm.get())) # gives 1 as output as the program executes from the top and set 1 in the queue
#sm.put(word)
#print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
#pc_targets = {'pc1': 2, 'pc2': 4, 'pc3': 6, 'pc4': 8, 'pc5': 10}
pc_targets = {'pc1': 2, 'data': 0xC0DE, 'pc2': 29, 'pc3': 5}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

pc_targets = {'pc1': 7, 'pc2': 29, 'pc3': 29, 'pc4': 29, 'pc5': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
#print(hex(sm.get()))
sm.active(0)
#machine.reset()

