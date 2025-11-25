;
; Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
;
; SPDX-License-Identifier: BSD-3-Clause
;

.program hello

; Repeatedly get one word of data from the TX FIFO, stalling when the FIFO is
; empty. Write the least significant bit to the OUT pin group.
jmp !x,jump_to_the_address ; as x is zero goto to the end of the loop ]
jmp main ; as x is not zero goahead with the execution of the loop [
jmp !x,main ; as x is zero loop starts [ and next instruction is executed
jmp jump_to_the_address ; as the above instruction 
jmp x--,decrement_x ; decrement x by 1
decrement_x:
mov x,~x
out pc,4
jmp y--,decrement_y ; decrement y by 1
decrement_y:
mov y,~y
out pc,4
out y,16
out pc,4
out exec,16
out pc,4
out x,16
out pc,4
move_y_to_external_memory:
mov osr,y
start_transfer_for_y:
out pins,1
jmp !osre,start_transfer_for_y
jmp main
move_x_to_external_memory:
mov osr,x
start_transfer_for_x:
out pins,1
jmp !osre,start_transfer_for_x
jmp main
bring_in_x_from_external_memory:
; set x,16 needs to be done with the out x,16 instead to save one pio assembly space
begin_input_for_x:
in pins,1
jmp x--,begin_input_for_x
mov x,isr
jmp main
jump_to_the_address:
in osr,28
push
main:
.wrap_target
pull
out pc, 4
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
