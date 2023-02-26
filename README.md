Software-only capacitive touch for the Raspberry Pi Pico
=

Any GPIO pin can be used as a capacitive touch sensor.

This code uses a PIO program to detect the capacitance of a finger. First the pin is set to output and pulled low. Then it's set to input with the internal pull up enabled, and the PIO counts how long it takes to go high. There's a tiny difference in the timing of this count depending on whether there's a finger nearby, and by repeating the test thousands of times in a loop, that difference is amplified.

The PIO loops for a fixed length of time (about 16ms, for a 60Hz update rate), and returns a count of the number of charge / discharge cycles.

The Python program tracks the minimum and maximum counts, and turns the current count into a 0-1 level.


