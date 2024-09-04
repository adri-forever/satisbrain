import json, copy, timeit
from typing import Literal

"""
for future: take into account if water is produced somewhere as a byproduct, substract produced to needed amount
"""

### Functions ###
def build_item_to_recipes() -> dict:
    data_itemtorecipes = {}
    
    for item_k in data_items:
        data_itemtorecipes[item_k] = []
        
        for recipe_k, recipe_v in data_recipes.items():
            products = recipe_v['products']
            for product in products:
                if product['item']==item_k:
                    data_itemtorecipes[item_k].append(recipe_k)
    
    return data_itemtorecipes

def build_baseresources() -> set[str]:
    """
    Make set of items that are not produced by a crafting recipe
    
    Include water even though it is a byproduct of many recipes
    
    Includes things like radioactive waste because its not crafted but byproduct of generator. whatever
    """
    data_baseresources = {item for item, recipes in data_itemtorecipes.items() if not recipes}
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
               or not data_recipes[rec]['producedIn'] # cant compute whats not in a machine
               or not data_recipes[rec]['alternate'] # keep defaults
               or rec in alternates # and selected alternates
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

#Generate base resources
data_baseresources = build_baseresources()

### Main code ###
if __name__=='__main__':
    # exact, inexact = search_object('steel ingot')
    # print('Exact results:')
    # for res in exact:
    #     print(res)
    # print('Inexact results:')
    # for res in inexact:
    #     print(res)
        
    # if exact:
    #     print('Details for first result:\n', get_details(exact[1][1]))
    
    exact, inexact = search_object('liquid biofuel', 'items')
    print('Exact: ', exact)
    children, recipes = get_child_items(exact[0][1])
    print('Child items: ', children)
    print('Child recipes: ', recipes)
    