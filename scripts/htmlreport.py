import airium

# personal imports
import data

# Constants
DIGITS = 3

def generate_recipe(a: airium.Airium, recipe_data: dict, qty: int):
    
    products = recipe_data['products']
    ingredients = recipe_data['ingredients']
    
    machine = data.data_buildings[recipe_data['producedIn'][0]]['name']
    
    with a.table():
        with a.tr():
            a.td(_t='')
            a.th(_t='Rate (/min)')
            a.th(_t='Total (/min)')
            a.th(_t='')
            a.th(_t='Produced in')
            a.th(_t='Amount')
        with a.tr():
            a.th(_t='Products')
        for i, product in enumerate(products):
            with a.tr():
                prd_name = data.data_items[product['item']]['name']
                rate = 60 * product['amount'] / recipe_data['time']
                
                qrate = round(qty * rate, DIGITS)
                rate = round(rate, DIGITS)
                
                a.td(_t=prd_name)
                a.td(_t='{:g}'.format(rate))
                a.td(_t='{:g}'.format(qrate), klass='high')
                if i==0:
                    a.td(_t='')
                    a.td(_t=machine)
                    a.td(_t='{:g}'.format(qty))
        with a.tr():
            a.th(_t='Ingredients')
        for i, ingredient in enumerate(ingredients):
            with a.tr():
                ingr_name = data.data_items[ingredient['item']]['name']
                rate = 60 * ingredient['amount'] / recipe_data['time']
                
                qrate = round(qty * rate, DIGITS)
                rate = round(rate, DIGITS)
                
                a.td(_t=ingr_name)
                a.td(_t='{:g}'.format(rate))
                a.td(_t='{:g}'.format(qrate), klass='high') 

def generate_tier(a: airium.Airium, tierno: int, tier: dict):
    a.button(type='button', klass='collapsible', _t=f'Stage {tierno}')
    with a.div(klass='content'):
        for recipe in tier:
            recipe_data = data.data_recipes[recipe]
            with a.button(type='button', klass='collapsible'):
                a(recipe_data['name'])
            with a.div(klass='content'):
                generate_recipe(a, recipe_data, tier[recipe])

def generate_resources(a: airium.Airium, resources: dict):
    #Clean low numbers
    topop = []
    for resource, qty in resources.items():
        resources[resource] = round(qty, DIGITS)
        if not resources[resource]:
            topop.append(resource)
    for resource in topop:
        resources.pop(resource)
    
    if resources:
        with a.table():
            with a.tr():
                a.th(_t='Resource')
                a.th(_t='Total (/min)')
            for resource, qty in resources.items():
                res_name = data.data_items[resource]['name']
                with a.tr():
                    a.td(_t=res_name)
                    a.td(_t='{:g}'.format(qty))
    else:
        a.h3(_t='No leftover !', klass='high')

def generate_html(production_plan: dict, path: str):
    a = airium.Airium()
    
    key = list(production_plan[list(production_plan.keys())[0]].keys())[0]
    base_recipe = data.data_recipes[key]
    recipe_name = base_recipe['name']
    
    a('<!DOCTYPE html>')
    with a.html(lang='en'):
        with a.head():
            a.meta(content='width=device-width, initial-scale=1', name='viewport', charset='utf-8')
            a.title(_t=f'Satisbrain: {recipe_name}')
            with a.style():
                a(style)
        with a.body():
            a.h1(_t=f'Production plan: {recipe_name}')
            for i, tier in enumerate(production_plan):
                if i==0:
                    with a.div(klass='row'):
                        with a.div(klass='column'):
                            a.h2(_t='Recipe')
                            generate_recipe(a, base_recipe, production_plan[tier][key])
                        with a.div(klass='column'):
                            a.h2(_t='Base resources')
                            generate_resources(a, production_plan['base_resources'])
                        with a.div(klass='column'):
                            a.h2(_t='Extra resources')
                            generate_resources(a, production_plan['extra_resources'])
                    a.button(type='button', klass='expndall', _t='Expand/Collapse all')
                elif 'tier' in tier:
                    generate_tier(a, i, production_plan[tier])
        with a.script():
            a(script)
    
    html = str(a).encode('utf-8')
    with open(path, 'wb') as f:
        f.write(html)

style = """body {
	background-color: #333;
}

h1, h2, h3 {
	color: white;
	font-family: "Segoe UI", sans-serif;
}

table {
	padding: 5px 0 5px;
}

table, th {
    border: 1px dashed #444;
}

td, th {
	padding: 1px 5px;
	font-size: 16px;
	color: white;
	font-family: "Segoe UI", sans-serif;
}

.column {
  float: left;
  padding: 5px 40px;
}

/* Clear floats after the columns */
.row:after {
  content: "";
  display: table;
  clear: both;
}

.expndall {
	background-color: #555;
	color: white;
	cursor: pointer;
	padding: 5px 10px;
	border: none;
	text-align: left;
	outline: none;
	font-size: 16px;
	font-family: "Segoe UI", sans-serif;
}

.collapsible {
	background-color: #555;
	color: white;
	cursor: pointer;
	padding: 10px;
	width: 100%;
	border: none;
	text-align: left;
	outline: none;
	font-size: 16px;
	font-family: "Segoe UI", sans-serif;
}

.collapsible:hover, .expndall:hover {
	background-color: #FA9649;
}

.active {
	background-color: #777;
}

.content {
	color: white;
	padding: 0 18px;
	display: none;
	overflow: hidden;
	background-color: #333;
	font-family: "Segoe UI", sans-serif;
}

.high {
	color: #FA9649
}"""

script = """var expnd = document.getElementsByClassName("expndall")[0];
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
        this.classList.toggle("active");
        var content = this.nextElementSibling;
        if (content.style.display === "block") {
            content.style.display = "none";
        } else {
        content.style.display = "block";
        }
    });
}

expnd.addEventListener("click", function() {
    var state = false;
    var style = "block";
    for (i = 0; i < coll.length; i++) {
        state = state || (coll[i].nextElementSibling.style.display==="block");
    }

    if (state) {
        style = "none";
    }

    for (i = 0; i < coll.length; i++) {
        coll[i].nextElementSibling.style.display=style;
    coll[i].classList.toggle("active", !state)
    }
});"""