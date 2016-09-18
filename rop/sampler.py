#!/usr/bin/env python

from roplib import *

def setup_func():
    r = Ropper()

    r.irq_global_disable()

    # Set up FEB0h peripheral: Enabled, wait enabled, charge pump on
    r.poke(reg_wcon, 0xb0)

    # Usually the tablet uses a 750 kHz carrier, but we can reprogram it.
    r.set_wclk_freq(125000)

    # How long is the transmit burst? The tablet's analog frontend is half-duplex.
    # This is roughly how many half-cycles of carrier we generate between each
    # analog measurement. Larger values give a stronger carrier signal, but they
    # also give us fewer samples per target-visible clock, so the data can come in
    # too fast for us to sample.
    r.poke(reg_wsnd, 16)

    r.poke(reg_wrcv, 127)               # Receive length (max)
    r.poke(reg_wwai, 127)               # Repeat delay / ADC conversion time (max)
    r.pokew(reg_wsadr, adr_y[0])        # Where to transmit (Y00 has the lowest loss and is on the front side)
    r.memcpy(reg_wradr, reg_wsadr, 2)   # Receive at the same spot

    # Pre-load packet header
    r.poke(ep1_buffer + 0, 2)
    r.poke(reg_ep1cnt, 9)

    return r

def loop_func(precopy):
    r = Ropper()

    # Send USB packet (buffered in temp ram)
    r.memcpy(ep1_buffer + 1, factory_temp_ram, 8)
    r.le16(ep1sta_bit3_set)

    for bit in range(4):

        # Initiate scanning, one-shot
        r.poke(reg_wcon, 0xd0)

        # Store previous ADC result
        r.memcpy(factory_temp_ram + bit*2, reg_adrlc, 2)

        # Tuned delay to start ADC after integration ends
        r.delay(0.3)
        r.adc_start()

        # Turn the charge pump back on during the wait
        r.poke(reg_wcon, 0xb0)

        # Delay long enough for ADC conversion to be relatively undisturbed
        if bit < 3: precopy(r)

    return r

if __name__ == '__main__':
    write_loop(setup_func(), loop_func)
