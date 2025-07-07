# Brainfuck to 32-bit Hex Encoder for PIO-based Interpreter
# Command format: [4-bit opcode][28-bit instruction memory address]

# Sample Hello World Brainfuck program
hello_world_bf = """
++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++. .+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
"""

# bfpio.py
# Brainfuck to RP2040 PIO Instruction Encoder (5-bit opcode | 27-bit address)

BF_COMMANDS = "><+-[].,"

# PIO PC (jump address) mapping per Brainfuck command
# Commands like '+' and '>' use 3-step sequences
PC_MAP = {
    '>': [5, 4, 5],     # Flip-Sub-Flip for y++
    '<': [4],
    '+': [3, 2, 3],     # Flip-Sub-Flip for x++
    '-': [2],
    '[': [1],
    ']': [0],
    '.': [10],
    ',': [11],
}

def encode_command(pc: int, address: int) -> int:
    """Encodes into 32-bit value: [5-bit pc][27-bit address]"""
    if not (0 <= pc < 32):
        raise ValueError("PC must be a 5-bit value (0–31)")
    if not (0 <= address < (1 << 27)):
        raise ValueError("Address must be a 27-bit value")
    return (pc << 27) | (address & 0x7FFFFFF)

def bf_to_hex_encoded(bf_code: str) -> list[str]:
    # Clean Brainfuck code
    bf_code = ''.join(c for c in bf_code if c in BF_COMMANDS)

    # Stack-based bracket matching
    bracket_stack = []
    bracket_map = {}

    for i, c in enumerate(bf_code):
        if c == '[':
            bracket_stack.append(i)
        elif c == ']':
            if not bracket_stack:
                raise SyntaxError(f"Unmatched ']' at position {i}")
            start = bracket_stack.pop()
            bracket_map[start] = i
            bracket_map[i] = start
    if bracket_stack:
        raise SyntaxError(f"Unmatched '[' at position {bracket_stack[-1]}")

    # Instruction list: (char, src_index, pc, addr)
    instr_map = []
    addr_counter = 0
    instr_addr_map = {}  # map from bf index to base address

    for idx, char in enumerate(bf_code):
        if char not in PC_MAP:
            continue
        if char not in instr_addr_map:
            instr_addr_map[idx] = addr_counter
        for pc in PC_MAP[char]:
            instr_map.append((char, idx, pc, instr_addr_map[idx]))
            addr_counter += 1

    # Final hex encoding
    hex_lines = []
    for (char, src_idx, pc, addr) in instr_map:
        if char in "[]":
            match_idx = bracket_map[src_idx]
            match_addr = instr_addr_map[match_idx]
            encoded = encode_command(pc, match_addr)
        else:
            encoded = encode_command(pc, addr)
        hex_lines.append(f"0x{encoded:08X}")

    return hex_lines

def main():
    # Sample Hello World program in Brainfuck
    hello_world_bf = """
    ++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++. .+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
    """

    try:
        hex_lines = bf_to_hex_encoded(hello_world_bf)

        with open("hello_world_bf_grouped.hex", "w") as f:
            for line in hex_lines:
                f.write(line + "\n")

        print("✅ Hex encoding complete.")
        print("📄 Output written to hello_world_bf_grouped.hex")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
