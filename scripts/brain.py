import json, copy, timeit, airium, webbrowser
from typing import Literal

"""
for future: take into account if water is produced somewhere as a byproduct, substract produced to needed amount
"""

### Functions ###
def pretty_dict_print(dict_: dict, deep: bool = True, level: int = 0):
    indent = level*'\t'
    for key, value in dict_.items():
        if isinstance(value, dict) and deep:
            print(indent+f'{key} :')
            pretty_dict_print(value, deep=True, level=level+1)
        else:
            print(f'{indent+key} : {value}')
    
def build_item_to_recipes(alternates: bool = True) -> dict:
    data_itemtorecipes = {}
    
    for item_k in data_items:
        data_itemtorecipes[item_k] = []
        
        for recipe_k, recipe_v in data_recipes.items():
            products = recipe_v['products']
            for product in products:
                # Append recipe if:
                # recipe produces selected item
                # and
                # recipe is default, unless we asked for
                if product['item']==item_k and (not recipe_v['alternate'] or alternates):
                    data_itemtorecipes[item_k].append(recipe_k)
    
    return data_itemtorecipes

def build_baseresources() -> set[str]:
    """
    Make set of items that are not produced by a crafting recipe
    
    Include water even though it is a byproduct of many recipes
    
    Includes things like radioactive waste because its not crafted but byproduct of generator. whatever
    """
    data_baseresources = {item for item, recipes in data_itemtodefaultrecipes.items() if not recipes}
    data_baseresources.add('Desc_Water_C')
    
    return data_baseresources

def get_details(key, datatype: Literal['recipes', 'items', 'schematics',
                                         'generators', 'resources', 'miners',
                                         'buildings'] = None) -> dict:
    """
    kinda useless? if you know the datatype just use the according dict
    unless the datatype is a variable
    """
    if datatype:
        return data[datatype][key]
    else:
        for datatype in data:
            if key in data[datatype]:
                return data[datatype][key]

def exact_search(name: str, dtypes: list[str]) -> list[tuple[str]]:
    results = []
    for dtype in dtypes:
        for itemkey, item in data[dtype].items():
            for value in item.values():
                if isinstance(value, str):
                    if name.lower() == value.lower():
                        results.append((dtype, itemkey))
    return results

def inexact_search(name: str, dtypes: list[str]) -> list[tuple[str]]:
    """
    Inexact search rules:
        It is possible to specify several items with chosen delimiters (space and comma?)
        as to allow typing "iron ingot" to find the item with slug "iron ingot"

    Args:
        name (str): _description_
        dtypes (list[str]): _description_

    Returns:
        _type_: _description_
    """
    results_inex: list[tuple] = []
    
    #Delimiters
    inex_delimiters = [' ', ',']
    base_delimiter = inex_delimiters[0]
    for i, delimiter in enumerate(inex_delimiters):
        if i!=0:
            name_inex = name.replace(delimiter, base_delimiter)
    name_parts = name_inex.split(base_delimiter)

    #Search process
    for dtype in dtypes:
        for itemkey, item in data[dtype].items():
            addresult = False
            partialresult = True
            
            #partialresult will only stay True if all given parts are in item name (slug or display name)
            for value in item.values():
                if isinstance(value, str):
                    addresult |= name.lower() in value.lower()
                    
                    
                    p2result = True
                    for part in name_parts:
                        p2result &= part.lower() in value.lower() 
                partialresult &= p2result
            
            #Add result if name is contained in item name or if all parts correspond
            if name in item.values() or partialresult:
                results_inex.append((dtype, itemkey))
    
    return results_inex    
    
def search_object(name: str, datatype: Literal['recipes', 'items', 'schematics',
                                         'generators', 'resources', 'miners',
                                         'buildings'] = None, exact: bool = False) -> tuple[list[tuple[str]]]:
    '''
    Here item does not refer to an actual in-game item you can hold in your inventory,
    but an item of the database
    Search for an item(item)/recipe/etc by name or slug
    
    '''
    # Type filter
    dtypes = data.keys()
    if datatype:
        dtypes = [datatype]

    # Exact search    
    results_ex = exact_search(name, dtypes)
    
    # Inexact search
    results_inex = []
    if not exact:
        results_inex = inexact_search(name, dtypes)
    
    #Filter out exact result from inexact result
    results_inex = [res for res in results_inex if res not in results_ex]
    
    return results_ex, results_inex

def general_lookup(slug: str):
    pass

def get_recipe_ingredients(recipe: str) -> dict:
    return data_recipes[recipe]['ingredients']

def get_child_items(item: str, alternates: list[str] = [], deep: bool = True, parent_recipes: set[str] = set()) -> tuple[set[str]]:
    """
    """ 
    #Get all possible recipes for item
    recipes = data_itemtorecipes[item]
    
    #Force absence of recipes in case of base resource
    #Useful for forced base resources like water
    if item in data_baseresources:
        recipes = []
    
    #Filter out recipes that are projected to be used higher in the chain to prevent looping
    recipes = [rec for rec in recipes
               if rec not in parent_recipes # prevent looping
               and data_recipes[rec]['producedIn'] # cant compute whats not in a machine
               and(
                   not data_recipes[rec]['alternate'] # keep defaults
                   or rec in alternates # and selected alternates
                   )
              ]
    
    #Select desired recipe
    # use default, but if an alternate is given use it and immediately break out of loop
    # unless its the only available recipe, do not use packager recipes
    recipe = ''
    for _recipe in recipes:
        if data_recipes[_recipe]['producedIn'][0]=='Desc_Packager_C' and len(recipes)>1:
            continue 
        if not data_recipes[_recipe]['alternate']:
            recipe = _recipe
        if _recipe in alternates:
            recipe = _recipe
            break
    
    #Add selected recipe to chain of parent recipes
    if recipe:
        parent_recipes.add(recipe)
    # else:
    #     print(f'{item} has no more available recipes')
    
    #Get ingredients from recipe
    children = set()
    if recipe in data_recipes:
        for child in data_recipes[recipe]['ingredients']:
            children |= {child['item']}
    
    #Recursively search children (unless explicitly asked not to with deep=False)
    subchildren = set()
    if deep:
        for child in children:
            tempsubchildren, subrecipes = get_child_items(child, alternates=alternates, parent_recipes=parent_recipes)
            subchildren |= tempsubchildren
            parent_recipes |= subrecipes
    
    children |= subchildren
    
    return children, parent_recipes

def get_production_plan(item: str, qty: float, recipes: list[str]):
    # Contains steps
    production_plan = {}
    
    recipe = [rec for rec in recipes if rec in data_itemtorecipes[item]][0]
    item_to_recipe = {item: recipe}
    recipe_data = data_recipes[recipe]
    if qty <= 0:
        print('Cannot produce negative amount of items. Creating plan for singular machine')
        qty = 60 * recipe_data['products'][0]['amount'] / recipe_data['time'] # /min
    
    # For calculation
    itempool = {item: qty}
    
    for i in range(MAX_ITER): #change to while once we got the condition
        #Make room for current tier
        tiername = f'tier{i}'
        production_plan[tiername] = {}
        
        #List all items to produce in said tier
        left_items = [item for item, iqty in itempool.items() if iqty>0 and item not in data_baseresources]
        if not left_items:
            break # if no items are left to craft, exit loop
        
        for item in left_items:
            recipe = [rec for rec in data_itemtorecipes[item] if rec in recipes][0]
            recipe_data = data_recipes[recipe]
            
            # decide number of machines for recipe: divide asked quantity by recipe rate (/min)
            machine_qty = itempool[item] / (60 * recipe_data['products'][0]['amount'] / recipe_data['time'])
            
            production_plan[tiername][recipe] = machine_qty
            for product in recipe_data['products']:
                product_item = product['item']
                product_qty = 60 * machine_qty * product['amount'] / recipe_data['time']
                
                if product_item not in itempool:
                    itempool[product_item] = 0
                itempool[product_item] -= product_qty

            for ingredient in recipe_data['ingredients']:
                ingr_item = ingredient['item']
                ingr_qty = 60 * machine_qty * ingredient['amount'] / recipe_data['time']
                
                if ingr_item not in itempool:
                    itempool[ingr_item] = 0
                itempool[ingr_item] += ingr_qty
    
        # print('Item pool:')
        # print(itempool)
        # print('Production plan:')
        # print(production_plan[tiername])
    
    # Refine plan
    #Downwards: concatenate recipes that appear several time to lowest tier
    for recipe in recipes:
        lowest_tier = ''
        tiers = []
        total = 0
        for tier, plan in production_plan.items():
            if recipe in plan:
                lowest_tier = tier
                tiers.append(tier)
                total = plan[recipe]
        
        for tier in tiers:
            production_plan[tier].pop(recipe)
        production_plan[lowest_tier][recipe] = total
    
    #Final cleanup: remove empty tiers
    topop = []
    for tier, plan in production_plan.items():
        if not plan:
            topop.append(tier)
    for tier in topop:
        production_plan.pop(tier)
    
    base_resources = {item: value for item, value in itempool.items() if value>0}
    production_plan['base_resources'] = base_resources
    
    return production_plan

def generate_recipe(a: airium.Airium, recipe_data: dict, qty: int):
    
    products = recipe_data['products']
    ingredients = recipe_data['ingredients']
    
    machine = data_buildings[recipe_data['producedIn'][0]]['name']
    
    with a.table():
        with a.tr():
            a.th(_t='')
            a.th(_t='Rate (/min)')
            a.th(_t='Total (/min)')
            a.th(_t='')
            a.th(_t='Produced in')
            a.th(_t='Amount')
        with a.tr():
            a.th(_t='Products')
        for i, product in enumerate(products):
            with a.tr():
                prd_name = data_items[product['item']]['name']
                rate = 60 * product['amount'] / recipe_data['time']
                a.td(_t=prd_name)
                a.td(_t=rate)
                a.td(_t=qty * rate, klass='high')
                if i==0:
                    a.td(_t='')
                    a.td(_t=machine)
                    a.td(_t=qty)
        with a.tr():
            a.th(_t='Ingredients')
        for i, ingredient in enumerate(ingredients):
            with a.tr():
                ingr_name = data_items[ingredient['item']]['name']
                rate = 60 * ingredient['amount'] / recipe_data['time']
                a.td(_t=ingr_name)
                a.td(_t=rate)
                a.td(_t=qty * rate, klass='high')      

def generate_tier(a: airium.Airium, tierno: int, tier: dict):
    a.button(type='button', klass='collapsible', _t=f'Stage {tierno}')
    with a.div(klass='content'):
        for recipe in tier:
            recipe_data = data_recipes[recipe]
            with a.button(type='button', klass='collapsible'):
                a(recipe_data['name'])
            with a.div(klass='content'):
                generate_recipe(a, recipe_data, tier[recipe])

def generate_resources(a: airium.Airium, resources: dict):
    # with a.button(type='button', klass='collapsible'):
    #     a('Resources')
    a.h2(_t='Resources')
    with a.p(klass='content'):
        with a.table():
            with a.tr():
                a.th(_t='Resource')
                a.th(_t='Total (/min)')
            for resource, qty in resources.items():
                res_name = data_items[resource]['name']
                with a.tr():
                    a.td(_t=res_name)
                    a.td(_t=qty)

def generate_html(production_plan: dict, path: str):
    a = airium.Airium()
    
    key = list(production_plan[list(production_plan.keys())[0]].keys())[0]
    base_recipe = data_recipes[key]
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
                    generate_recipe(a, base_recipe, production_plan[tier][key])
                elif 'tier' in tier:
                    generate_tier(a, i, production_plan[tier])
                else:
                    generate_resources(a, production_plan[tier])
        with a.script():
            a(script)
    
    html = str(a).encode('utf-8')
    with open(path, 'wb') as f:
        f.write(html)

### Script code ###
try:
    #Load data
    with open('resource\\data.json') as f:
        data = json.load(f)
except FileNotFoundError:
    print('Could not find data file. Program will not work')
    exit()

#Decompose big dict
data_recipes = data['recipes']
data_items = data['items']
data_schematics = data['schematics']
data_generators = data['generators']
data_resources = data['resources']
data_miners = data['miners']
data_buildings = data['buildings']

#Generate item to recipes
data_itemtorecipes = build_item_to_recipes()
data_itemtodefaultrecipes = build_item_to_recipes(alternates=False)

#Generate base resources
data_baseresources = build_baseresources()

# Prevent infinite looping
MAX_ITER = 1000

# Web shit
style = """body {
	background-color: #333;
}

h1, h2 {
	color: white;
	font-family: "Segoe UI", sans-serif;
}

table {
	padding: 5px 0 5px;
}

td, th {
	padding: 1px 5px;
	font-size: 16px;
	font-family: "Segoe UI", sans-serif;
	color: white;
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

.collapsible:hover {
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

script = """var coll = document.getElementsByClassName("collapsible");
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
}"""

### Main code ###
if __name__=='__main__':
    #investigate why fuel does not work
    
    exact, inexact = search_object('uranium fuel rod', 'items')
    print('Exact: ', exact)
    if exact:
        item = exact[0][1]
    else:
        print('No corresponding item found. Exiting')
        quit()
    children, recipes = get_child_items(item)
    print('Child items: ', children)
    print('Child recipes: ', recipes)
    
    qty = 10
    production_plan = get_production_plan(item, qty, recipes)
    print('\t--- PRODUCTION PLAN ---')
    pretty_dict_print(production_plan)
    
    path = 'output\\test.html'
    generate_html(production_plan, path)
    
    webbrowser.open(path)
    
    print('Travail terminé !')