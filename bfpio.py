from typing import List, Tuple

# Toggle suppression of redundant pointer read/write macros
SUPPRESS_POINTER_READ_WRITE = True

# Valid Brainfuck commands
BF_COMMANDS = "><+-[].,"

# PIO instruction PC mapping
PC_MAP = {
    '>': [10, 8, 10],       # flip-sub-flip for y++
    '<': [8],               # y--
    '+': [6, 4, 6],         # flip-sub-flip for x++
    '-': [4],               # x--
    '[': [2],               # loop start
    ']': [0],               # loop end
    '.': [24],              # print from x
    ',': [24],              # input into x
    'send_from_y': [12],
    'send_from_x': [27],
    'bring_into_x': [14,18],
    'bring_into_y': [14,20],
}

def encode_command(pc: int, address: int) -> int:
    """Encodes instruction: top 5 bits PC | lower 27 bits address."""
    return (pc << 27) | (address & 0x7FFFFFF)

def optimize_bf_code(bf_code: str, suppress: bool = True) -> List[Tuple[str, int]]:
    """Expands Brainfuck into (command, addr_index) tuples with optimized pointer I/O."""
    clean_code = [c for c in bf_code if c in BF_COMMANDS]
    optimized = []
    last_data_mutation = False

    i = 0
    while i < len(clean_code):
        c = clean_code[i]

        if c in '><':
            start = i
            while i < len(clean_code) and clean_code[i] in '><':
                i += 1
            group = clean_code[start:i]

            if not suppress:
                # Emit all macros for every move
                for j, move in enumerate(group):
                    idx = start + j
                    optimized.append(('send_from_y', idx))
                    optimized.append(('send_from_x', idx))
                    optimized.append((move, idx))
                    optimized.append(('send_from_y', idx))
                    optimized.append(('bring_into_x', idx))
            else:
                # Suppress intermediate macros, emit only at edges
                first_idx = start
                last_idx = start + len(group) - 1
                optimized.append(('send_from_y', first_idx))
                optimized.append(('send_from_x', first_idx))
                for j, move in enumerate(group):
                    idx = start + j
                    optimized.append((move, idx))
                optimized.append(('send_from_y', last_idx))
                optimized.append(('bring_into_x', last_idx))
            last_data_mutation = False

        else:
            optimized.append((c, i))
            if c in '+-':
                last_data_mutation = True
            elif c in '.,':
                # Read from current tape cell before I/O
                optimized.append(('send_from_y', i))
                optimized.append(('bring_into_x', i))
                last_data_mutation = False
            elif c in '[]':
                last_data_mutation = False
            i += 1

    return optimized

def match_brackets(code: List[Tuple[str, int]]) -> dict:
    """Match brackets for jump address patching."""
    stack = []
    bracket_map = {}
    for idx, (cmd, _) in enumerate(code):
        if cmd == '[':
            stack.append(idx)
        elif cmd == ']':
            if not stack:
                raise SyntaxError("Unmatched ']'")
            open_idx = stack.pop()
            bracket_map[open_idx] = idx
            bracket_map[idx] = open_idx
    if stack:
        raise SyntaxError("Unmatched '['")
    return bracket_map

def bf_to_hex_optimized(bf_code: str, suppress: bool = True) -> List[str]:
    """Generates 32-bit encoded hex strings from Brainfuck code."""
    optimized_code = optimize_bf_code(bf_code, suppress=suppress)
    bracket_map = match_brackets(optimized_code)

    instr_map = []
    addr_counter = 0
    addr_map = {}

    for idx, (cmd, origin_idx) in enumerate(optimized_code):
        if origin_idx not in addr_map:
            addr_map[origin_idx] = addr_counter
            addr_counter += 1
        addr = addr_map[origin_idx]
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

# Example usage
if __name__ == "__main__":
    test_bf = ">>>"
    hex_output = bf_to_hex_optimized(test_bf, suppress=SUPPRESS_POINTER_READ_WRITE)
    for h in hex_output:
        print("fifo -p 0 -s 0 -t -e -v "+h)
