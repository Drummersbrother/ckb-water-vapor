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
import select
import sys
import threading
import time

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
            # We load the code_config file to get the list of keyboards that are supported
            with open("code_config.json", encoding="utf-8") as config_file:
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
            print("All notifying nodes are being used, please check what programs are using the keyboard and try again.")
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
            self.verbose_name.strip(), self.serial, self.pollrate, self.keyboard_path, self.notify_path, ", ".join(self.features))

    def execute_command(self, cmd):
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
        """This method is used to get the unread notifications from the keyboard in the form of four lists.
        The first is the list of regular keys that have been pressed since the last read.
        The second is the list of regular keys that have been released since the last read.
        The third is the list of indicator LEDs that have been turned on since the last read.
        The fourth is the list of indicator LEDs that have been turned off since the last read
        """

        # FIXME This is not getting notifications, I'm not seeing them at all actually, how the fuck do I get his to work??!??

        # The list of regular keys that have been pressed since the last read
        regular_pressed = []
        # The list of regular keys that have been released since the last read
        regular_released = []
        # The list of indicator LEDs that have been turned on since the last read
        indicator_on = []
        # The list of indicator LEDs that have been turned off since the last read
        indicator_off = []

        # We do the file-reading with a lock to ensure thread-safety
        with self.notify_lock:
            notify_raw_content = ""
            # We read and save the contents of the notify file for the keyboards
            try:
                notify_file = os.open(self.notify_path, os.O_NONBLOCK | os.O_RDONLY)
                # Wait for readable data or errors, and we timeout after 1 / 120 seconds
                read_events, write_events, error_events = select.select([notify_file], [], [notify_file], 1 / 120)
                notify_raw_content = os.read(notify_file, 2)
                print(notify_raw_content)
                if error_events:
                    print("Error events %s" % error_events)

                if read_events:
                    notify_raw_content = notify_file.read()
                    print(notify_raw_content)

                os.close(notify_file)

            except OSError as e:
                if e.errno == 11:
                    os.close(notify_file)
                    pass
                else:
                    print(e)
                    os.close(notify_file)
                    exit()

            else:
                notify_raw_content = ""

        # We make a list of all the separate words in the notify file, by splitting the content by space
        notify_content = [x.strip() for x in notify_raw_content.split(" ") if len(x)]

        return notify_content

    def set_key_color(self, key, rgb):
        """This method is used to set a key to a certain rgb (represented as a tuple of ints) color."""

        # We check that the input is valid, else we throw a valueerror
        if key.replace("_", "").replace(",", "").isalnum():
            # Check if the rgb values are valid
            if max([(int(x) > 255 or int(x) < 0) for x in rgb]) or len(rgb) != 3:
                # The colour values are invalid so we raise valueerror
                raise ValueError

            else:
                # All arguments are valid, so we execute the command
                self.execute_command("rgb " + key + ":" + "".join([str(format(int(x), "02x")) for x in rgb]))

        else:
            # We raise a ValueError
            raise ValueError

    def set_full_color(self, rgb):
        """This method is used to set the whole keyboard to a certain rgb (represented as a tuple of ints) color."""

        # Check if the rgb values are valid
        if max([(int(x) > 255 or int(x) < 0) for x in rgb]) or len(rgb) != 3:
            # The colour values are invalid so we raise valueerror
            raise ValueError

        else:
            # The rgb values are valid, so we execute the command
            self.execute_command("rgb " + "".join([str(format(int(x), "02x")) for x in rgb]))

    def set_multiple_colors(self, keys_and_colors, background=None):
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
                    if max([(int(x) > 255 or int(x) < 0) for x in pair[1]]) or len(pair[1]) != 3:
                        # The colour values are invalid so we raise valueerror
                        raise ValueError

                    else:
                        # If the arguments were valid we append a string for the pair to the individual key part of the command
                        keys_and_colors_command += " " + pair[0] + ":" + "".join(
                            [str(format(int(x), "02x")) for x in pair[1]])

                else:
                    # We raise a ValueError because the key name is not valid
                    raise ValueError

        # We check if the user specified a background color for the command
        if background is not None:

            # We check that the background rgb values are valid
            if max([(int(x) > 255 or int(x) < 0) for x in background]) or len(background) != 3:
                # We raise a ValueError because the background rgb values are invalid
                raise ValueError

            # We execute the command with the background part
            self.execute_command(
                "rgb " + "".join([str(format(int(x), "02x")) for x in background]) + keys_and_colors_command)

        else:
            # We execute the command without the background part
            self.execute_command("rgb " + keys_and_colors_command)

    def cmd_set_fps(self, fps):
        """This method is used to set the driver update frequence in updates per second (the fps argument)"""

        # We check that the input fps is valid
        if 61 > int(fps) > 0:
            # The input is valid, so we execute the fps command
            self.execute_command("fps {0:d}".format(int(fps)))

        else:
            # The input is invalid so we raise a ValueError
            raise ValueError

    def cmd_set_notification(self, keys):
        """This method is used to enable notifications to the keyboard object's notifying node of all the keys in argument keys."""

        # We check that the key list only contains valid strings, if it's invalid we raise a ValueError
        if len(keys) == 0 or max([not x.replace("_", "").isalnum() for x in keys]):
            # The keys list is invalid, we raise a ValueError
            raise ValueError
        else:
            # The list of keys is valid, so we execute the notify command
            self.execute_command("@" + str(self.notify_node_nr) + " notify " + "".join(keys))

    def cmd_unset_notification(self, keys):
        """This method is used to disable notifications to the keyboard object's notifying node of all the keys in argument keys."""

        # We check that the key list only contains valid strings, if it's invalid we raise a ValueError
        if len(keys) == 0 or max([not x.replace("_", "").isalnum() for x in keys]):
            # The keys list is invalid, we raise a ValueError
            raise ValueError
        else:
            # The list of keys is valid, so we execute the notify command
            self.execute_command("@" + str(self.notify_node_nr) + " notify " + ":off ".join(keys) + ":off")