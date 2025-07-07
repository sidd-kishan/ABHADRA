# Brainfuck to 32-bit Hex Encoder for PIO-based Interpreter
# Command format: [4-bit opcode][28-bit instruction memory address]

# Sample Hello World Brainfuck program
hello_world_bf = """
++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++. .+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
"""

# Clean input: retain only valid Brainfuck commands
bf_commands = "><+-[].,"
bf_code_clean = ''.join(c for c in hello_world_bf if c in bf_commands)

# Opcode (4-bit) for each Brainfuck command
NIBBLE_MAP = {
    ']': [0x0],
    '[': [0x1],
    '+': [0x3, 0x2, 0x3],  # flip-sub-flip
    '-': [0x2],
    '<': [0x4],
    '>': [0x5, 0x4, 0x5],  # flip-sub-flip
    '.': [0xA],
    ',': [0xB],
}

def encode_command_with_nibble(cmd_nibble: int, address: int) -> int:
    """Encode the instruction with 4-bit opcode and 28-bit address."""
    return ((cmd_nibble & 0xF) << 28) | (address & 0x0FFFFFFF)

def bf_to_nibble_hex_grouped(bf_code: str) -> list[str]:
    # Pass 1: bracket matching for loops
    bracket_stack = []
    bracket_map = {}
    for i, c in enumerate(bf_code):
        if c == '[':
            bracket_stack.append(i)
        elif c == ']':
            if not bracket_stack:
                raise SyntaxError(f"Unmatched ] at {i}")
            start = bracket_stack.pop()
            bracket_map[start] = i
            bracket_map[i] = start
    if bracket_stack:
        raise SyntaxError(f"Unmatched [ at {bracket_stack[-1]}")

    # Pass 2: build instruction map (grouped by command)
    instr_map = []  # (char, char_idx, nibble, addr)
    instr_addr = 0
    for idx, c in enumerate(bf_code):
        if c not in NIBBLE_MAP:
            continue
        nibble_group = NIBBLE_MAP[c]
        for nib in nibble_group:
            instr_map.append((c, idx, nib, instr_addr))
        instr_addr += 1  # same addr for entire group

    # Pass 3: encode instructions with real jump targets
    hex_lines = []
    for (char, idx, nibble, addr) in instr_map:
        if char in '[]' and idx in bracket_map:
            match_idx = bracket_map[idx]
            match_addr = next(a for a in instr_map if a[1] == match_idx)[3]
            encoded = encode_command_with_nibble(nibble, match_addr)
        else:
            encoded = encode_command_with_nibble(nibble, addr)
        hex_lines.append(f"0x{encoded:08X}")

    return hex_lines

# Generate hex instructions
hex_lines = bf_to_nibble_hex_grouped(bf_code_clean)

# Print to console
for line in hex_lines:
    print(line)

# Optionally save to file
with open("hello_world_bf_grouped.hex", "w") as f:
    f.write('\n'.join(hex_lines))
