import flask
import json
from pathlib import Path as pPath
from os import path as ospath
from python import htmlreport, brain

DEBUG = False

app = flask.Flask(__name__)


def fillDictionary(baseresource: set):
    dictionary = {"items": {
        item: brain.data.data_items[item][0]["name"] for item in baseresource}}

    return dictionary


@app.route('/')
def index():
    # return flask.render_template('index.html', landing=htmlreport.generate_html_flask([]))
    return flask.render_template('index.html', landing=htmlreport.generateHtmlFlask())


@app.route('/send', methods=['POST'])
def send():
    payload = flask.request.get_json()

    if DEBUG:
        print("\n---- RECEIVED POST ----")
        print(json.dumps(payload))

    target: dict[str, float]
    baseresource: set[str]
    recipes: dict[str, str] = {}
    if 'target' in payload:
        target = payload['target']
    else:
        raise Exception("No target in request payload.")
    if 'baseresource' in payload:
        baseresource = set(payload['baseresource'])
    else:
        baseresource = brain.data.data_baseresources
    if 'recipes' in payload:
        recipes = payload['recipes']

    productionPlan: dict

    graph = brain.Graph(
        target=target, baseresource=baseresource, recipes=recipes)
    graph.compute()
    productionPlan = graph.flatten()

    if DEBUG:
        print("\n\tOutput plan: ")
        print(productionPlan)

    productionPlan['dictionary'] = fillDictionary(graph.baseresource)

    # this is where the render of the plan happens
    productionPlan['html'] = htmlreport.generateHtmlFlask(graph)
    return flask.jsonify(productionPlan)


if __name__ == "__main__":
    settingpath = pPath(__file__).parent / "settings.json"
    if ospath.exists(settingpath):
        with open(settingpath, 'r') as f:
            settings = json.load(f)
    else:
        defaultpath = pPath(__file__).parent / "defaultsettings.json"
        settings = {"DEBUG": False}
        if ospath.exists(defaultpath):
            with open(defaultpath, 'r') as f:
                settings = json.load(f)
        with open(settingpath, "w") as f:
            json.dump(settings, f, indent=4)
    if 'DEBUG' in settings:
        DEBUG = settings["DEBUG"]

    if DEBUG:
        print(f"{__file__} is main")
        brain.DEBUG = True

    app.run(host="0.0.0.0", debug=DEBUG, port=8080)
