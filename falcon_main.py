from wsgiref import simple_server

import falcon

import keyboard

# The falcon api instance
app = falcon.API()

# The api instance to handle requests for the keyboard
keyboard_api = keyboard.Keyboard_Falcon_Api(keyboard.Keyboard())

# We direct /keyboard to the keyboard object
app.add_route("/keyboard", keyboard_api)

if __name__ == "__main__":
    httpd = simple_server.make_server("127.0.0.1", 42069, app)
    httpd.serve_forever()

    keyboard_api.keyboard.__exit__()