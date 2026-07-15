Elevator Saga
===================
The elevator programming game

[Play it now!](http://play.elevatorsaga.com/)

Or [Run the unit tests](http://play.elevatorsaga.com/test/)

For developers/contributors: This project is not actively maintained. The repo is used to serve github pages so I would like to keep it as is. Feel free to fork and host your own versions of Elevator Saga! But I would like to keep the domain name with the original version of the game.

![Image of Elevator Saga in browser](https://raw.githubusercontent.com/magwo/elevatorsaga/master/images/screenshot.png)

Python NiceGUI visualization
----------------------------

The Python-first interface visualizes both Python and Java strategies. It records simulation snapshots and replays elevators and passengers in the browser with Python-controlled NiceGUI elements.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-nicegui.txt
.venv/bin/python nicegui_app.py --port 8082
```

Open <http://127.0.0.1:8082/>. Python is the default language; Java visualization requires JDK 11 or newer. The interface includes challenge and language selection, strategy editing, play/pause, replay speed, progress, and live replay statistics.

Local multi-language mode
-------------------------

The local development server uses Python as the default strategy language and provides a language selector:

- Python is selected by default and runs headlessly through the Python port.
- JavaScript remains available with the original browser visualization.
- Java runs headlessly through the Java port and requires JDK 11 or newer.

Start the server from the repository root:

```bash
python3 multilang_server.py --port 8001
```

Then open <http://127.0.0.1:8001/index.html>. Python and Java strategies are arbitrary local programs and run with your user permissions; only execute code you trust.
