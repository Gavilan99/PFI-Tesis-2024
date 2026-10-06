from app import create_app

app = create_app()

if __name__ == "__main__":
    # Loopback only, debugger off: the Werkzeug debugger executes code and must never be reachable from the network.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
