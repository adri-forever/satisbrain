import json, copy, timeit, airium, webbrowser, math
from typing import Literal
import numpy as np

"""
the ultimate test for this tool will be:
successfuly produce a plan for fuel using diluted packaged fuel
=> fuel (unpackage: packaged fuel)
=> packaged fuel (diluted fuel: packaged water + heavy oil residue)
=> packaged water (package: water) + heavy oil residue (heavy oil residue: oil)
=> input: water, oil, canisters (0/min)
=> extra: polymer resin

inputs you should give:
    alternates: packaged diluted fuel, heavy oil residue
    
    
    
Trucs a fixer: dans les recettes 'principales' n'utiliser que les recettes dont l'item est le premier output:
NE PAS ESSAYER DE FABRIQUER DE LACIDE SULFURIQUE AVEC DES URANIUM CELL ????? Ca se fait avec du SULFUR et de LEAU merde
"""

### Functions ###
def pretty_dict_print(dict_: dict, deep: bool = True, level: int = 0):
    indent = level*'\t'
    for key, value in dict_.items():
        if isinstance(value, dict) and deep:
            print(indent+f'{key} :')
            pretty_dict_print(value, deep=True, level=level+1)
        else:
            print(f'{indent}{key} : {value}')
    
def build_item_to_recipes(alternates: bool = True) -> dict:
    """
    """
    data_itemtorecipes = {}
    
    for item_k in data_items:
        data_itemtorecipes[item_k] = []
        
        for recipe_k, recipe_v in data_recipes.items():
            products = recipe_v['products']
            for product in products:
                # Append recipe if:
                # recipe produces selected item
                # and recipe comes from a machine
                # and recipe is default, unless we asked for
                if product['item']==item_k and (not recipe_v['alternate'] or alternates) and recipe_v['inMachine']:
                    data_itemtorecipes[item_k].append(recipe_k)
    
    return data_itemtorecipes

def build_baseresources() -> set[str]:
    """
    Make set of items that are not produced by a crafting recipe
    
    Include water even though it is a byproduct of many recipes
    
    Includes things like radioactive waste because its not crafted but byproduct of generator. whatever
    
    For 1.0: manually make the list for ores. they can now be transmuted.
    iron, copper, limestone, coal, crystal, caterium, bauxite, uranium, sulfur, SAM(not necessary?), water, oil, nitrogen
    """
    data_baseresources = {item
                          for item, recipes in data_itemtodefaultrecipes.items()
                          if (not recipes)}
    
    data_baseresources.add('Desc_OreIron_C')
    data_baseresources.add('Desc_OreBauxite_C')
    data_baseresources.add('Desc_OreGold_C')
    data_baseresources.add('Desc_OreCopper_C')
    data_baseresources.add('Desc_OreUranium_C')
    data_baseresources.add('Desc_Stone_C')
    data_baseresources.add('Desc_Coal_C')
    data_baseresources.add('Desc_Sulfur_C')
    data_baseresources.add('Desc_RawQuartz_C')
    data_baseresources.add('Desc_SAM_C')
    
    data_baseresources.add('Desc_Water_C')
    data_baseresources.add('Desc_LiquidOil_C')
    data_baseresources.add('Desc_NitrogenGas_C')
    
    return data_baseresources

def build_counterrecipes() -> dict[str]:
    """
    dict with all recipes that have a counter (recipes that loop, like package/unpackage)
    and their counterpart
    example: { packagewater: unpackagewater, unpackagewater: packagewater, etc}
    """
    pass

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
    results: list[str] = []
    for dtype in dtypes:
        for itemkey, item in data[dtype].items():
            for value in item.values():
                if isinstance(value, str):
                    if name.lower() == value.lower():
                        results.append((dtype, itemkey))
    return results

def exact_search_new(name: str, dtype: str) -> list[tuple[str]]:
    results: list[str] = []
    for itemkey, item in data[dtype].items():
        for value in item.values():
            if isinstance(value, str):
                if name.lower() == value.lower():
                    results.append(itemkey)
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
  
def inexact_search_new(name: str, dtype: str) -> list[tuple[str]]:
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
    results_inex: list[str] = []
    
    #Delimiters
    inex_delimiters = [' ', ',']
    base_delimiter = inex_delimiters[0]
    for i, delimiter in enumerate(inex_delimiters):
        if i!=0:
            name_inex = name.replace(delimiter, base_delimiter)
    name_parts = name_inex.split(base_delimiter)

    #Search process
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
            results_inex.append(itemkey)
    
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

def build_production_tier(tier: int, production_plan: dict, base_resources: list[str], recipes: dict[str: str]):
    """
    finish making this function, create wrapper func to use it,
    but the endgame is to use only 1 function like get_production_plan_old, without an intermediate function
    
    AH EN FAIT JAVAIS DES BONNES IDEES POUR LES LEFT ITEMS....
    Juste, faire get_new_new_production_plan (au cas ou on a eu des bonnes idees dans le refactor 1) un copie colle de
    get production plan avec le nouveau modele de production plan:
        ancien:
            {
                'tier0': recipepool,
                'tier1': recipepool,
                'base_resources': resources
            }
        
        nouveau:
            {
                'tier0': {recipepool: recipepool, itempool: itempool},
                'tier1': {recipepool: recipepool, itempool: itempool},
                etc
            }
            + notion de item to 1 recipe contenant pour chaque item LA recette associée
            (si pas de recette associée, prendre celle par défaut)
            (faire fonction pour trouver une recette pour un item (options alternate? unpack/pack?))
            + notion de base_resources
            (pas les items inputs et leur quantité, mais la liste de base de ce qui est ou non considéré comme input!)
            (modifiable)
            (créer un set de base de resources 'naturelles'. nécessaire pour la 1.0 car les 'ores' peuvent être transmutés!)
    """
    tiername = f'tier{tier}'
    previoustier = f'tier{tier-1}'
    
    itempool = copy.deepcopy(production_plan[previoustier])
    production_plan[tiername] = {'recipepool': {}}

    for item, qty in itempool.items():
        if item not in data_baseresources and qty > 0:
            recipe = recipes[item] if item in recipes else None
            if not recipe:
                pass
                #try finding default recipe
            recipe_data = data_recipes[recipe]

            # Select rate of the right product, in case there are several
            item_qty = [product['amount'] for product in recipe_data['products'] if product['item']==item][0]

            # Calculate the needed amount of machines to satisfy the needed quantity of items (/min)
            machine_qty = qty * recipe_data['time'] / (60 * item_qty)
            
            # ----
            # Check all previous tiers, if item was already part of an itempool prior retrieve it to this tier
            # add the fetched item quantities to all pools inbetween
            # add the machine quantity of pool fetched from to current machine quantity
            # 
            # children problem - if there is more than 1 tier difference between the puller and the pulled:
            # fusing the recipes will not be a problem, but the quantities will fuck up
            # the pulling tier will have the correct desired quantity, but will still fetch the extra children quantities
            #
            # other solution:
            # only fuse at the end, the quantities will never fuck up ...
            # ----
            
            # Alter recipe pool
            production_plan[tiername]['recipepool'][recipe] = machine_qty
            
            # Alter item pool (products are substracted from, ingredients are added to the pool)
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
        else:
            pass
            #if quantity is negative, dont do anything, the itempool is passed on from tier to tier
        
    return production_plan, recipes

def select_recipe(item: str):
    recipe = ''
    recipes = data_itemtorecipes[item]
    
    rec_score = [0]*len(recipes)
    
    """
    How should we choose recipes
    1- Default recipe, and main product // 3
    2- Default recipe, byproduct // 2
    3- Alternate recipe, main product // 1
    4- Alternate recipe, byproduct // 0
    5- (Un)Packaging // -1
    """
    
    for i in range(len(recipes)):
        rec = recipes[i]
        score = 0
        if item==data_recipes[rec]['products'][0]['item']: # if main product
            score += 1
        if not data_recipes[rec]['alternate']: # if default recipe
            score += 2
        if data_recipes[rec]['producedIn'][0]=='Desc_Packager_C': # if packaging/unpackaging
            score = -1
        
        rec_score[i] = score
    
    if recipes:
        idmax= np.array(rec_score).argmax()
        recipe = recipes[idmax]
    else:
        print(f'No recipe found for item {data_items[item]['name']}')
    return recipe

def get_production_plan(target_item: str, qty: float, recipes: dict[str: str], base_resources: list[str]):
    # Contains steps
    production_plan = {}
    tiername = 'tier0'
    production_plan[tiername] = {'itempool': {target_item: qty}}
    
    if qty <= 0:
        print('Cannot produce negative amount of items. Let us make 1 of these per minute')
        qty = 1
    
    for i in range(1, MAX_ITER): #change to while once we got the condition
        #Make room for current tier
        previoustier = tiername
        
        itempool: dict[str: float] = copy.deepcopy(production_plan[previoustier]['itempool'])
        # next_itempool: dict[str: float] = copy.deepcopy(itempool) # questionable
        # on certain occasions, not separating the pools this will compress a recipe to one tier higher than it shoulde be
        # However, separating the pools may cause some error when a single recipe has a byproduct
        
        # how to handle the 1 tier up situation:
        # if the item you are currently treating is child of other items in the tier,
        # skip to compute on next tie
        #
        # do that during tier building or during plan refinement ?
        # the advantage of doing that during tier building is that we have left_items to refer to 
        
        #List all items to produce in said tier
        left_items = [item_ for item_, qty_ in itempool.items() if qty_>10**(-DIGITS) and item_ not in base_resources]
        
        if not left_items:
            break # if no items are left to craft, exit loop (and dont make a next tier)
        
        tiername = f'tier{i}'
        production_plan[tiername] = {'itempool': {}, 'recipepool': {}, 'itemtorec': {}}
        
        for item in left_items:
            if item in recipes:
                recipe = recipes[item]
            else:
                recipe = select_recipe(item)
                recipes[item]= recipe #this way any recipe that was not chosen is added to the dict
            
            if not recipe:
                base_resources.add(item)
                print(f'No available recipe for {data_items[item]['name']}. It has been added to base resources')
                continue
            
            production_plan[tiername]['itemtorec'][item] = recipe
            
            recipe_data = data_recipes[recipe]
            
            # decide number of machines for recipe: divide asked quantity by recipe rate (/min)
            machine_qty = itempool[item] / (60 * recipe_data['products'][0]['amount'] / recipe_data['time'])
            
            # Alter recipe pool
            production_plan[tiername]['recipepool'][recipe] = machine_qty
            
            # Alter item pool
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

        if i==MAX_ITER-1:
            print(f'WARNING: Max recipe iterations reached. Looping may have occured.')
        
        # Remove items with quantity 0
        empty_items = [item_ for item_, qty_ in itempool.items() if abs(qty_)<10**(-DIGITS)] # Ignore items with too low of a quantity 
        for empty_item in empty_items:
            itempool.pop(empty_item)
        
        production_plan[tiername]['itempool'] = itempool

    # Refine plan: concatenate recipes that appear several times to lowest tier
    for item, recipe in recipes.items():
        # Find all tiers where recipe appear
        tiers_recipe: list[str] = []
        recipetotal = 0
        for tier, plan in production_plan.items():
            # Count recipe qty
            if 'recipepool' in plan:
                if recipe in plan['recipepool']:
                    tiers_recipe.append(tier)
                    recipetotal += plan['recipepool'][recipe]
        
        # Find all tiers where item (should!) appear
        highest_tier = ''
        lowest_tier = ''
        tiers_item: list[str] = []
        for tier, plan in production_plan.items():
            # Find highest and lowest tier where item appear
            if 'itempool' in plan:
                if item in plan['itempool']:
                    if not highest_tier:
                        highest_tier = tier
                    lowest_tier = tier
        #Find all tiers between highest and lowest
        intermediate = False
        for tier in production_plan.keys():
            intermediate |= tier==highest_tier # Start registering if we hit the highest tier
            
            if intermediate:
                tiers_item.append(tier)
                
            intermediate &= not tier==lowest_tier # Stop registering if we hit the lowest tier
        
        # Push recipe down lowest
        if len(tiers_recipe)>1:
            for tier in tiers_recipe:
                production_plan[tier]['recipepool'].pop(recipe)
                production_plan[tier]['itemtorec'].pop(item)
            production_plan[tiers_recipe[-1]]['recipepool'][recipe] = recipetotal
            production_plan[tiers_recipe[-1]]['itemtorec'][item] = recipe
        
        # Propagate item quantities
        itemtotal = 0
        if len(tiers_item)>1:
            for tier in tiers_item:
                plan = production_plan[tier]
                if item not in plan['itempool']:
                    plan['itempool'][item] = 0
                plan['itempool'][item] += itemtotal
                itemtotal = plan['itempool'][item]
    
    return production_plan, recipes

def generate_recipe(a: airium.Airium, recipe_data: dict, qty: int):
    
    qty = round(qty, DIGITS)
    
    products = recipe_data['products']
    ingredients = recipe_data['ingredients']
    
    machine = data_buildings[recipe_data['producedIn'][0]]['name']
    
    with a.table():
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
                prd_name = data_items[product['item']]['name']
                rate = 60 * product['amount'] / recipe_data['time']
                
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
                ingr_name = data_items[ingredient['item']]['name']
                rate = 60 * ingredient['amount'] / recipe_data['time']
                
                qrate = round(qty * rate, DIGITS)
                rate = round(rate, DIGITS)
                
                a.td(_t=ingr_name)
                a.td(_t='{:g}'.format(rate))
                a.td(_t='{:g}'.format(qrate), klass='high') 

def get_recipe_title(recipe_data: dict) -> str:
    return f'{recipe_data['name']} {'(alternate)' if recipe_data['alternate'] else ''}'

def generate_tier(a: airium.Airium, tierno: int, tier: dict):
    """
    add recipe name in tab and if alternate or not
    """
    a.button(type='button', klass='collapsible', _t=f'Stage {tierno}')
    with a.div(klass='content'):
        if 'recipepool' in tier:
            with a.div(klass='tiercontainer'):
                for recipe in tier['recipepool']:
                    recipe_data = data_recipes[recipe]
                    # a.button(type='button', klass='collapsible', _t=get_recipe_title(recipe_data))
                    # with a.div(klass='content'):
                    #     with a.div(klass='tablecont'):
                    #         generate_recipe(a, recipe_data, tier['recipepool'][recipe])
                    with a.div(klass='tierbox'):
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
                res_name = data_items[resource]['name']
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
                recipe_data = data_recipes[recipe]
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
                machine_data = data_buildings[machine]
                name = machine_data['name']
                power = round(qty * machine_data['metadata']['powerConsumption'], DIGITS)
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
    enlever les collapsibles de 2e etage, mettre titre en h3 avec recipe dans un truc (div?) et les mettre cote a cote
    permettra peut etre d'avoir 2 tableaux cote a cote
    watch out for variable power consumption machines
    """
    a = airium.Airium()
    
    tierlist = list(production_plan.keys()) # tier list, lol
    target_item = list(production_plan[tierlist[0]]['itempool'].keys())[0]
    target_recipe = list(production_plan[tierlist[1]]['recipepool'].keys())[0]
    target_quantity = production_plan[tierlist[0]]['itempool'][target_item]
    target_quantity = '{:g}'.format(round(target_quantity, DIGITS))
    
    item_name = data_items[target_item]['name']
    
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
                    a.h2(_t=f'Recipe: {get_recipe_title(data_recipes[target_recipe])}')
                    generate_recipe(a, data_recipes[target_recipe], production_plan[tierlist[1]]['recipepool'][target_recipe])
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
    
def example_run():
    production_plan, recipes = get_production_plan('Desc_NuclearFuelRod_C', 10, {}, data_baseresources)
    pretty_dict_print(production_plan)
    
    path = 'output\\test.html'
    generate_html(production_plan, path)
    
    webbrowser.open(path)
    
def get_recipe_disp(recipe):
    data = data_recipes[recipe]
    disp_name = data["name"]
    machines = ', '.join([data_buildings[machine]['name'] for machine in data["producedIn"]])
    txt = f'{disp_name} (produced in {machines})'
    return txt

def main():
    print('\t--- SATISBRAIN ---')
    
    item = None
    while not item:
        search = input('Please enter desired item: ')
        ex_res = exact_search_new(search, 'items')
        inex_res = inexact_search_new(search, 'items')
        
        results = list(set(ex_res+inex_res))
        item_choice = None if results else 'back'
        while not item_choice:
            item_choices = {str(i): item for i, item in enumerate(results[:5])}
            item_choices_disp = {str(i): data_items[item]['name'] for i, item in enumerate(results[:5])}
        
            print('Search results - select item:')
            pretty_dict_print(item_choices_disp, level=1)
            print('Enter "back" to change desired item input')
            item_choice = input('Choice: ')
            
            if not (item_choice=='back' or item_choice in item_choices):
                print('Invalid input')
                item_choice = None
        
        if item_choice=='back':
            continue
        else:
            item = item_choices[item_choice]
            item_disp = item_choices_disp[item_choice]
    
        print(f'Chosen item: {item_disp}')
        recipe_choices = {str(i): recipe for i, recipe in enumerate(data_itemtorecipes[item])}
        recipe_choices_disp = {str(i): get_recipe_disp(recipe) for i, recipe in enumerate(data_itemtorecipes[item])}
        recipe_choice = None if recipe_choices else 'back'
        if recipe_choice=='back':
            item = None
            continue
        while not recipe_choice:
            print('Search results - select item:')
            pretty_dict_print(recipe_choices_disp, level=1)
            print('Enter "back" to change desired item input')
            recipe_choice = input('Choice: ')
            
            if not (recipe_choice=='back' or recipe_choice in recipe_choices_disp):
                print('Invalid input')
                recipe_choice = None
        
        if recipe_choice=='back':
            item = None
            continue
        else:
            recipe = recipe_choices[recipe_choice]
            recipe_disp = recipe_choices_disp[recipe_choice]
        
        print('Chosen recipe:', recipe_disp)
        
        qty = -1
        while qty<=0:
            qty = input('Enter desired production rate: ')
            if qty.isnumeric():
                qty = float(qty)
            else:
                print('Please enter a numeric value, greater than 0')
                qty = -1
                
        loop = True
        while loop:
            production_plan = get_production_plan(recipe, qty, [])
            pretty_dict_print(production_plan)
            loop_choice = input('Good ? (Y/N)')
            
            loop = True
            if loop_choice=='Y':
                loop = False
            elif loop_choice!='N':
                print('couldnt catch that. looping just in case')
        

    #while smth
    #generate prodplan
    #use alternate ? #select tier #select recipe to change

    #generate html (choose name depending on recipe and time)

    #open html

    print('Travail terminé !')

### Script code ###
try:
    #Load data
    with open('resource\\data.json', encoding='utf-8') as f:
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
MAX_ITER = 10
# Number of digits floats are rounded to
DIGITS = 3

# Web shit, CSS and JS
style = """body {
	background-color: #333;
	color: white;
	font-family: "Segoe UI", sans-serif;
}

h2, h3 {
    margin-bottom: 5px;
}

table, th {
    border: 1px dashed #555;
}

td, th {
	padding: 2px 8px;
	font-size: 16px;
}

.tiercontainer {
    display: flex;
    flex-wrap: wrap; /* Allows the boxes to wrap onto the next line */
    gap: 20px; /* Optional: Adds space between the boxes */
    padding: 0 0 20px;
}

.tierbox {
    flex: auto; /* Prevents the boxes from growing or shrinking */
    justify-content: center;
}

.tablecont {
    padding: 10px 10px;
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
	cursor: pointer;
    color: white;
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
	padding: 0 18px;
	display: none;
	overflow: hidden;
	background-color: #333;
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

### Main code ###
if __name__=='__main__':
    # main()
    example_run()
    
    print('Travail terminé')