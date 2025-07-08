# bfpio.py
# Converts Brainfuck code into 32-bit hex for PIO BF interpreter (Abhadra)

from typing import List, Tuple

# Toggle this to enable/disable suppression of redundant pointer I/O
SUPPRESS_POINTER_READ_WRITE = True

# Valid Brainfuck commands
BF_COMMANDS = "><+-[].,"

# PIO instruction PC addresses for each BF command or macro
PC_MAP = {
    '>': [5, 4, 5],       # flip-sub-flip for y++
    '<': [4],             # y--
    '+': [3, 2, 3],       # flip-sub-flip for x++
    '-': [2],             # x--
    '[': [1],             # loop start
    ']': [0],             # loop end
    '.': [10],            # print (send_from_x)
    ',': [11],            # input (bring_into_x)
    'send_from_y': [8],
    'send_from_x': [9],
    'bring_into_x': [11],
}

def encode_command(pc: int, address: int) -> int:
    """Encode as: 5-bit instruction | 27-bit instruction memory address"""
    return (pc << 27) | (address & 0x7FFFFFF)

def optimize_bf_code(bf_code: str, suppress: bool = True) -> List[Tuple[str, int]]:
    """Expands and optimizes Brainfuck into command/macro tuples with pointer I/O control."""
    clean_code = [c for c in bf_code if c in BF_COMMANDS]
    optimized = []
    last_data_mutation = False

    i = 0
    while i < len(clean_code):
        c = clean_code[i]

        if c in '><':
            # Identify full sequence of pointer movement
            start = i
            while i < len(clean_code) and clean_code[i] in '><':
                i += 1
            group = clean_code[start:i]

            if not suppress:
                for j, move in enumerate(group):
                    if last_data_mutation:
                        optimized.append(('send_from_y', start + j))
                        optimized.append(('send_from_x', start + j))
                    optimized.append((move, start + j))
                    optimized.append(('send_from_y', start + j))
                    optimized.append(('bring_into_x', start + j))
                last_data_mutation = False
            else:
                # Suppress redundant I/O: only emit I/O at start (if needed) and end
                if last_data_mutation:
                    optimized.append(('send_from_y', start))
                    optimized.append(('send_from_x', start))
                for j, move in enumerate(group):
                    optimized.append((move, start + j))
                    if j == len(group) - 1:
                        optimized.append(('send_from_y', start + j))
                        optimized.append(('bring_into_x', start + j))
                last_data_mutation = False
        else:
            optimized.append((c, i))
            if c in '+-':
                last_data_mutation = True
            elif c in '.,':
                optimized.append(('send_from_y', i))
                optimized.append(('bring_into_x', i))
                last_data_mutation = False
            elif c in '[]':
                last_data_mutation = False
            i += 1

    return optimized

def match_brackets(code: List[Tuple[str, int]]) -> dict:
    """Matches brackets and returns a lookup for jump destinations."""
    bracket_stack = []
    bracket_map = {}
    for idx, (cmd, _) in enumerate(code):
        if cmd == '[':
            bracket_stack.append(idx)
        elif cmd == ']':
            if not bracket_stack:
                raise SyntaxError("Unmatched ']'")
            open_idx = bracket_stack.pop()
            bracket_map[open_idx] = idx
            bracket_map[idx] = open_idx
    if bracket_stack:
        raise SyntaxError("Unmatched '['")
    return bracket_map

def bf_to_hex_optimized(bf_code: str, suppress: bool = True) -> List[str]:
    """Encodes full hex sequence from BF code with optional suppression."""
    optimized_code = optimize_bf_code(bf_code, suppress=suppress)
    bracket_map = match_brackets(optimized_code)

    instr_map = []
    addr_counter = 0
    addr_map = {}

    for idx, (cmd, original_idx) in enumerate(optimized_code):
        if original_idx not in addr_map:
            addr_map[original_idx] = addr_counter
            addr_counter += 1
        addr = addr_map[original_idx]
        pcs = PC_MAP.get(cmd, [])
        for pc in pcs:
            instr_map.append((cmd, idx, pc, addr))

    hex_lines = []
    for cmd, idx, pc, addr in instr_map:
        if cmd in '[]':
            match_idx = bracket_map[idx]
            match_instr = next((x for x in instr_map if x[1] == match_idx), None)
            match_addr = match_instr[3] if match_instr else 0
            encoded = encode_command(pc, match_addr)
        else:
            encoded = encode_command(pc, addr)
        hex_lines.append(f"0x{encoded:08X}")
    return hex_lines

def save_hex_to_file(bf_code: str, filename: str, suppress: bool = True):
    """Generates and saves encoded hex file."""
    hex_lines = bf_to_hex_optimized(bf_code, suppress=suppress)
    with open(filename, 'w') as f:
        f.write('\n'.join(hex_lines))
    print(f"Saved {len(hex_lines)} lines to {filename}")

if __name__ == "__main__":
    # Example program: Hello World
    hello_world_bf = """
    ++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++. .+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>.
    """
    filename = "hello_world.hex"
    save_hex_to_file(hello_world_bf, filename, suppress=SUPPRESS_POINTER_READ_WRITE)
