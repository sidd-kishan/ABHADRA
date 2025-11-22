;
; Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
;
; SPDX-License-Identifier: BSD-3-Clause
;

.program Abhadra_Interpreter_program_instructions

; Repeatedly get one word of data from the TX FIFO, stalling when the FIFO is
; empty. Write the least significant bit to the OUT pin group.

jmp !x,x_is_zero
jmp x_is_not_zero
jmp x--,x_decremented
mov x,~x
x_decremented:
out pc,5
jmp y--,y_decremented
mov y,~y
y_decremented:
out pc,5
in osr,16
out pc,5
mov x,isr
out pc,5
mov y,isr
out pc,5
in isr,1
out pc,5
x_is_not_zero:
x_is_zero:
out_code:
out pins,1
jmp !osre,out_code
.wrap_target
pull
out pc,5
.wrap

% c-sdk {
static inline void hello_program_init(PIO pio, uint sm, uint offset, uint pin) {
    pio_sm_config c = hello_program_get_default_config(offset);

    // Map the state machine's OUT pin group to one pin, namely the `pin`
    // parameter to this function.
    sm_config_set_out_pins(&c, pin, 1);
    // Set this pin's GPIO function (connect PIO to the pad)
    pio_gpio_init(pio, pin);
    // Set the pin direction to output at the PIO
    pio_sm_set_consecutive_pindirs(pio, sm, pin, 1, true);

    // Load our configuration, and jump to the start of the program
    pio_sm_init(pio, sm, offset, &c);
    // Set the state machine running
    pio_sm_set_enabled(pio, sm, true);
}
%}
