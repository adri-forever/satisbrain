import airium, uuid, copy, math
from typing import Literal

# personal imports
import data

# Constants
DIGITS = 3

def generate_recipe(a: airium.Airium, recipe_data: dict, qty: int):
    
    qty = round(qty, DIGITS)
    
    products = recipe_data['products']
    ingredients = recipe_data['ingredients']
    
    machine = data.data_buildings[recipe_data['producedIn'][0]][0]['name']
    
    # Indicate with class that the table colors can be altered by the checkbox state
    with a.table(klass='checkbox_altered'):
        with a.tr():
            a.td(_t='')
            a.th(_t='Rate (/min)')
            a.th(_t='Total (/min)')
            a.th(_t='Produced in')
            a.th(_t='Amount')
        with a.tr():
            a.th(_t='Products')
        for i, product in enumerate(products):
            with a.tr():
                prd_name = data.data_items[product['item']][0]['name']
                rate = 60 * product['amount'] / recipe_data['duration']
                
                qrate = round(qty * rate, DIGITS)
                rate = round(rate, DIGITS)
                
                a.td(_t=prd_name)
                a.td(_t='{:g}'.format(rate))
                a.td(_t='{:g}'.format(qrate), klass='high')
                if i==0:
                    a.td(_t=machine)
                    a.td(_t='{:g}'.format(qty))
        with a.tr():
            a.th(_t='Ingredients')
        for i, ingredient in enumerate(ingredients):
            with a.tr():
                ingr_name = data.data_items[ingredient['item']][0]['name']
                rate = 60 * ingredient['amount'] / recipe_data['duration']
                
                qrate = round(qty * rate, DIGITS)
                rate = round(rate, DIGITS)
                
                a.td(_t=ingr_name)
                a.td(_t='{:g}'.format(rate))
                a.td(_t='{:g}'.format(qrate), klass='high') 

def get_recipe_title(recipe_data: dict) -> str:
    return f'{recipe_data['name']}{' (alternate)' if recipe_data['alternate'] else ''}'

def generate_tier(a: airium.Airium, tierno: int, tier: dict):
    """
    add recipe name in tab and if alternate or not
    """
    a.button(type='button', klass='collapsible', _t=f'Stage {tierno}')
    with a.div(klass='content'):
        if 'recipepool' in tier:
            with a.div(klass='tiercontainer'):
                for recipe in tier['recipepool']:
                    recipe_data = data.data_recipes[recipe][0]
                    with a.div(klass='tierbox'):
                        # Custom checkbox
                        with a.label(klass='recipe_checkbox'):
                            a.input(type='checkbox', id=uuid.uuid1()) #Generate UUID for each checkbox (localStorage state)
                            a.span(klass='checkmark')
                            a.h3(_t=get_recipe_title(recipe_data))
                        generate_recipe(a, recipe_data, tier['recipepool'][recipe])
        
def generate_resources(a: airium.Airium, resources: dict, fltr: Literal['positive', 'negative', 'all'] = 'all'):
    # Prevent modification outside
    pool = copy.deepcopy(resources)

    # Remove 0 (according to precision) and filter according to fltr
    topop = []
    for resource, qty in pool.items():
        pool[resource] = round(qty, DIGITS)
        condition = ((not pool[resource])
            or (fltr=='positive' and pool[resource]<10**(-DIGITS))
            or (fltr=='negative' and -pool[resource]<10**(-DIGITS))
            )
                        
        if condition:
            topop.append(resource)
            
    for resource in topop:
        pool.pop(resource)
    
    if pool:
        with a.table():
            with a.tr():
                a.th(_t='Resource')
                a.th(_t='Total (/min)')
            for resource, qty in pool.items():
                qty = round(qty, DIGITS)
                res_name = data.data_items[resource][0]['name']
                with a.tr():
                    a.td(_t=res_name)
                    a.td(_t='{:g}'.format(abs(qty)))
    else:
        a.h3(_t='No leftover !', klass='high')

def generate_machines(a: airium.Airium, production_plan: dict):
    machines = {}
    for tier in production_plan.values():
        if 'recipepool' in tier:
            for recipe, qty in tier['recipepool'].items():
                recipe_data = data.data_recipes[recipe][0]
                machine = recipe_data['producedIn'][0]
                if machine not in machines:
                    machines[machine] = 0
                machines[machine] += math.ceil(qty)
    
    totalpower = 0
    if machines:
        with a.table():
            with a.tr():
                a.th(_t='Machine')
                a.th(_t='Quantity')
                a.th(_t='Estimated power (MW)')
            for machine, qty in machines.items():
                machine_data = data.data_buildings[machine][0]
                name = machine_data['name']
                power = round(qty * machine_data['powerUsage'], DIGITS)
                totalpower += power
                qty = round(qty, DIGITS)
                with a.tr():
                    a.td(_t=name)
                    a.td(_t='{:g}'.format(qty))
                    a.td(_t='{:g}'.format(power))
            with a.tr():
                a.td(_t='Total')
                a.td(_t='')
                a.td(_t='{:g}'.format(totalpower))
    a.p(_t='Resource extraction ignored. Variable power buildings not computed')

def generate_html(production_plan: dict, path: str):
    """
    watch out for variable power consumption machines
    """
    a = airium.Airium()
    
    tierlist = list(production_plan.keys()) # tier list, lol
    target_item = list(production_plan[tierlist[0]]['itempool'].keys())[0]
    target_recipe = list(production_plan[tierlist[1]]['recipepool'].keys())[0]
    target_quantity = production_plan[tierlist[0]]['itempool'][target_item]
    target_quantity = '{:g}'.format(round(target_quantity, DIGITS))
    
    item_name = data.data_items[target_item][0]['name']
    
    a('<!DOCTYPE html>')
    with a.html(lang='en'):
        with a.head():
            a.meta(content='width=device-width, initial-scale=1', name='viewport', charset='utf-8')
            a.title(_t=f'Satisbrain: {item_name}')
            with a.style():
                a(style)
        with a.body():
            a.h1(_t=f'Production plan: {target_quantity} {item_name} per min')
            with a.div(klass='row'):
                with a.div(klass='column'):
                    a.h2(_t=f'Recipe: {get_recipe_title(data.data_recipes[target_recipe][0])}')
                    generate_recipe(a, data.data_recipes[target_recipe][0], production_plan[tierlist[1]]['recipepool'][target_recipe])
                with a.div(klass='column'):
                    a.h2(_t='Input')
                    generate_resources(a, production_plan[tierlist[-1]]['itempool'], 'positive')
            with a.div(klass='row'):
                with a.div(klass='column'):
                    a.h2(_t='Machines & power')
                    generate_machines(a, production_plan)
                with a.div(klass='column'):
                    a.h2(_t='Extra resources')
                    generate_resources(a, production_plan[tierlist[-1]]['itempool'], 'negative')
            a.h2(_t='Production steps')
            a.button(type='button', klass='expndall', _t='Expand/Collapse all')
            for i in range(0, len(tierlist)-2):
                # Offset by 2 because first tier only has target item and second only has target recipe
                generate_tier(a, i+1, production_plan[tierlist[i+2]])
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