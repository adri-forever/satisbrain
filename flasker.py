import flask
from python import htmlreport, brain

app = flask.Flask(__name__)

@app.route('/')
def index():
	return flask.render_template('index.html', landing=htmlreport.generate_html_flask([]))

@app.route('/send', methods=['POST'])
def send():
	data = flask.request.get_json()
	
	item: str
	baseresource: set[str]
	recipes: dict[str, str]
	if 'item' in data:
		item = data['item']
	else:
		raise Exception("No item in request data.")
	if 'recipes' in data:
		recipes = data['recipes']
	if 'baseresource' in data:
		baseresource = set(data['baseresource'])
	else:
		baseresource = brain.data.data_baseresources
	
	production_plan: dict
	recipes: dict[str, str]
	production_plan, recipes = brain.get_production_plan(item, baseresource)	
	
	html = htmlreport.generate_html_flask(production_plan) # this is where the render of the plan happens
	print(production_plan)
	response = {
		"production_plan": production_plan,
		"recipes": recipes,
		"baseresource": list(baseresource),
		"html": html
	}
	return flask.jsonify(response)

if __name__=="__main__":
	print(f"{__file__} is main")

	app.run(host="0.0.0.0", debug=True)