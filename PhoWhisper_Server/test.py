from flask import Flask

app = Flask(__name__)

@app.before_first_request
def load_resources():
    print("Resources are being loaded...")

@app.route('/')
def home():
    return "Home Page"

if __name__ == "__main__":
    app.run(debug=True)