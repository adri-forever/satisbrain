import webbrowser, copy, os
from typing import Literal
import numpy as np

# personal imports
import data, htmlreport

"""
for future: take into account if water is produced somewhere as a byproduct, substract produced to needed amount
"""

# constants

# Prevent infinite looping
MAX_ITER = 100


### Functions ###
def get_details(key, datatype: Literal['recipes', 'items', 'schematics',
                                         'generators', 'resources', 'miners',
                                         'buildings'] = None) -> dict:
    """
    kinda useless? if you know the datatype just use the according dict
    unless the datatype is a variable
    """
    if datatype:
        return data.data[datatype][key]
    else:
        for datatype in data.data:
            if key in data.data[datatype]:
                return data.data[datatype][key]

def exact_search(name: str, dtypes: list[str]) -> list[tuple[str]]:
    results: list[str] = []
    for dtype in dtypes:
        for itemkey, item in data.data[dtype].items():
            for value in item.values():
                if isinstance(value, str):
                    if name.lower() == value.lower():
                        results.append((dtype, itemkey))
    return results

def exact_search_new(name: str, dtype: str) -> list[tuple[str]]:
    results: list[str] = []
    for itemkey, item in data.data[dtype].items():
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
        for itemkey, item in data.data[dtype].items():
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
    for itemkey, item in data.data[dtype].items():
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
    dtypes = data.data.keys()
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
    return data.data_recipes[recipe]['ingredients']

def get_child_items(item: str, alternates: list[str] = [], deep: bool = True, parent_recipes: set[str] = set()) -> tuple[set[str]]:
    """
    """ 
    #Get all possible recipes for item
    recipes = data.data_itemtorecipes[item]
    
    #Force absence of recipes in case of base resource
    #Useful for forced base resources like water
    if item in data.data_baseresources:
        recipes = []
    
    #Filter out recipes that are projected to be used higher in the chain to prevent looping
    recipes = [rec for rec in recipes
               if rec not in parent_recipes # prevent looping
               and data.data_recipes[rec]['producedIn'] # cant compute whats not in a machine
               and(
                   not data.data_recipes[rec]['alternate'] # keep defaults
                   or rec in alternates # and selected alternates
                   )
              ]
    
    #Select desired recipe
    # use default, but if an alternate is given use it and immediately break out of loop
    # unless its the only available recipe, do not use packager recipes
    recipe = ''
    for _recipe in recipes:
        if data.data_recipes[_recipe]['producedIn'][0]=='Desc_Packager_C' and len(recipes)>1:
            continue 
        if not data.data_recipes[_recipe]['alternate']:
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
    if recipe in data.data_recipes:
        for child in data.data_recipes[recipe]['ingredients']:
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

def build_production_tier(tier: int, production_plan: dict, itempool: dict[float], base_resources: list[str], recipes: dict[str]):
    tiername = f'tier{tier}'
    previoustier = f'tier{tier-1}'
    
    itempool = copy.deepcopy(production_plan[previoustier])
    production_plan[tiername] = {'recipepool': {}}

    for item, qty in itempool.items():
        if item not in data.data_baseresources and qty > 0:
            recipe = recipes[item] if item in recipes else None
            if not recipe:
                pass
                #try finding default recipe
            recipe_data = data.data_recipes[recipe]

            # Select rate of the right product, in case there are several
            item_qty = [product['amount'] for product in recipe_data['products'] if product['item']==item][0]

            # Calculate the needed amount of machines to satisfy the needed quantity of items (/min)
            machine_qty = qty * recipe_data['duration'] / (60 * item_qty)
            
            # Alter recipe pool
            production_plan[tiername]['recipepool'][recipe] = machine_qty
            
            # Alter item pool (products are substracted from, ingredients are added to the pool)
            for product in recipe_data['products']:
                product_item = product['item']
                product_qty = 60 * machine_qty * product['amount'] / recipe_data['duration']
                
                if product_item not in itempool:
                    itempool[product_item] = 0
                itempool[product_item] -= product_qty

            for ingredient in recipe_data['ingredients']:
                ingr_item = ingredient['item']
                ingr_qty = 60 * machine_qty * ingredient['amount'] / recipe_data['duration']
                
                if ingr_item not in itempool:
                    itempool[ingr_item] = 0
                itempool[ingr_item] += ingr_qty
        else:
            pass
            #if quantity is negative, dont do anything, the itempool is passed on from tier to tier
        
    return production_plan, recipes

def select_recipe(item: str):
    recipe = ''
    recipes = data.data_itemtorecipes[item]
    
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
        if item==data.data_recipes[rec][0]['products'][0]['item']: # if main product
            score += 1
        if not data.data_recipes[rec][0]['alternate']: # if default recipe
            score += 2
        if data.data_recipes[rec][0]['producedIn'][0]=='Desc_Packager_C': # if packaging/unpackaging
            score = -1
        
        rec_score[i] = score
    
    if recipes:
        idmax= np.array(rec_score).argmax()
        recipe = recipes[idmax]
    else:
        print(f'No recipe found for item {data.data_items[item]['name']}')
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
        left_items = [item_ for item_, qty_ in itempool.items() if qty_>1e-5 and item_ not in data.data_baseresources]
        
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
                print(f'No available recipe for {data.data_items[item]['name']}. It has been added to base resources')
                continue
            
            production_plan[tiername]['itemtorec'][item] = recipe
            
            #------------------
            # recipe = [rec for rec in data.data_itemtorecipes[item] if rec in recipes][0]
            recipe_data = data.data_recipes[recipe][0]
            
            # decide number of machines for recipe: divide asked quantity by recipe rate (/min)
            machine_qty = itempool[item] / (60 * recipe_data['products'][0]['amount'] / recipe_data['duration'])
            
            # Alter recipe pool
            production_plan[tiername]['recipepool'][recipe] = machine_qty
            
            # Alter item pool
            for product in recipe_data['products']:
                product_item = product['item']
                product_qty = 60 * machine_qty * product['amount'] / recipe_data['duration']
                
                if product_item not in itempool:
                    itempool[product_item] = 0
                itempool[product_item] -= product_qty

            for ingredient in recipe_data['ingredients']:
                ingr_item = ingredient['item']
                ingr_qty = 60 * machine_qty * ingredient['amount'] / recipe_data['duration']
                
                if ingr_item not in itempool:
                    itempool[ingr_item] = 0
                itempool[ingr_item] += ingr_qty

        if i==MAX_ITER-1:
            print(f'WARNING: Max recipe iterations reached. Looping may have occured.')
        
        # Remove items with quantity 0
        empty_items = [item_ for item_, qty_ in itempool.items() if abs(qty_)<1e-5] # Ignore items with too low of a quantity 
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


def example_run():
    production_plan, recipes = get_production_plan('Desc_NuclearFuelRod_C', 10, {}, data.data_baseresources)
    data.pretty_dict_print(production_plan)
    
    path = 'output\\test.html'
    if not os.path.exists('output'):
        os.mkdir('output')

    htmlreport.generate_html(production_plan, path)
    
    webbrowser.open(path)
    
def get_recipe_disp(recipe):
    data = data.data.data_recipes[recipe]
    disp_name = data.data["name"]
    machines = ', '.join([data.data_buildings[machine]['name'] for machine in data.data["producedIn"]])
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
            item_choices_disp = {str(i): data.data_items[item]['name'] for i, item in enumerate(results[:5])}
        
            print('Search results - select item:')
            data.pretty_dict_print(item_choices_disp, level=1)
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
        recipe_choices = {str(i): recipe for i, recipe in enumerate(data.data_itemtorecipes[item])}
        recipe_choices_disp = {str(i): get_recipe_disp(recipe) for i, recipe in enumerate(data.data_itemtorecipes[item])}
        recipe_choice = None if recipe_choices else 'back'
        if recipe_choice=='back':
            item = None
            continue
        while not recipe_choice:
            print('Search results - select item:')
            data.pretty_dict_print(recipe_choices_disp, level=1)
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
            data.pretty_dict_print(production_plan)
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

### Main code ###
if __name__=='__main__':
    # main()
    example_run()
    
    print('Travail terminé')