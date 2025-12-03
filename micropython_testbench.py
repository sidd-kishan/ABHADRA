import rp2
from machine import Pin
import time

def reverse_bits(n, bit_width):
    reversed_n = 0
    for i in range(bit_width):
        if (n >> i) & 1:  # Check if the i-th bit is set
            reversed_n |= (1 << (bit_width - 1 - i)) # Set the corresponding bit in the reversed number
    return reversed_n

# Example usage for an 8-bit number
number = 0b10110011 # 179
reversed_number = reverse_bits(number, 8)

def pack_pio_jumps(**kwargs) -> int:
    """
    Packs jump targets and data into a single 32-bit word, supporting two formats.

    Format 1 (JUMPS_6_X_5): 0x{unused - 2 bits}{pc6 - 5 bits}...{pc1 - 5 bits}
    Format 2 (DATA_16_JUMPS_3): 0x{unused - 1 bit}{pc3 - 5 bits}{pc2 - 5 bits}{data - 16 bits}{pc1 - 5 bits}
    Format 3 (ADDR_27_JUMP_1): 0x{addr - 27 bits}{pc1 - 5 bits}

    Args (via kwargs):
        For Format 1: pc1, pc2, pc3, pc4, pc5, pc6 (0-15)
        For Format 2: pc1, data (0-65535), pc2, pc3 (0-15)
        For Format 3: pc1, addr (0-0x7fffffe)

    Returns:
        The single 32-bit integer for sm.put().
    """
    
    packed_word = 0
    # --- Format 3 Check: If 'addr' is provided, use the 1 Jump + Addr format ---
    if 'addr' in kwargs:
        pc1 = kwargs.get('pc1', 0)
        addr = kwargs.get('addr', 0)
        packed_word = (
            (pc1 << 0)    |  # PC1: Bits 0-4 (LSB)
            (reverse_bits(addr, 26) << 5)      # Data: Bits 5-31
        )
        return packed_word
    # --- Format 2 Check: If 'data' is provided, use the 3 Jumps + Data format ---
    elif 'data' in kwargs:
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
def abhadra():
    wrap_target()							# address: N/A - Interpreter Begins main loop starts does not consume any pio assembly spot
    label("restart_loop")					# address: N/A - label to start the main loop does not consume any pio assembly spot
    pull()									# address: 0   - The 1 element of 32 bits are pulled from the RX Fifo consumes 1 spot in the pio assembly memory
    label("next_instruction")				# address: N/A - label marks the jump to the 5 bit address in the pio program does not consume any pio assembly spot
    mov(pc,osr)								# address: 1   - This makes the jump based on 5 bits in the osr and branches to the perticular section of the pio asm program
    wrap()									# address: N/A - 
    out(null,5)								# address: 2   - strips 5 bits
    out(x,16)								# address: 3   - x = 16 bits from osr
    jmp("move_ahead")						# address: 4
    in_(x,32)								# address: 5
    jmp("consume_n_move_ahead")				# address: 6
    label("just_push")
    push()									# address: 7
    jmp("consume_n_move_ahead")				# address: 8
    jmp(not_x,"skip_the_loop")				# address: 9   - [ loop begins for BF
    jmp("consume_n_move_ahead")				# address: 10
    jmp(not_x,"consume_n_move_ahead")		# address: 11  - ] loop ends for BF
    jmp("return_to_the_start_of_the_loop")	# address: 12
    jmp(x_dec,"flip_x")						# address: 13  - - x decrement for BF
    label("flip_x")
    mov(x,invert(x))						# address: 14  - invert x for 2 complements addition +
    jmp("consume_n_move_ahead")				# address: 15
    jmp(y_dec,"flip_y")						# address: 16  - < y decrement for BF
    label("flip_y")
    mov(y,invert(y))						# address: 17  - invert y for 2 complements addition >
    jmp("consume_n_move_ahead")				# address: 18
    label("return_to_the_start_of_the_loop")
    label("skip_the_loop")
    in_(osr,32)								# address: 19
    jmp("just_push")						# address: 20
    label("arbitrary_execute")
    out(null,5)								# address: 21
    out(exec,16)							# address: 22
    jmp("move_ahead")						# address: 23
    label("in_to_memory")
    in_(pins,1)								# address: 24
    jmp(x_dec,"in_to_memory")				# address: 25
    jmp("consume_n_move_ahead")				# address: 26
    label("out_to_memory")
    out(pins,1)								# address: 27
    jmp(x_dec,"out_to_memory")				# address: 28
    label("consume_n_move_ahead")			# address: N/A
    out(null,5)								# address: 29
    label("move_ahead")						# address: N/A
    jmp(not_osre, "next_instruction")		# address: 30
    jmp("restart_loop")						# address: 31

# Instantiate a state machine with the blink program, at 2000Hz, with set bound to Pin(25) (LED on the Pico board)
sm = rp2.StateMachine(0, abhadra, freq=2000, set_base=Pin(25),out_shiftdir=rp2.PIO.SHIFT_RIGHT)
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

# Sequence to assign a value to x
pc_targets = {'pc1': 2, 'data': 0xC0DE, 'pc2': 5, 'pc3': 7}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

pc_targets = {'pc1': 13, 'pc2': 14, 'pc3': 5, 'pc4': 7, 'pc5': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))
print(hex(sm.get()))

pc_targets = {'pc1': 14, 'pc2': 13, 'pc3': 5, 'pc4': 7, 'pc5': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 2, 'data': 0xADDE, 'pc2': 5, 'pc3': 7}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 21,'data': rp2.asm_pio_encode("mov(y, x)",0), 'pc2': 16, 'pc3': 17}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

pc_targets = {'pc1': 21,'data': rp2.asm_pio_encode("mov(x, y)",0), 'pc2': 5, 'pc3': 7}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 17, 'pc2': 16, 'pc3': 29, 'pc4': 29, 'pc5': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

pc_targets = {'pc1': 21,'data': rp2.asm_pio_encode("mov(x, y)",0), 'pc2': 5, 'pc3': 7}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 11,'addr': 0xfffffff}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 2, 'data': 0x0, 'pc2': 5, 'pc3': 7}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

pc_targets = {'pc1': 9,'addr': 0xfffffff}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
print(hex(sm.get()))

# Out to Memory test
pc_targets = {'pc1': 2, 'data': 10, 'pc2': 27, 'pc3': 31}
word = pack_pio_jumps(**pc_targets)
sm.put(word)
#print(hex(sm.get()))

pc_targets = {'pc1': 21,'data': rp2.asm_pio_encode("set(pins, 1)",0), 'pc2': 29, 'pc3': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

time.sleep(1)

pc_targets = {'pc1': 21,'data': rp2.asm_pio_encode("set(pins, 0)",0), 'pc2': 29, 'pc3': 29}
word = pack_pio_jumps(**pc_targets)
sm.put(word)

time.sleep(1)


sm.active(0)
#machine.reset()



