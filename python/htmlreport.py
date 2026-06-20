from python.brain import data, Graph, Node, EPSILON
import airium
import uuid
import copy
import sys
import os
import webbrowser
from typing import Literal, Any
from pathlib import Path
from contextlib import contextmanager

sys.path.append(str(Path(__file__).resolve().parent.parent))

# personal imports


def generate_recipe(a: airium.Airium, recipe_data: dict[str, Any], qty: int):

    # qty = round(qty, DIGITS):

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

                # qrate = round(qty * rate, DIGITS)
                # rate = round(rate, DIGITS)

                a.td(_t=prd_name)
                a.td(klass='fixed', **{'data-value': rate})
                a.td(klass='high scalable', **{'data-value': qty * rate})
                if i == 0:
                    a.td(_t=machine)
                    a.td(klass='scalable', **{'data-value': qty})
        with a.tr():
            a.th(_t='Ingredients')
        for i, ingredient in enumerate(ingredients):
            with a.tr():
                ingr_name = data.data_items[ingredient['item']][0]['name']
                rate = 60 * ingredient['amount'] / recipe_data['duration']

                # qrate = round(qty * rate, DIGITS)
                # rate = round(rate, DIGITS)

                a.td(_t=ingr_name)
                a.td(klass='fixed', **{'data-value': rate})
                a.td(klass='high scalable', **{'data-value': qty * rate})


def generateResources(a: airium.Airium, resources: dict[str, float], fltr: Literal['positive', 'negative', 'all'] = 'all'):
    # filter the resources to display
    pool: dict[str, float] = {}
    for item, amount in resources.items():
        if fltr == 'positive':
            if amount > EPSILON:
                pool[item] = amount
        elif fltr == 'negative':
            if -amount > EPSILON:
                # show amounts as positive if only negative are wanted
                pool[item] = -amount
        else:
            if abs(amount) > EPSILON:
                pool[item] = amount

    if pool:
        with a.table():
            with a.tr():
                a.th(_t='Resource')
                a.th(_t='Total (/min)')
            for item, amount in pool.items():
                res_name = data.data_items[item][0]['name']
                with a.tr():
                    a.td(_t=res_name)
                    a.td(klass='scalable', **{'data-value': amount})
    elif fltr == 'negative':
        a.span(_t='No leftover !', klass='high')


def generateMachines(a: airium.Airium, graph: Graph):
    machines: list[str] = []
    names: list[str] = []
    amounts: list[float] = []
    powers: list[float] = []
    id: str
    node: Node
    producedIn: list[str]
    machine: str
    i: int
    machine_data: dict[str]
    recipe_data: dict[str]
    power: float
    for id, node in graph.nodes.items():
        if node.type == 'recipe':
            machine = ""
            if id in data.data_recipes:
                recipe_data = data.data_recipes[id][0]
                producedIn = recipe_data['producedIn']
                if len(producedIn) > 0:
                    machine = producedIn[0]

                if machine:
                    machine_data = data.data_buildings[machine][0]

                    if machine not in machines:
                        machines.append(machine)
                        amounts.append(0)
                        powers.append(0)
                        names.append(machine_data['name'])
                    i = machines.index(machine)
                    amounts[i] += node.getRequired()

                    power = machine_data['powerUsage'] - machine_data['powerGenerated']
                    if power == 0:
                        power = (recipe_data["minPower"] +
                                 recipe_data["maxPower"])/2
                    powers[i] += power*amounts[i]

    if machines:
        with a.table():
            with a.tr():
                a.th(_t='Machine')
                a.th(_t='Quantity')
                a.th(_t='Estimated power (MW)')
            for i in range(len(machines)):
                with a.tr():
                    a.td(_t=names[i])
                    a.td(klass='scalable', **{"data-value": amounts[i]})
                    a.td(klass='scalable', **{"data-value": powers[i]})
            with a.tr():
                a.td(_t='Total')
                a.td(_t='')
                a.td(klass='scalable', **{"data-value": sum(powers)})
    a.span(_t='Resource extraction is not taken into account. Overclocking machines will result in much higher power usage.', klass='light')


@contextmanager
def generate_box(a: airium.Airium, boxclass: str = '', item: str = '', recipe: str = '', title: str = '', edit: bool = False, collapsed: bool = False, qty: float = 1):
    title2: str = ""

    dropdownvalues: dict[str, str] = {"": "--"}

    if boxclass in ["item", "recipe"]:
        if item in data.data_items:
            title = data.data_items[item][0]["name"]
    if boxclass == "item":
        dropdownvalues = {key: value[0]['name']
                          for key, value in data.data_items.items()}
    if boxclass == "recipe":
        title2 = data.data_recipes[recipe][0]["name"]
        dropdownvalues = {key: value[0]['name'] for key, value in data.data_recipes.items(
        ) if key in data.data_itemtorecipes[item]}
        dropdownvalues['baseresource'] = 'Set as base resource'

    # bypass - being an invalid name in python by using kwargs
    with a.div(klass=f"box {boxclass}{" edit" if edit else ""}{" collapsed" if collapsed else ""}", **{"data-item": item}):
        with a.div(klass="header"):
            with a.div(klass="left"):
                a.button(klass="status smallbutton", onclick="changeStatus(this)")
                a.div(klass="title1", _t=title)
                a.div(klass="title2", _t=title2)
                if boxclass in ["item", "recipe"]:
                    with a.div(klass="selector").select(id=uuid.uuid4()):
                        for key, value in dropdownvalues.items():
                            selection = {}
                            if (boxclass == "item" and key == item) or (boxclass == "recipe" and key == recipe):
                                selection["selected"] = "selected"
                            a.option(_t=value, value=key, **selection)
            with a.div(klass="right"):
                a.button(klass="validate smallbutton", onclick="validate(this)")
                a.button(klass="edit smallbutton", onclick="toggleEdit(this)")
                a.button(klass="collapse smallbutton",
                         onclick="toggleCollapse(this, event)")
        with a.div(klass="content"):
            if (boxclass == "item" and item in data.data_items):
                a.div(klass="itemdesc",
                      _t=data.data_items[item][0]['description'])
            if (boxclass == "recipe" and recipe in data.data_recipes):
                recipe_data = data.data_recipes[recipe][0]
                generate_recipe(a, recipe_data, qty)
            yield


def generateTier(a: airium.Airium, nodes: list[Node], tierno: int) -> airium.Airium:
    with generate_box(a, 'tier container', '', '', f'Stage {tierno}', False, False):
        for node in nodes:
            if node.type == 'item':
                raise ValueError(
                    f'Trying to generate recipe box for node {node.id} of type {node.type}')
            for item in node.activeparents:
                with generate_box(a, 'recipe', item, node.id, '', True, False, node.getRequired(item)):
                    pass
    return a


def generateHtmlFlask(graph=Graph()) -> str:
    a = airium.Airium()

    with generate_box(a, 'configuration container', '', '', 'Configuration'):
        with generate_box(a, 'item_multi', '', '', 'Item inputs', False, False):
            with a.div(klass="template hidden"):
                with a.select(id=uuid.uuid4()):
                    for key, value in data.data_items.items():
                        a.option(_t=value[0]['name'], value=key)
            with a.div(klass='buttons'):
                a.button(klass="validate smallbutton", onclick="validate(this)")
                a.button(klass="add smallbutton", onclick="addItem(this, null, null, true)")
        with generate_box(a, 'baseresource', '', '', 'Base resource', False, False):
            a.button(klass="reset", onclick="resetBaseResource()", _t="Reset")
        with a.div(klass='loads'):
            a.button(klass='export', onclick='exportPlan(this)', _t='Export')
            a.input(klass='import', id=uuid.uuid4(),
                    type='file', accept="application/json", onchange="onImport(event)", autocomplete="off")
            a.button(klass='import', onclick='showUpload()', _t='Import')

    with generate_box(a, 'information container', '', '', 'Information'):
        with generate_box(a, '', '', '', 'Input quantities', False, False):
            generateResources(a, graph.getBalance(), 'positive')
        with generate_box(a, '', '', '', 'Extra resources', False, False):
            generateResources(a, graph.getBalance(), 'negative')
        with generate_box(a, '', '', '', 'Machines', False, False):
            generateMachines(a, graph)

    a.button(_t='Expand/Collapse all', klass='collapseall',
             onclick='toggleAll(this, event)')

    for i in range(2, graph.getDepth(), 2):
        # depth 0 is start, depth 1 is start items, depth 2 is the first actual recipe
        # last depth is items, so we only need to get to depth n-1
        # depths alternate between items and recipes, so skip the item part
        generateTier(a, graph.getNodes(i), int(i/2))

    return str(a)


if __name__ == "__main__":
    print("No main executable code in this module")
