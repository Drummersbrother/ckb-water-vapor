"""
The MIT License (MIT)

Copyright (c) 2016 Hugo Berg

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import math
import time

import keyboard as keyboard_file


def main():
    """The main method of the project."""

    # We get the keyboard, if there isn't any keyboards connected, the program will exit here
    with keyboard_file.Keyboard() as keyboard:

        # We print information about the keyboard object
        print(keyboard)

        # We set the keyboard fps to 30
        keyboard.cmd_set_fps(30)

        curr_x = 0

        while True:
            time.sleep(1 / 30)
            curr_x += math.pi / 100
            curr_x %= math.pi * 2
            keyboard.set_multiple_colors([("w,a,s,d,up,left,down,right", (int(255 * (math.sin(curr_x) + 1) / 2), ) * 3)], (int(255 * (math.sin(curr_x) + 1) / 2), 0, 0))

if __name__ == "__main__":
    main()