# ckb-water-vapor
A small project to try out the ckb-daemon on linux, it might work on macOS, but I make `fib(0)` guarantees.
I only have a Corsair K70 RGB, and I only test on linux, so if you don't match both those things, I, once again, make `fib(0)` guarantees.
(oh, and the water vapour thing is a cloud :wink:)

## Documentation
You want to know how to use the code?
OK! Here's some info about what files do what :smile:
(I'm probably going to use some incorrect python lingo, but it should be barely understandable atleast)

### `keyboard.py`
There are two classes here, one that interacts with ckb-daemon, and one that provides the API when using falcon.


#### `Keyboard`
This class stores information about and handles communication with the ckb-daemon about a keyboard. To use it, use it with a `with`-statement, as it needs to be initialised and closed. It has various methods that do various things, and they may change drastically, so read the code to find out how to use them and what they do.


#### `Keyboard_Falcon_Api`
This class is used as a "Resource" for [falcon](https://falconframework.org/), and is the file that actually implements the API. If you want to add something to the API, do it here :smile:.


### `__init__.py`
This file is simply a script that makes the keyboard breathe red with the arrow and wasd keys breathing white. This may change, and is used to test the daemon interaction.


### `falcon_main.py`
This file is what serves the API via falcon and `wsgiref.simple_server`. Run this if you want to open the API to your keyboard. Note that the API uses port 42069, so you need to open that port if you want anyone on the internet to control your RGB keyboard.


### `basic_client.py`
This file is a uses the API to communicate with a `falcon_main.py` anywhere on the internet. When you run this you will be prompted for the IP or url of the API server (the computer that's running `falcon_main`). After you've put the URL you can input text that (via the API) will light up the corresponding keys on the server keyboard in sequence. There are a couple of commands that can be used by inputting them like regular text.

|Command|Description|
|---|---|
|`_clear`|Sets the whole server keyboard to black (0, 0, 0)|
|`_exit`|Exits the basic client, note that this does not affect the server in any way as there is no "connection" to the server, only requests|
|`_act_time <seconds>`|Sets the number of seconds each key in the sequence should take to light up.|


### `code_config.json`
This file stores info that the `keyboard.Keyboard` class needs. It currently only stores a list of supported keyboards, if your's isn't on the list, the `keyboard.Keyboard` class won't accept your keyboard. You can add your own keyboard to it, but I make `fib(0)` guarantees that it will work as expected.

