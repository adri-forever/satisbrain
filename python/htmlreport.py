from python import data
import airium
import uuid
import copy
import math
import sys
from typing import Literal, Any
from pathlib import Path
from contextlib import contextmanager
import webbrowser
import os

sys.path.append(str(Path(__file__).resolve().parent.parent))

# personal imports

# Constants
DIGITS = 3


def dict_getkey(di: dict[str, Any], val: Any):
    for k, v in di.items():
        if v == val:
            return k
    return None


def generate_recipe(a: airium.Airium, recipe_data: dict[str, Any], qty: int):

    qty = round(qty, DIGITS)

    products = recipe_data['products']
    ingredients = recipe_data['ingredients']

    machine: str = data.data_buildings[recipe_data['producedIn'][0]][0]['name']

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
                if i == 0:
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


def generate_tier_old(a: airium.Airium, tierno: int, tier: dict):
    """
    add recipe name in tab and if alternate or not
    """
    a.button(type='button', klass='collapsible', _t=f'Stage {tierno}')
    with a.div(klass='collapsiblecontent'):
        if 'recipepool' in tier:
            with a.div(klass='tiercontainer'):
                for recipe in tier['recipepool']:
                    recipe_data = data.data_recipes[recipe][0]
                    with a.div(klass='tierbox'):
                        # Custom checkbox
                        with a.label(klass='recipe_checkbox'):
                            # Generate UUID for each checkbox (localStorage state)
                            a.input(type='checkbox', id=str(uuid.uuid1()))
                            a.span(klass='checkmark')
                            a.h3(_t=get_recipe_title(recipe_data))
                        generate_recipe(
                            a, recipe_data, tier['recipepool'][recipe])


def generate_resources(a: airium.Airium, resources: dict, fltr: Literal['positive', 'negative', 'all'] = 'all'):
    # Prevent modification outside
    pool = copy.deepcopy(resources)

    # Remove 0 (according to precision) and filter according to fltr
    topop = []
    for resource, qty in pool.items():
        pool[resource] = round(qty, DIGITS)
        condition = ((not pool[resource])
                     or (fltr == 'positive' and pool[resource] < 10**(-DIGITS))
                     or (fltr == 'negative' and -pool[resource] < 10**(-DIGITS))
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
    for tier in production_plan:
        if 'recipepool' in tier:
            for recipe, qty in tier['recipepool'].items():
                recipe_data = data.data_recipes[recipe][0]
                machine = recipe_data['producedIn'][0]
                if machine not in machines:
                    machines[machine] = 0
                machines[machine] += qty

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

    target_item = list(production_plan[0]['itempool'].keys())[0]
    target_recipe = list(production_plan[1]['recipepool'].keys())[0]
    target_quantity = production_plan[0]['itempool'][target_item]
    target_quantity = '{:g}'.format(round(target_quantity, DIGITS))

    item_name = data.data_items[target_item][0]['name']

    a('<!DOCTYPE html>')
    with a.html(lang='en'):
        with a.head():
            a.meta(content='width=device-width, initial-scale=1',
                   name='viewport', charset='utf-8')
            a.title(_t=f'Satisbrain: {item_name}')
            with a.style():
                a(style)
        with a.body():
            a.h1(_t=f'Production plan: {target_quantity} {item_name} per min')
            with a.div(klass='row'):
                with a.div(klass='column'):
                    a.h2(
                        _t=f'Recipe: {get_recipe_title(data.data_recipes[target_recipe][0])}')
                    generate_recipe(
                        a, data.data_recipes[target_recipe][0], production_plan[1]['recipepool'][target_recipe])
                with a.div(klass='column'):
                    a.h2(_t='Input')
                    generate_resources(
                        a, production_plan[-1]['itempool'], 'positive')
            with a.div(klass='row'):
                with a.div(klass='column'):
                    a.h2(_t='Machines & power')
                    generate_machines(a, production_plan)
                with a.div(klass='column'):
                    a.h2(_t='Extra resources')
                    generate_resources(
                        a, production_plan[-1]['itempool'], 'negative')
            a.h2(_t='Production steps')
            a.button(type='button', klass='expndall', _t='Expand/Collapse all')
            for i in range(0, len(production_plan)-2):
                # Offset by 2 because first tier only has target item and second only has target recipe
                generate_tier_old(a, i+1, production_plan[i+2])
        with a.script():
            a(script)

    html = str(a).encode('utf-8')
    with open(path, 'wb') as f:
        f.write(html)


def generate_box_nocont(a: airium.Airium, boxtype: str = '', item: str = '', recipe: str = '', title: str = '', content: str = '', edit: bool = False, collapsed: bool = False):
    title2: str = ""

    dropdownvalues: dict[str, str] = {"": "--"}

    if boxtype in ["item", "recipe"]:
        if item in data.data_items:
            title = data.data_items[item][0]["name"]
    if boxtype == "item":
        dropdownvalues = {key: value[0]['name']
                          for key, value in data.data_items}
    if boxtype == "recipe":
        title2 = data.data_recipes[recipe][0]["name"]
        dropdownvalues = {key: value[0]['name'] for key,
                          value in data.data_recipes if key in data.data_itemtorecipes[item]}

    # bypass - being an invalid name in python by using kwargs
    with a.div(klass=f"box {boxtype} {"edit" if edit else ""} {"collapsed" if collapsed else ""}", **{"data-item": item}):
        with a.div(klass="header"):
            with a.div(klass="left"):
                a.button(klass="status")
                a.div(klass="title1", _t=title)
                a.div(klass="title2", _t=title2)
                if boxtype in ["item", "recipe"]:
                    with a.div(klass="selector").select(id=uuid.uuid4()):
                        for key, value in dropdownvalues.items():
                            a.option(value=key, _t=value)
            with a.div(klass="right"):
                a.button(klass="validate", onclick="validate(this)")
                a.button(klass="edit", onclick="toggleedit(this)")
                a.button(klass="collapse", onclick="togglecollapse(this)")
        with a.div(klass="content"):
            if isinstance(content, str):
                a.text(content)
            if isinstance(content, dict):
                pass
            else:
                print(
                    f"Could not interpret content of box with title {title}. Type {type(content)}")


def generate_table():
    """
    <table class="checkbox_altered">
      <tbody><tr>
        <td></td>
        <th>Rate (/min)</th>
        <th>Total (/min)</th>
        <th>Produced in</th>
        <th>Amount</th>
      </tr>
      <tr>
        <th>Products</th>
      </tr>
      <tr>
        <td>Aluminum Ingot</td>
        <td>60</td>
        <td class="high">1.02</td>
        <td>Foundry</td>
        <td>0.017</td>
      </tr>
      <tr>
        <th>Ingredients</th>
      </tr>
      <tr>
        <td>Aluminum Scrap</td>
        <td>90</td>
        <td class="high">1.53</td>
      </tr>
      <tr>
        <td>Silica</td>
        <td>75</td>
        <td class="high">1.275</td>
      </tr>
    </tbody></table>
    """
    """
    passer une matrice de données à afficher
    passer une recette génère le tableau
    """

    pass


@contextmanager
def generate_box(a: airium.Airium, boxtype: str = '', item: str = '', recipe: str = '', title: str = '', edit: bool = False, collapsed: bool = False, qty: float = 1):
    title2: str = ""

    dropdownvalues: dict[str, str] = {"": "--"}

    if boxtype in ["item", "recipe"]:
        if item in data.data_items:
            title = data.data_items[item][0]["name"]
    if boxtype == "item":
        dropdownvalues = {key: value[0]['name']
                          for key, value in data.data_items.items()}
    if boxtype == "recipe":
        title2 = data.data_recipes[recipe][0]["name"]
        dropdownvalues = {key: value[0]['name'] for key, value in data.data_recipes.items(
        ) if key in data.data_itemtorecipes[item]}
        dropdownvalues['baseresource'] = 'Set as base resource'

    # bypass - being an invalid name in python by using kwargs
    with a.div(klass=f"box {boxtype} {"edit" if edit else ""} {"collapsed" if collapsed else ""}", **{"data-item": item}):
        with a.div(klass="header"):
            with a.div(klass="left"):
                a.button(klass="status")
                a.div(klass="title1", _t=title)
                a.div(klass="title2", _t=title2)
                if boxtype in ["item", "recipe"]:
                    with a.div(klass="selector").select(id=uuid.uuid4()):
                        for key, value in dropdownvalues.items():
                            selection = {}
                            if (boxtype == "item" and key == item) or (boxtype == "recipe" and key == recipe):
                                selection["selected"] = "selected"
                            a.option(_t=value, value=key, **selection)
            with a.div(klass="right"):
                a.button(klass="validate", onclick="validate(this)")
                a.button(klass="edit", onclick="toggleedit(this)")
                a.button(klass="collapse", onclick="togglecollapse(this)")
        with a.div(klass="content"):
            if (boxtype == "item" and item in data.data_items):
                a.div(klass="itemdesc",
                      _t=data.data_items[item][0]['description'])
            if (boxtype == "recipe" and recipe in data.data_recipes):
                recipe_data = data.data_recipes[recipe][0]
                generate_recipe(a, recipe_data, qty)
            yield


def generate_tier(a: airium.Airium, tier: dict, tierno: int) -> airium.Airium:
    with generate_box(a, 'tier', '', '', f'Stage {tierno}', False, False):
        if 'recipepool' in tier:
            for recipe in tier['recipepool']:
                item = dict_getkey(tier['itemtorec'], recipe)
                with generate_box(a, 'recipe', item, recipe, '', True, False, tier['recipepool'][recipe]):
                    pass
    return a


def generate_html_flask(production_plan: list[dict] = []) -> str:
    a = airium.Airium()

    target_item = ''
    if len(production_plan) > 0:
        target_item = list(production_plan[0]['itempool'].keys())[0]
    # target_recipe = list(production_plan[1]['recipepool'].keys())[0]
    # target_quantity = production_plan[0]['itempool'][target_item]
    # target_quantity = '{:g}'.format(round(target_quantity, DIGITS))

    # item_name = data.data_items[target_item][0]['name']

    with generate_box(a, '', '', '', 'Configuration'):
        with generate_box(a, 'item', target_item, '', '', True, False):
            pass
        # base resource hander
        # quantity handler

    with generate_box(a, '', '', '', 'Information'):
        # base resource
        # machines
        # extra resource
        pass

    # with a.div(klass='row'):
    # 	with a.div(klass='column'):
    # 		a.h2(_t=f'Recipe: {get_recipe_title(data.data_recipes[target_recipe][0])}')
    # 		generate_recipe(a, data.data_recipes[target_recipe][0], production_plan[1]['recipepool'][target_recipe])
    # 	with a.div(klass='column'):
    # 		a.h2(_t='Input')
    # 		generate_resources(a, production_plan[-1]['itempool'], 'positive')
    # with a.div(klass='row'):
    # 	with a.div(klass='column'):
    # 		a.h2(_t='Machines & power')
    # 		generate_machines(a, production_plan)
    # 	with a.div(klass='column'):
    # 		a.h2(_t='Extra resources')
    # 		generate_resources(a, production_plan[-1]['itempool'], 'negative')
    # a.button(type='button', klass='expndall', _t='Expand/Collapse all')

    for i in range(1, len(production_plan)):
        # Offset by 1 because first tier only has target item
        generate_tier(a, production_plan[i], i)

    return str(a)


try:
    # Load style
    with open('static\\style\\main.css', 'r') as stylefile:
        style = stylefile.read()
except FileNotFoundError:
    print('Could not find style file. Produced report will be very ugly')
    style = ''

try:
    # Load script
    with open('static\\script\\report_script.js', 'r') as scriptfile:
        script = scriptfile.read()
except FileNotFoundError:
    print('Could not find script file. Deactivating style so produced report still works')
    script = ''
    style = ''

if __name__ == "__main__":
    print('testing box "with" generation')

    prodplan = [{'itempool': {'Desc_AluminumIngot_C': 1.0, 'Desc_Silica_C': 0}}, {'itempool': {'Desc_AluminumScrap_C': 1.5, 'Desc_Silica_C': 1.25}, 'recipepool': {'Recipe_IngotAluminum_C': 0.016666666666666666}, 'itemtorec': {'Desc_AluminumIngot_C': 'Recipe_IngotAluminum_C'}}, {'itempool': {'Desc_Water_C': -0.5, 'Desc_AluminaSolution_C': 1.0, 'Desc_Coal_C': 0.5, 'Desc_RawQuartz_C': 0.75}, 'recipepool': {'Recipe_AluminumScrap_C': 0.004166666666666667,
                                                                                                                                                                                                                                                                                                                                                                                                                       'Recipe_Silica_C': 0.03333333333333333}, 'itemtorec': {'Desc_AluminumScrap_C': 'Recipe_AluminumScrap_C', 'Desc_Silica_C': 'Recipe_Silica_C'}}, {'itempool': {'Desc_Water_C': 1.0, 'Desc_Coal_C': 0.5, 'Desc_RawQuartz_C': 0.75, 'Desc_Silica_C': -0.4166666666666667, 'Desc_OreBauxite_C': 1.0}, 'recipepool': {'Recipe_AluminaSolution_C': 0.008333333333333333}, 'itemtorec': {'Desc_AluminaSolution_C': 'Recipe_AluminaSolution_C'}}]
    html = generate_html_flask(prodplan)

    tstrep = 'testreport.html'
    with open(tstrep, 'w') as f:
        f.write(html)
    webbrowser.open(os.getcwd()+'\\'+tstrep)
    print('travail terminé')
