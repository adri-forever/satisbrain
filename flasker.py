import flask
from python import htmlreport, brain

app = flask.Flask(__name__)

@app.route('/')
def index():
	return flask.render_template('index.html', landing=htmlreport.landing_page_flask())

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
	
	production_plan: dict
	recipes: dict[str, str]
	production_plan, recipes = brain.get_production_plan(item, brain.data.data_baseresources)	
	
	html = htmlreport.generate_html_flask(production_plan)
	print(production_plan)
	response = {
		"production_plan": production_plan,
		"recipes": recipes,
		"html": html
	}
	return flask.jsonify(response)

if __name__=="__main__":
	print(f"{__file__} is main")

	app.run(host="0.0.0.0", debug=True)