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

import json
import threading
import time

import requests


def __init__():
    """This method starts a simple client that lights all the (alphanumeric + some more) keys that correspond to the text the user inputs."""

    # We make some variables global so the request thread can access them
    global char_list, char_lock, mc, fg, should_exit, activation_time, server_url, special_dict

    # We get the server ip/url
    server_url = "http://" + input("Please input url or IP to the keyboard server:") + ":42069/keyboard"

    # A dictionary that maps the result of pressing a key in input() to the keycode for ckb-daemon and a boolean indicating if this input is generated by pressing the shift (assumed leftshift)
    special_dict = {
        " ": ("space", False),
        "å": ("lbrace", False),
        "ä": ("quote", False),
        "ö": ("colon", False),
        ",": ("comma", False),
        ".": ("dot", False),
        "-": ("slash", False),
        "_": ("slash", True),
        "<": ("bslash_iso", False),
        "'": ("hash", False),
        "¨": ("rbrace", False),
        "§": ("grave", False),
        "+": ("minus", False),
        "=": ("0", True),
        "!": ("1", True),
        '"': ("2", True),
        "#": ("3", True),
        "¤": ("4", True),
        "%": ("5", True),
        "&": ("6", True),
        "/": ("7", True),
        "(": ("8", True),
        ")": ("9", True),
        ">": ("bslash_iso", True),
        ";": ("comma", True),
        ":": ("dot", True),
    }

    # Some colors
    bg = "000000"
    # The color to show when transitioning between the states
    mc = "666666"
    fg = "ffffff"

    # The list of chars that we're going to output to the keyboard
    char_list = []

    # The lock for the char list
    char_lock = threading.Lock()

    # When this is true it indicates to the request thread that it should exit ASAP
    should_exit = False

    # The time it will take between activating a key and seeing it in the foreground color
    activation_time = 0.5

    # The thread that is going to do all the actual requests
    request_thread = threading.Thread(target=output_colors)

    # We start the thread
    request_thread.start()

    # The main loop
    while True:
        # We check if we should exit
        if should_exit:
            print("Exiting")
            # IDK if this will ever be needed, but maybe some edge-case somewhere will use this
            request_thread.join()
            exit()

        # We get text from the user
        raw_input = input("")

        # If the user just pressed enter we make the whole keyboard the background color
        if raw_input == "_clear":
            # We send a request to the server to make the whole keyboard the background color
            requests.post(server_url,
                          data=json.dumps({"command": "rgb_change_single", "arguments": {"key": "all", "color": bg}}))

        elif raw_input == "_exit":
            # We exit
            print("Exiting")
            # We signal to the request thread that it should exit
            should_exit = True
            # We wait for the thread to exit
            request_thread.join()
            exit()

        elif raw_input.startswith("_act_time"):
            # We change the activation time to the number of seconds the user specifies
            try:
                activation_time = float(raw_input[10:])
            except ValueError:
                print("Invalid activation time.")

        else:
            # The user inputted actual data, so we remove all non-alphanumeric chars
            raw_input = ''.join(ch for ch in raw_input if ch.isalnum() or ch in special_dict)

            # We check that there is valid input to send
            if raw_input:
                # We send add the pressed keys to the key list
                # Thread safety please
                with char_lock:
                    char_list.extend([x for x in raw_input])


def output_colors():
    """This is what sends the API requests."""

    global should_exit

    while True:
        if char_list:

            # Thread safety please
            with char_lock:
                # We process the first char in the list
                char = char_list.pop(0)

                # If the char is alphabetical and upper case we add leftshift to the char
                if char.isalpha() and char.isupper():
                    # We add lshift to show that shift was used
                    char_list.insert(0, char.lower())
                    char = "lshift"

                # We check if the char need special handling
                if char in special_dict:
                    # We check if the special char uses shift
                    if special_dict[char][1]:
                        # We add lshift to show that shift was used
                        char_list.insert(0, special_dict[char][0])
                        char = "lshift"
                    else:
                        # We look up the key in the key-handling dictionary
                        char = special_dict[char][0]

            # Try except block to catch connection errors
            try:
                # We send a request to the server to make the char (as they will match to the keycodes) to the middle colour
                requests.post(server_url,
                              data=json.dumps({"command": "rgb_change_single", "arguments": {"key": char, "color": mc}}))
            except requests.exceptions.ConnectionError:
                print("Error when connecting to keyboard server, are you sure the server url is correct? (Press return to exit)")
                # We signal to the main thread should exit
                should_exit = True
                return

            time.sleep(activation_time / 2)

            # Try except block to catch connection errors
            try:
                # We send a request to the server to make the char (as they will match to the keycodes) to the foreground color
                requests.post(server_url,
                              data=json.dumps({"command": "rgb_change_single", "arguments": {"key": char, "color": fg}}))
            except requests.exceptions.ConnectionError:
                print("Error when connecting to keyboard server, are you sure the server is up? (Press return to exit)")
                # We signal to the main thread should exit
                should_exit = True
                return

            time.sleep(activation_time / 2)

        # We check if we should exit
        if should_exit:
            # We exit
            return

        # We don't want to use 100% cpu while idle
        time.sleep(1 / 20)


if __name__ == "__main__":
    __init__()
