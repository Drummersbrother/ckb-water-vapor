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

    # A dictionary that maps the result of pressing a key in input() to the keycode for ckb-daemon
    special_dict = {
        " ": "space",
        "å": "lbrace",
        "ä": "quote",
        "ö": "colon",
        ",": "comma",
        ".": "dot",
        "-": "slash",
        "_": "slash",
        "<": "bslash_iso",
        "'": "hash",
        "¨": "rbrace",
        "§": "grave",
        "+": "minus",
        "=": "lshift,0",
        "!": "lshift,1",
        '""': "lshift,2",
        "#": "lshift,3",
        "¤": "lshift,4",
        "%": "lshift,5",
        "&": "lshift,6",
        "/": "lshift,7",
        "(": "lshift,8",
        ")": "lshift,9",
        ">": "lshift,bslash_iso",
        ";": "lshift,comma",
        ":": "lshift,dot",
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
    activation_time = 0.1

    # The thread that is going to do all the actual requests
    request_thread = threading.Thread(target=output_colors)

    # We start the thread
    request_thread.start()

    # The main loop
    while True:
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
                    # We look up the key in the key-handling dictionary
                    char = special_dict[char]

            # We send a request to the server to make the char (as they will match to the keycodes) to the middle colour
            requests.post(server_url,
                          data=json.dumps({"command": "rgb_change_single", "arguments": {"key": char, "color": mc}}))

            time.sleep(activation_time / 2)

            # We send a request to the server to make the char (as they will match to the keycodes) to the foreground color
            requests.post(server_url,
                          data=json.dumps({"command": "rgb_change_single", "arguments": {"key": char, "color": fg}}))

            time.sleep(activation_time / 2)

        # We check if we should exit
        if should_exit:
            # We exit
            return

        # We don't want to use 100% cpu while idle
        time.sleep(1 / 20)


if __name__ == "__main__":
    __init__()
