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

platform = sys.platform

class Keyboard(object):
    """This class represents a keyboard connected to the ckb-daemon."""

    def __init__(self):
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
                print("ckb-daemon isn't running, (or isn't installed). Please install and/or run ckb-daemon and try again.")

        elif platform.startswith("darwin"):
            # We're on macOS, elegancy and simplicity FTW!
            # We check if ckb-daemon is running (by checking if the keyboard info file exists)
            if os.path.exists("/var/run/ckb0"):
                # ckb-daemon is running, so we store the filepath prefix
                self.prefix = "/var/run/"

            else:
                # ckb-daemon is not running or it isn't installed
                print("ckb-daemon isn't running, (or isn't installed). Please install and/or run ckb-daemon and try again.")

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

                    if " ".join(features.readline().split(" ")[:2]) in config_supported_devices:
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
                # There are more than 1 supported keyboard connected, so we make the user choose between them
                for index, val in enumerate(supported_devices):
                    # We make a dict mapping user options to device numbers
                    choice_dict = {str(key + 1): value for (key, value) in enumerate(supported_devices)}

                    # We ask the user to choose between their devices
                    print("Please input a number corresponding to which of your connected keyboards you want to use.\nHere are the connected keyboards:")
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
            print("You have not connected any keyboard, please connect a keyboard and try again.")
            exit()


        # We have a supported keyboard with it's path, so we print out some info about it
        with open(self.keyboard_path + "model") as model_file:
            print("Using keyboard: " + model_file.read())
            # We seek back to the file beginning to read it again
            model_file.seek(0)

            # We save the keyboard name for future usage
            self.verbose_name = model_file.read()