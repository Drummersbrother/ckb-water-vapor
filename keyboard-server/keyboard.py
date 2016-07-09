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
import os.path
import sys
import threading
import time

import falcon

platform = sys.platform


class Keyboard(object):
    """This class represents a keyboard connected to the ckb-daemon.
    This class is supposed to be used quite like a file-descriptor, use it with a with statement.
    """

    def __enter__(self):
        """Creates a keyboard object if there is one connected.
        If there are multiple keyboards connected, it prompts the user to choose between them.
        If there are no no keyboards connected, it tells the user to connect one and then exits the program.
        """

        # We check if we're on mac or linux (the file-path is different on mac)
        if platform.startswith("linux"):
            # We're on linux, FOSS FTW!
            # We check if ckb-daemon is running (by checking if the keyboard info file exists)
            if os.path.exists("/dev/input/ckb0"):
                # ckb-daemon is running, so we store the filepath prefix
                self.prefix = "/dev/input/"

            else:
                # ckb-daemon is not running or it isn't installed
                print(
                    "ckb-daemon isn't running, (or isn't installed). Please install and/or run ckb-daemon and try again.")

        elif platform.startswith("darwin"):
            # We're on macOS, elegancy and simplicity FTW!
            # We check if ckb-daemon is running (by checking if the keyboard info file exists)
            if os.path.exists("/var/run/ckb0"):
                # ckb-daemon is running, so we store the filepath prefix
                self.prefix = "/var/run/"

            else:
                # ckb-daemon is not running or it isn't installed
                print(
                    "ckb-daemon isn't running, (or isn't installed). Please install and/or run ckb-daemon and try again.")

        else:
            # Who the fuck runs anything other than linux and macOS nowadays!?
            # We exit because ckb doesn't exist on any other platforms than the ones we tested for
            print("You're not running on a supported OS, please install gentoo and git gud.")
            exit()

        # We check how many devices that are connected
        with open(self.prefix + "ckb0/connected") as connection_file:
            # We calculate the number of devices connected by counting the number of lines with content in the file
            num_connected_devices = len(connection_file.read()[:-1].splitlines())

        # We check if there are any connected devices at all
        if num_connected_devices > 0:
            # We load the keyboard_server_config file to get the list of keyboards that are supported
            with open("keyboard_server_config.json", encoding="utf-8") as config_file:
                config_supported_devices = json.load(config_file)["supported_devices"]

            # The list of supported device numbers (the * in ckb*)
            supported_devices = []

            # We loop through all devices and check if their features node starts with a supported device name
            for i in range(1, num_connected_devices + 1):
                # We load the features file for the current device and check if the first line is a supported device identifier
                with open(self.prefix + "ckb" + str(i) + "/features") as features:

                    if " ".join(features.read().split(" ")[:2]) in config_supported_devices:
                        # The device is supported, so we append the device number
                        supported_devices.append(i)

            # We check how many supported devices that were detected
            if len(supported_devices) == 0:
                # There are no connected keyboards that are supported (maybe the user just has a corsair mouse?)
                # We tell the user to connect a keyboard and try again
                print("You have not connected any keyboards, please connect a keyboard and try again.")
                exit()

            elif len(supported_devices) == 1:
                # Everything is fine and dandy, the user has 1, and exactly 1, connected supported keyboard
                # We save the path and number of the supported keyboard
                self.keyboard_path = self.prefix + "ckb" + str(supported_devices[0]) + "/"

            else:
                # We make a dict mapping user options to device numbers
                choice_dict = {str(key + 1): value for (key, value) in enumerate(supported_devices)}

                # We ask the user to choose between their devices
                print(
                    "Please input a number corresponding to which of your connected keyboards you want to use.\nHere are the connected keyboards:")
                # We loop through all the choices and output info about that device in a user readable format
                for key in choice_dict:
                    with open(self.prefix + "ckb" + str(choice_dict[key])) as features:
                        # The 38 is the number of chars between the beginning of the line and the device name
                        print("\tNr. {0:s}: {1:s}".format(key, features.readline()[self.prefix + 38:-1]))

                # We force the user to provide proper input or exit
                while True:
                    choice = input("Please input a valid number:")

                    # We check if the choice was a valid one
                    if choice in choice_dict:
                        # We save the path and number of the supported keyboard
                        self.keyboard_path = self.prefix + "ckb" + str(choice_dict[choice]) + "/"

                        # We break out of the while loop
                        break

        else:
            # There are no connected devices, so we tell the user to connect a keyboard and try again
            print("You don't have any connected keyboards, please connect a keyboard and try again.")
            exit()

        # We have a supported keyboard with it's path, so we print out some info about it
        with open(self.keyboard_path + "model") as model_file:
            print("Using keyboard: " + model_file.read().strip())
            # We seek back to the file beginning to read it again
            model_file.seek(0)

            # We save the keyboard name for future usage
            self.verbose_name = model_file.read()

        # We open the pollrate file and save the pollrate
        with open(self.keyboard_path + "pollrate") as pollrate_file:
            # We parse and save the pollrate
            self.pollrate = int(pollrate_file.read()[:1])

        # We open the features file and save the list of features the device supports
        with open(self.keyboard_path + "features") as features_file:
            # We parse and save the supported features
            self.features = features_file.read().split(" ")[2:]

        # We open the serial file and save the serial number of the device
        with open(self.keyboard_path + "serial") as serial_file:
            # We save the contents of the serial file
            self.serial = serial_file.read().strip()

        # The list of notify node numbers that are being used
        used_notify_nodes = []

        # We check what notifying nodes are being used
        for i in range(1, 10):
            # We check if the file exists as a notifying node
            if os.path.isfile(self.keyboard_path + "notify" + str(i)):
                # We append the number to the list of used nodes
                used_notify_nodes.append(i)

        # We find a notify node number that isn't used
        # If all notify nodes are being used we tell the user that there aren't any nodes available and exit
        for i in range(1, 10):
            # We check if the node number is used
            if i not in used_notify_nodes:
                # We save the notify node number
                self.notify_node_nr = i
                break
        else:
            # If we didn't find a notify node number that wasn't used, we tell the user to check what programs are using the keyboard and try again
            print(
                "All notifying nodes are being used, please check what programs are using the keyboard and try again.")
            exit()

        # We create various Lock objects to mak the whole class thread-safe
        self.cmd_lock = threading.Lock()
        self.notify_lock = threading.Lock()

        # We found a notify node, so we register it to the daemon for this keyboard
        self.execute_command("notifyon " + str(self.notify_node_nr))

        # We save the notify path for the keyboard
        self.notify_path = self.keyboard_path + "notify" + str(self.notify_node_nr)

        # We wait for the notification file to exist
        timeout = time.time() + 2
        while not os.path.exists(self.notify_path) and time.time() < timeout:
            time.sleep(0.01)
        if not os.path.exists(self.notify_path):
            # The daemon didn't create the notification file fast enough
            print("Failed to create notification file before timeout.")
            exit()

        # We make this device go into software controlled mode
        self.execute_command("active")

        return self

    def __exit__(self, *args):
        """This method is called when the instance exits the with statement and needs to be closed again."""

        # We close the notifying node for this device
        self.execute_command("notifyoff " + str(self.notify_node_nr))

        # We make this device go back to hardware controlled mode
        self.execute_command("idle")

    def __str__(self):
        """This method provides a string representation of the keyboard object."""
        return "keyboard.Keyboard object:\nKeyboard name: {0:s}\nKeyboard serial number: {1:s}\nKeyboard pollrate: {2:d} ms\nKeyboard path: {3:s}\nKeyboard notify node path: {4:s}\nKeyboard features: {5:s}".format(
            self.verbose_name.strip(), self.serial, self.pollrate, self.keyboard_path, self.notify_path,
            ", ".join(self.features))

    def execute_command(self, cmd: str):
        """This method is used to use a string as a command to the daemon, only use this if you know what you're doing."""

        # We do the file-writing with a lock to ensure thread-safety
        with self.cmd_lock:
            # We open the cmd file and write the command into it
            with open(self.keyboard_path + "cmd", mode="w") as cmd_file:
                # We append the command string and a newline
                cmd_file.write(cmd + "\n")

                # We flush the file to get the command written ASAP
                cmd_file.flush()

    def get_notifications(self):
        """This method is used to get the unread notifications from the keyboard notification node.
        Note that this blocks until there is data to read, so only use this directly if you know what you're doing.
        """

        # FIXME This is not getting notifications (only command responses), I'm not seeing them at all actually, how the fuck do I get this to work??!??

        # We do the file-reading with a lock to ensure thread-safety
        with self.notify_lock:
            notify_raw_content = ""
            # We read and save the contents of the notify file for the keyboards
            with open(self.notify_path) as notify_file:
                if os.path.exists(self.notify_path):
                    notify_raw_content += notify_file.readline()
                else:
                    # We don't have a notification node, so we print an error and exit
                    print(
                        "Could not find notification node, please make sure that ckb-daemon is running and that the keyboard hasn't been unplugged and try again")
                    exit()

        # We make a list of all the separate words in the notify file, by splitting the content by space
        notify_content = [x.strip() for x in notify_raw_content.split(" ") if len(x.strip()) > 0]

        return notify_content

    def get_parameter(self, parameter: str):
        """This method is used to get the current parameters of the keyboard.
        This will return the raw ckb-daemon response, so only use this if you know what you're doing.
        """

        # We assume that all input is valid, so do not use this if you don't know what you're doing
        self.execute_command("@" + str(self.notify_node_nr) + " get :" + parameter)

        # We return whatever is printed to our notification node
        return self.get_notifications()

    def get_all_color_pairs(self):
        """This method is used to get the current rgb colors of all keys.
        It returns this data in the form of [(comma_separated_keys, color tuple), (comma_separated_keys, other color tuple), ...] .
        It is guaranteed that the list entries all specify different colours.
        The color tuples are of length 3 and contain 3 255 >= ints >= 0 .
        """

        # We get the "rgb" parameter and remove the first three entries (those are "mode", "mode_number", and "rgb")
        rgb_raw_list = self.get_parameter("rgb")[3:]

        # The list for saving what we're going to output
        rgb_key_color_list = []

        # We loop through the raw get response and parse each entry and then add it to the list
        for index, key_color_pair in enumerate(rgb_raw_list):
            # We check if the pair is the only one in the list (it's the "all" key)
            if len(rgb_raw_list) == 1:
                # We append the value as the "all" key
                rgb_key_color_list.append(("all", (int(key_color_pair[:2], base=16), int(key_color_pair[2:4], base=16), int(key_color_pair[4:6], base=16))))

                # We break out of the loop
                break

            # We store the split version of the entry, to not call the split function multiple times.
            # We know that the number of entries after splitting is always 2, so this won't throw an error.
            keys, color = key_color_pair.split(":")
            rgb_key_color_list.append(
                (keys, (int(color[:2], base=16), int(color[2:4], base=16), int(color[4:6], base=16))))

        # We return the list of keys and colors
        return rgb_key_color_list

    def get_all_key_color_pairs(self):
        """This method simply parses the 'get_all_color_pairs' list
        and returns it in the form of {"key": (color_tuple)}
        where key is a ckb-daemon keycode and color_is a tuple of the same form as 'get_all_color_pairs'
        """

        # We get the rgb keys' colors
        rgb_key_color_pairs = self.get_all_color_pairs()

        # The dict with key to colors mappings
        key_color_dict = {}

        # We loop through all the pairs and append the add the pairs' keys to the dictionary that we're going to return
        for keys_color_pair in rgb_key_color_pairs:
            # We split the key string by the commas that separate the keycodes
            pair_key_list = keys_color_pair[0].split(",")
            # We loop through the keys in the current pair and add that key with it's color to the dictionary
            for key in pair_key_list:
                key_color_dict[key] = keys_color_pair[1]

        return key_color_dict

    def set_key_color(self, key: str, rgb: tuple):
        """This method is used to set a key to a certain rgb (represented as a tuple of ints) color."""

        # We check that the input is valid, else we return False
        if key.replace("_", "").replace(",", "").isalnum():
            # Check if the rgb values are valid
            if not all([256 > int(x) > -1 for x in rgb]) or len(rgb) != 3:
                # The colour values are invalid so we return False
                return False

            else:
                # All arguments are valid, so we execute the command
                self.execute_command("rgb " + key + ":" + "".join([str(format(int(x), "02x")) for x in rgb]))

                # We return True to indicate success
                return True

        else:
            # We return False
            return False

    def set_full_color(self, rgb: tuple):
        """This method is used to set the whole keyboard to a certain rgb (represented as a tuple of ints) color."""

        # Check if the rgb values are valid
        if not all([256 > int(x) > -1 for x in rgb]) or len(rgb) != 3:
            # The colour values are invalid so we return False
            return False

        else:
            # The rgb values are valid, so we execute the command
            self.execute_command("rgb " + "".join([str(format(int(x), "02x")) for x in rgb]))
            # We return True to indicate success
            return True

    def set_multiple_colors(self, keys_and_colors: list, background: tuple = None):
        """This method is used to set multiple keys and (not required) the background to different colors using a single ckb-daemon command.
        keys_and_colors shall be structured like [("w,a,s,d", (255, 255, 0)), ("esc,caps", (0, 0, 255)))]
        """

        # We check that we got keys or background
        if len(keys_and_colors) == 0 and background is None:
            return

        # The part of the finished command that is going to be the individual or groups of keys
        keys_and_colors_command = ""

        # We got valid arguments, so we check if we should use the key list
        if len(keys_and_colors) != 0:

            # We loop through the list to validate all the key and color pairs
            for pair in keys_and_colors:
                if pair[0].replace("_", "").replace(",", "").isalnum():
                    # Check if the rgb values are valid
                    if not all([256 > int(x) > -1 for x in pair[1]]) or len(pair[1]) != 3:
                        # The colour values are invalid so we return False
                        return False

                    else:
                        # If the arguments were valid we append a string for the pair to the individual key part of the command
                        keys_and_colors_command += " " + pair[0] + ":" + "".join(
                            [str(format(int(x), "02x")) for x in pair[1]])

                else:
                    # We return False because the key name is not valid
                    return False

        # We check if the user specified a background color for the command
        if background is not None:

            # We check that the background rgb values are valid
            if not all([256 > int(x) > -1 for x in background]) or len(background) != 3:
                # We return False because the background rgb values are invalid
                return False

            # We execute the command with the background part
            self.execute_command(
                "rgb " + "".join([str(format(int(x), "02x")) for x in background]) + keys_and_colors_command)

            # We return True to indicate success
            return True

        else:
            # We execute the command without the background part
            self.execute_command("rgb " + keys_and_colors_command)
            # We return True to indicate success
            return True

    def cmd_set_fps(self, fps: int):
        """This method is used to set the driver update frequence in updates per second (the fps argument)"""

        # We check that the input fps is valid
        if 61 > int(fps) > 0:
            # The input is valid, so we execute the fps command
            self.execute_command("fps {0:d}".format(int(fps)))

        else:
            # The input is invalid so we raise a ValueError
            raise ValueError

    def cmd_set_notification(self, keys: list):
        """This method is used to enable notifications to the keyboard object's notifying node of all the keys in argument keys."""

        # We check that the key list only contains valid strings, if it's invalid we raise a ValueError
        if len(keys) == 0 or not all([x.replace("_", "").isalnum() for x in keys]):
            # The keys list is invalid, we raise a ValueError
            raise ValueError
        else:
            # The list of keys is valid, so we execute the notify command
            self.execute_command("@" + str(self.notify_node_nr) + " notify " + "".join(keys))

    def cmd_unset_notification(self, keys: list):
        """This method is used to disable notifications to the keyboard object's notifying node of all the keys in argument keys."""

        # We check that the key list only contains valid strings, if it's invalid we raise a ValueError
        if len(keys) == 0 or all([x.replace("_", "").isalnum() for x in keys]):
            # The keys list is invalid, we raise a ValueError
            raise ValueError
        else:
            # The list of keys is valid, so we execute the notify command
            self.execute_command("@" + str(self.notify_node_nr) + " notify " + ":off ".join(keys) + ":off")


class Keyboard_Falcon_Api(object):
    """This class represents and handler the HTTP REST api for a keyboard object."""

    def __init__(self, keyboard):
        """This method initialises the API."""

        # The list of dicts that describe what commands can be user via HTTP GET requests
        self.get_commands = [
            dict(command="get_multiple_key_rgb", method=self.cmd_get_get_multiple_key_rgb)
        ]

        # The list of dicts that describe what commands can be used via HTTP POST requests
        self.post_commands = [
            dict(command="set_rgb_single", method=self.cmd_post_rgb_change_single)
        ]

        self.keyboard = keyboard.__enter__()

    def on_get(self, req, resp):
        """This method handles all get requests to our API."""

        # The requester has to be able to accept json
        if req.client_accepts_json:

            # We check if the user used a command or not
            if req.content_length in (0, None):
                # Everything went ok
                resp.status = falcon.HTTP_200

                # We return the string representation of the keyboard
                resp.body = json.dumps({"keyboard": str(self.keyboard)})

            else:
                # We check if the user want/tries to use a command
                try:
                    # Store the request body
                    req_body = req.stream.read().decode("utf-8")

                    # We try to parse the request as json
                    post_params = json.loads(req_body)

                    # We check that the arguments exist and are valid
                    if post_params["command"]:
                        # We check what command was used
                        for command in self.get_commands:
                            # We check if the current request matches the command
                            if post_params["command"] == command["command"]:
                                # We call the command method with the request object, response object, and the parsed request dictionary
                                command["method"](req, resp, post_params)

                                # No more than one command shall be executed per request
                                break
                        else:
                            # If no command was found we return bad request
                            resp.status = falcon.HTTP_400
                            resp.body = json.dumps({"message": "Invalid command"})

                    else:
                        # Invalid arguments
                        resp.status = falcon.HTTP_400
                        resp.body = json.dumps({"message": "Invalid arguments"})

                    # We're done now
                    return

                except json.JSONDecodeError:
                    resp.status = falcon.HTTP_400
                    resp.body = json.dumps({"message": "Invalid JSON"})
        else:
            # Fuck you user
            resp.status = falcon.HTTP_417
            resp.body = json.dumps({"message": "Client doesn't accept JSON"})

    def on_post(self, req, resp):
        """This method handles all post requests to our API."""

        # The requester has to be able to accept json
        if req.client_accepts_json:

            try:
                if req.content_length in (0, None):
                    raise json.JSONDecodeError

                # We store the request body
                req_body = req.stream.read().decode("utf-8")

                # We try to parse the request as json
                post_params = json.loads(req_body)

                # We check that the arguments exist and are valid
                if post_params["command"]:
                    # We check what command was used
                    for command in self.post_commands:
                        # We check if the current request matches the command
                        if post_params["command"] == command["command"]:
                            # We call the command method with the request object, response object, and the parsed request dictionary
                            command["method"](req, resp, post_params)

                            # No more than one command shall be executed per request
                            break
                    else:
                        # If no command was found we return bad request
                        resp.status = falcon.HTTP_400
                        resp.body = json.dumps({"message": "Invalid command"})

                else:
                    # Invalid arguments
                    resp.status = falcon.HTTP_400
                    resp.body = json.dumps({"message": "Invalid arguments"})

                # We're done now
                return

            except json.JSONDecodeError:
                resp.status = falcon.HTTP_400
                resp.body = json.dumps({"message": "Invalid JSON"})

        else:
            # Fuck you user
            resp.status = falcon.HTTP_417

    def cmd_get_get_multiple_key_rgb(self, req, resp, post_params):
        """This method handles getting and sending back the rgb colors of keys on the keyboard.
        The request arguments should include a list of keycodes as strings called "keys", and optionally a string called "color_format" that is either "hex" or "ints"
        If the argument "color_format" is "hex" the color of each key is sent back as a lowercase 6 char hex string, where pairs of chars represents the (in order of pairs) R, B, and G values of the corresponding key ,
        else the color of each key is sent back as a list of 3 ints representing the R, G, and B values of the corresponding key.
        If the HTTP status code of the response is not 200, the response will include a "message" property with an error message.
        If the HTTP status code of the response is 200, the response will include a property called "keys", where all the valid keycodes (that exist on the server keyboard) that were specified in the request are names of properties.
        Those properties are either lists of ints, or lowercase hex strings, depending on the "color_format" request argument.
        A keycode may be returned with a color of the background color of the keyboard, although this only happens when the whole server keyboard is the same color.
        If the whole server keyboard is not the same color, keycodes that are not on the server keyboard will not have a property in the response.
        This means that the response may be equal to json.dumps({"key": {}})
        """

        # We check if all arguments exist
        if "keys" in post_params["arguments"]:
            if type(post_params["arguments"]["keys"]) == list:
                # We loop through the keys list and check that all items are strings
                if all([type(x) == str for x in post_params["arguments"]["keys"]]):
                    # We get the dictionary of keys to color from the keyboard
                    key_color_dict = self.keyboard.get_all_key_color_pairs()

                    # The dict we're going to return
                    requested_keys_dict = {"keys": {}}

                    # We check if the user wanted the response colors to be hex or not
                    if "color_format" in post_params["arguments"]:
                        if post_params["arguments"]["color_format"] == "hex":
                            # We do the same thing, but we add the color values as lists of ints
                            for key in key_color_dict:
                                if key in post_params["arguments"]["keys"]:
                                    requested_keys_dict["keys"][key] = ("".join([str(format(int(x), "02x")) for x in key_color_dict[key]]))
                                else:
                                    # We check if the whole keyboard is one color
                                    if "all" in key_color_dict:
                                        requested_keys_dict["keys"][key] = ("".join([str(format(int(x), "02x")) for x in key_color_dict["all"]]))
                        else:
                            # We do the same thing, but we add the color values as lists of ints
                            for key in key_color_dict:
                                if key in post_params["arguments"]["keys"]:
                                    requested_keys_dict["keys"][key] = key_color_dict[key]
                                else:
                                    # We check if the whole keyboard is one color
                                    if "all" in key_color_dict:
                                        requested_keys_dict["keys"][key] = key_color_dict["all"]
                    else:
                        # We do the same thing, but we add the color values as lists of ints
                        for key in key_color_dict:
                            if key in post_params["arguments"]["keys"]:
                                requested_keys_dict["keys"][key] = key_color_dict[key]
                            else:
                                # We check if the whole keyboard is one color
                                if "all" in key_color_dict:
                                    requested_keys_dict["keys"][key] = key_color_dict["all"]

                    # We set the HTTP status code to 200 and the body of the response to the proper JSON response
                    resp.status = falcon.HTTP_200
                    resp.body = json.dumps(requested_keys_dict)

                    # We're done, so we return
                    return

        # Invalid arguments
        resp.status = falcon.HTTP_400
        resp.body = json.dumps({"message": "Invalid arguments"})

    def cmd_post_rgb_change_single(self, req, resp, post_params):
        """This method handles changing the keys of the keyboard to a single colour."""

        # We check if all arguments exist
        if post_params["arguments"]["key"] and post_params["arguments"]["color"]:
            if self.is_hex_color(post_params["arguments"]["color"]):

                # We check if the command executed successfully
                if self.keyboard.set_key_color(post_params["arguments"]["key"], (
                        int(post_params["arguments"]["color"][:2], base=16),
                        int(post_params["arguments"]["color"][2:4], base=16),
                        int(post_params["arguments"]["color"][4:], base=16))):
                    # Successfully executed the command
                    resp.status = falcon.HTTP_200
                    resp.body = json.dumps({"message": "Command successfully executed"})

                    return

                else:
                    # Invalid arguments
                    resp.status = falcon.HTTP_400
                    resp.body = json.dumps({"message": "Invalid arguments"})

            else:
                # Invalid arguments
                resp.status = falcon.HTTP_400
                resp.body = json.dumps({"message": "Invalid arguments"})

        else:
            # Invalid arguments
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({"message": "Invalid arguments"})

    def is_hex_color(self, string: str):
        """This method returns true if string is a properly formatted (lower case) hex color."""

        if len(string) != 6:
            return False

        return all(c in set("1234567890abcdef") for c in string)
