import flask, json
from python import htmlreport, brain

DEBUG = True

app = flask.Flask(__name__)

def fill_dictionary(baseresource: set):
    dictionary = {"items": {item: brain.data.data_items[item][0]["name"] for item in baseresource}}

    return dictionary

@app.route('/')
def index():
    return flask.render_template('index.html', landing=htmlreport.generate_html_flask([]))

@app.route('/send', methods=['POST'])
def send():
    payload = flask.request.get_json()

    if DEBUG:
        print("\n---- RECEIVED POST ----")
        print(json.dumps(payload))

    item: str
    baseresource: set[str]
    recipes: dict[str, str] = {}
    if 'item' in payload:
        item = payload['item']
    else:
        raise Exception("No item in request payload.")
    if 'recipes' in payload:
        recipes = payload['recipes']
    if 'baseresource' in payload:
        baseresource = set(payload['baseresource'])
    else:
        baseresource = brain.data.data_baseresources

    production_plan: dict
    production_plan, recipes, baseresource = brain.get_production_plan(item, baseresource, recipes, 1)
    
    dictionary = fill_dictionary(baseresource)

    if DEBUG:
        print("\n\tOutput plan: ")
        print(production_plan)

    # this is where the render of the plan happens
    html = htmlreport.generate_html_flask(production_plan)
    response = {
        "production_plan": production_plan,
        "recipes": recipes,
        "baseresource": list(baseresource),
        "html": html,
        "dictionary": dictionary
    }
    return flask.jsonify(response)


if __name__ == "__main__":
    print(f"{__file__} is main")

    app.run(host="0.0.0.0", debug=DEBUG, port=8080)
