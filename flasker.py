import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return flask.render_template('index.html')

if __name__=="__main__":
    print(f"{__file__} is main")

    app.run(host="0.0.0.0")