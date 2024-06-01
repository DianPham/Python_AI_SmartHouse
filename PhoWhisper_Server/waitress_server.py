import logging
from waitress import serve
from init_server import app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve(app, host='0.0.0.0', port=5000, threads = 2)