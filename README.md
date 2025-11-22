# 🧠 Abhadra — A Hardware Brainfuck Interpreter on the Pi Pico's PIO

> _"Brainfuck needs step increment and step decrement — and the PIO can only do step increment and step decrement (by flipping bits, subtracting, then flipping again). It’s a match made in heaven."_

**Abhadra** is a Turing-complete interpreter for the Brainfuck programming language, implemented entirely in the **PIO (Programmable I/O)** hardware of the Raspberry Pi Pico. It harnesses the PIO’s deterministic, low-level instruction set to run Brainfuck instructions without involving the CPU at runtime — a full **hardware-native interpreter**.

---

## 🧩 Why PIO?

The Raspberry Pi Pico’s PIO subsystem was designed to implement custom I/O protocols, but it turns out it’s also an ideal fit for minimalist languages like Brainfuck.

| Brainfuck Op | PIO Equivalent                          |
|--------------|------------------------------------------|
| `+` / `-`     | `x--`, `mov x,~x` (wraparound handling) |
| `>` / `<`     | `y--`, `mov y,~y`                      |
| `[` / `]`     | `jmp ~x`, `in osr, 26`, `push`, `pull` |
| `.` / `,`     | `out pins,1`, `in pins,1`              |

PIO allows **precise stepwise manipulation**, with no multiplication, division, or complex math. This makes it a **natural match for Brainfuck**, which also works by single-step increments, decrements, and conditional loops.

---

## ⚙️ Architecture

- **1 PIO state machine = 1 Brainfuck interpreter core**
- **8 cores** on a standard Pi Pico (2 PIO blocks × 4 state machines)
- **12 cores** on the Pico W2 (3 PIO blocks)
- Uses **27-bit operand** in each instruction to store jump addresses
- All instructions are 32-bit values, dispatched via `out pc,5`

PIO executes instructions independently from the CPU — no polling or interrupts. Once started, the state machines run the program purely in hardware.

---

## 📦 File Structure

🧠 High-Level Overview

We are using:
	•	Manual pull / push: Full control over instruction fetch and FIFO handling.
	•	5-bit dispatch via out pc, 5 — Brainfuck opcodes.
	•	Bit-serial I/O through GPIO (in pins, 1 and out pins, 1).
	•	A flexible flow mechanism with jmp ~x, x--, y--, and mov x,~x to handle step instructions and wraparound behavior.
	•	Dedicated logic for looping ([, ]) using push/pull and decode logic.

⸻

🧩 Detailed Instruction Map (with PC index meaning):

PC Index	Label (Instruction)	Brainfuck Equivalent	Description
0	instruction_at_pc_zero_which_is_closing_sq_bracket	]	If x is non-zero, jump to loop start. Else, continue.
2	instruction_at_pc_two_which_is_starting_sq_bracket	[	If x is zero, discard instructions until ].
4	instruction_at_pc_four_which_substract_one_from_data_which_is_x	-	Decrement data value.
5	instruction_at_pc_five_which_bit_flips_data_which_is_x_if_previous_instruction_falls_thrrough_wrap_arround_or_overflow_handelling_is_observed	(Overflow handling)	Bit flip — restores two’s complement for x wraparound
7	instruction_at_pc_seven_which_substract_one_from_tape_address_which_is_y	<	Decrement data pointer.
8	instruction_at_pc_eight_which_bit_flips_tape_address_which_is_y_if_previous_instruction_falls_thrrough_wrap_arround_or_overflow_handelling_is_observed	(Overflow handling)	Bit flip for y.
9	bit_reversed_x_register	(Helper)	Reverses bits of x. Could be prep for display or masking.
10	send_from_y	(Custom)	Sends the value of y via bit-serial pins.
12	bring_into_x	,	Reads a value from pins into x.
15	go_to_start_of_the_loop	] target	Pushes return point. Used for looping logic.
16	go_to_throw_away_loop_till_the_end_of_loop	Skipping loop	Pulls and discards instructions till matching ].
19	send_from_x	.	Sends value in x via pins.
21	goto_wrap	Dispatch	Pulls next instruction, decodes using out pc, 5.


⸻

🔄 Instruction Fetch and Dispatch

goto_wrap:
.wrap_target
pull          ; Manually pull instruction from TX FIFO (not auto-pull)
out pc,5      ; Lower 5 bits determine the next instruction (BF opcode)
.wrap

This pattern gives you full control over the instruction fetch rate and ensures predictable behavior. It’s especially useful when multiple interpreters or DMA-driven streams are in play.

⸻

🧠 Key Design Decisions
	•	Explicit FIFO usage: By disabling auto-pull/push, you ensure:
	•	No accidental overwriting or misalignment of data.
	•	Full compatibility with complex fetch mechanisms like DMA chaining.
	•	Wraparound handling (mov x,~x after decrement):
	•	Emulates unsigned wrap/underflow conditions common in BF implementations.
	•	Keeps the logic tight without additional branches.

⸻

💡 Suggestions / Enhancements (Optional):
	1.	Instruction Visualizer / Annotator: You could write a Python utility that parses a BF program and emits the encoded 32-bit words, highlighting:
	•	Opcode (out pc, 5)
	•	Jump target / operand (27-bit immediate)
	2.	DMA preload + state machine scheduling:
	•	Since you’re doing pull manually, DMA engines can prepopulate FIFO buffers for multiple SMs in a chained fashion — setting the stage for full automation.
	3.	External RAM Interface:
	•	Since memory addressing is done via y, and data is in x, you could extend send_from_y and bring_into_x to interface with SPI RAM or USB-connected host memory — allowing true virtual 

✅ What’s New in This Version

1. ✅ Auto Push is Enabled
	•	With auto push, mov x,isr automatically causes the x register value to be pushed to the RX FIFO after a 32-bit in completes (if threshold met).
	•	You’ve retained manual control of pull (instruction fetch), which is a good design for future chained DMA booting.

2. ✅ Bit-Reversal Support Added

bit_reversed_x_register:
mov x,::x

	•	This is useful for protocols that require MSB-first data ordering (e.g., SPI, UART).
	•	Could also be used for visualization (like LED patterns or graphical output transforms).

3. ✅ Instruction Reflow Cleaned
	•	Unused or redundant logic paths seem trimmed.
	•	Your jmp ~x and jmp ... combinations cleanly model the semantics of [ and ] with better alignment to how branching works in BF.

⸻

📜 Instruction Set Summary

Here’s a refined map of your current 32-instruction space:

PC	Instruction Label	Function	Brainfuck Equivalent
0	instruction_at_pc_zero_which_is_closing_sq_bracket	Loop close (back if x ≠ 0)	]
2	instruction_at_pc_two_which_is_starting_sq_bracket	Loop start (skip if x == 0)	[
4	instruction_at_pc_four_which_substract_one_from_data_which_is_x	Decrement current cell value	-
5	instruction_at_pc_five_which_bit_flips_data_which_is_x_if_previous_instruction_falls_thrrough_wrap_arround_or_overflow_handelling_is_observed	Wraparound fix	(BF-compatible wrap)
7	instruction_at_pc_seven_which_substract_one_from_tape_address_which_is_y	Move left	<
8	instruction_at_pc_eight_which_bit_flips_tape_address_which_is_y_if_previous_instruction_falls_thrrough_wrap_arround_or_overflow_handelling_is_observed	Wraparound fix	(for pointer y)
9	bit_reversed_x_register	Bit-reverse of x	(helper / visual)
10	send_from_y → send_from_y_to_mem	Emit pointer via GPIO	@y (custom)
12	bring_into_x → bring_into_x_reg	Read byte from GPIO	,
15	go_to_start_of_the_loop	Load loop address from OSR	[ target addr
16	go_to_throw_away_loop_till_the_end_of_loop	Skip loop when x == 0	loop skip
19	send_from_x → send_from_x_to_mem	Emit data via GPIO	.
21	goto_wrap	Dispatcher: pull, out pc,5	dispatching next cmd

(Unlisted slots are available or reserved for future operations.)

⸻

📦 Current Architectural Highlights
	•	Instruction Structure: 32-bit (5-bit opcode + 27-bit operand)
	•	State Machine Behavior:
	•	Manual pull to fetch instructions
	•	Auto push is used to send input data into RX FIFO
	•	Bit-serial I/O via in pins,1 and out pins,1
	•	Memory Virtualization:
	•	External SPI PSRAM possible (via GPIO)
	•	Tape pointer (y) and cell data (x) managed in registers
	•	Instruction Dispatch via out pc,5 ensures deterministic branching

⸻

🧠 Next Steps to Consider
	1.	Build a Lookup Table / Preprocessor
Write a small tool (Python or C) to:
	•	Map Brainfuck characters to 5-bit opcodes
	•	Embed loop addresses in the upper 27 bits
	•	Produce a binary stream to send to each SM’s FIFO
	2.	Prepare a Debug/Visualization Harness
Optional: Implement GPIO debugging output (like pulsing a pin at wrap or loop entry) to watch interpreter behavior in real time with a logic analyzer or oscilloscope.
	3.	Document Instruction Format in a Markdown Spec

⸻

🔁 Loop Control Logic — [ and ] via Embedded Addresses

At the PIO instruction memory address PC = 0, we implement the logic for the Brainfuck ] (loop-close) command.

🧠 How it Works
	•	The x register holds the current memory cell’s value.
	•	On encountering ], the logic checks:

jmp ~x, goto_wrap
in osr, 27
push

	•	If x ≠ 0: jump back to the loop (continue looping)
	•	If x == 0: loop ends. We:
	1.	Extract the 27-bit jump address (encoded in the upper bits of the instruction) using in osr, 27
	2.	Push it into the RX FIFO via push, acting as a signal to the CPU

⸻

🔔 What Happens Next
	•	The RX FIFO interrupt wakes the main ARM Cortex-M0+ core
	•	The CPU interprets the pushed 27-bit address as the location of the matching [ (loop start)
	•	It resumes pushing instructions from that location into the PIO’s TX FIFO

This enables tight loop control even though the actual instruction stream lives on the CPU side. The PIO handles:
	•	Arithmetic
	•	Memory pointer control
	•	Step logic

While the CPU only participates for jump address resolution and instruction streaming.

⸻

🎯 Why This Design?

Brainfuck’s [ and ] require:
	•	Conditional branching
	•	Jump-to-address behavior
	•	And an implicit call stack-like pairing

The Pi Pico PIO doesn’t have call/return instructions or general memory, so we:
	•	Embed the matching loop address inside each instruction as a 27-bit operand
	•	Use in osr, 27 and push to hand control back to the CPU
	•	Let the CPU decide where to resume from in the instruction stream

✅ This division of responsibilities gives us a hybrid interpreter:
Hardware-native execution with software-assisted loop resolution.


🧠 Internal Architecture Summary

✅ Instruction Format

Each Brainfuck instruction is a 32-bit word sent via the PIO’s pull FIFO:

Bits	Purpose
0–4	5-bit opcode (used in out pc, 5) to jump to the PIO instruction
5–31	27-bit operand — typically used to encode jump addresses (e.g., for [ and ])

🔢 This gives you 2⁷² = 134,217,728 unique instruction addressable positions for branching or memory reference logic — more than enough for typical BF programs.

⸻

✅ Register Use in PIO

Register	Size	Role
x	32 bits	Data register — holds the value at current cell (+, -)
y	32 bits	Tape pointer — holds current memory address (>, <)
osr	32 bits	Output shift register — used for emitting x/y to GPIO or memory
isr	32 bits	Input shift register — used for reading data from GPIO

✅ All registers are full 32-bit width, consistent with the RP2040 PIO architecture.

⸻

📌 Implications
	•	✅ The 27-bit operand field allows for very large instruction address space — which is critical for nested loops ([ and ]) that need to jump deep into a large instruction stream.
	•	✅ Full 32-bit x and y registers mean:
	•	You can represent full 32-bit cell values (not just 8-bit BF cells).
	•	You can support a massive virtual memory tape, potentially spanning external RAM or a host-side memory.

# 🧠 `bfpio.py` — Brainfuck to RP2040 PIO Instruction Encoder

The `bfpio.py` script converts Brainfuck programs into 32-bit hexadecimal instructions suitable for direct execution on the **RP2040’s PIO (Programmable I/O)** state machines. This serves as the compiler frontend for the hardware-only Brainfuck interpreter called **Abhadra**.

# ChatGPT Discussion
https://chatgpt.com/share/686a8b03-1be4-8011-b488-57ae924e863f


V2:-
https://chatgpt.com/share/69216c3c-9e88-8011-b5c0-c25a86bc7243
