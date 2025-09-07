import webbrowser
from typing import Literal

# personal imports
import data, htmlreport

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

def general_lookup(slug: str):
    pass

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

def get_production_plan(item: str, qty: float, recipes: list[str]):
    # Contains steps
    production_plan = {}
    
    recipe = [rec for rec in recipes if rec in data.data_itemtorecipes[item]][0]
    item_to_recipe = {item: recipe}
    recipe_data = data.data_recipes[recipe]
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
        left_items = [item for item, iqty in itempool.items() if iqty>0 and item not in data.data_baseresources]
        if not left_items:
            break # if no items are left to craft, exit loop
        
        for item in left_items:
            recipe = [rec for rec in data.data_itemtorecipes[item] if rec in recipes][0]
            recipe_data = data.data_recipes[recipe]
            
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

        if i==MAX_ITER-1:
            raise LookupError(f'Max recipe iterations reached. Looping may have occured. Production plan: {production_plan}')
        
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
    extra_resources = {item: -value for item, value in itempool.items() if value<0}
    production_plan['extra_resources'] = extra_resources
    
    return production_plan

def build_production_tier(tier: int, production_plan: dict, itempool: dict[float], base_resources: list[str], recipes: dict[str]):
    tiername = f'tier{tier}'
    production_plan[tiername] = {}

    for item, qty in itempool.items():
        if item in data.data_baseresources:
            if 'base_resources' not in production_plan:
                production_plan['base_resources'] = {}
            
            production_plan['base_resources']['item'] = qty
        elif qty > 0:
            recipe = recipes[item] if item in recipes else None
            if not recipe:
                pass
                #try finding default recipe
            recipe_data = data.data_recipes[recipe]

            # Select rate of the right product, in case there are several
            item_qty = [product['amount'] for product in recipe_data['products'] if product['item']==item][0]

            # Calculate the needed amount of machines to satisfy the needed quantity of items (/min)
            machine_qty = qty * recipe_data['time'] / (60 * item_qty)
            
            # Alter itempool (products are substracted from, ingredients are added to the pool)
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

    return production_plan, itempool

def get_production_plan_new(target_recipe: str, qty: float, allowed_recipes: list[str]):
    # Contains steps
    production_plan = {}
    
    target_recipe_data = data.data_recipes[target_recipe]
    target_item = recipe_data['products'][0]['item']
    
    if qty <= 0:
        print('Cannot produce negative amount of items. Creating plan for singular machine')
        qty = 60 * target_recipe_data['products'][0]['amount'] / target_recipe_data['time'] # /min
    
    # For calculation
    itempool = {target_item: qty}
    
    for i in range(MAX_ITER): #change to while once we got the condition
        #Make room for current tier
        tiername = f'tier{i}'
        production_plan[tiername] = {}
        
        #List all items to produce in said tier
        left_items = [item for item, iqty in itempool.items() if iqty>0 and item not in data.data_baseresources]
        if not left_items:
            break # if no items are left to craft, exit loop
        
        for item in left_items:
            
            if item==target_item:
                recipe = target_recipe
            else:
                pass
                # find recipe for this item:
                # dont take alternates, unless they are in allowed recipes (in which case they MUST be chosen)
                # (two alternates for same item shouldnt be allowed)
                # if only way to craft item is alternate, choose it but mention it
                # think about what to do with unpacking recipes ...
                #   idea 1: if we say lets use pack/unpack, forbid to use counter recipe (unpack/pack)
            
            # once you have the recipe chosen, the rest is already written -->
            
            #------------------
            # recipe = [rec for rec in data.data_itemtorecipes[item] if rec in recipes][0]
            recipe_data = data.data_recipes[recipe]
            
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

        if i==MAX_ITER-1:
            raise LookupError(f'Max recipe iterations reached. Looping may have occured. Production plan: {production_plan}')
        
        # print('Item pool:')
        # print(itempool)
        # print('Production plan:')
        # print(production_plan[tiername])
    
    # Refine plan
    #Downwards: concatenate recipes that appear several time to lowest tier
    recipes = [] #prevent bug, we are remaking everything
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
    extra_resources = {item: -value for item, value in itempool.items() if value<0}
    production_plan['extra_resources'] = extra_resources
    
    return production_plan

def example_run():
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
    data.pretty_dict_print(production_plan)
    
    path = 'output\\test.html'
    htmlreport.generate_html(production_plan, path)
    
    webbrowser.open(path)

def get_recipe_disp(recipe):
    data.data = data.data_recipes[recipe]
    disp_name = data.data["name"]
    machines = ', '.join([data.data_buildings[machine]['name'] for machine in data.data["producedIn"]])
    txt = f'{disp_name} (produced in {machines})'
    return txt

def alter_pplan_recipes(production_plan: dict):
    """
    select tier
    select items in tier itempool to change recipes
    recompute production plan
    do it again
    add check to cleanum recipes for items that are not contained in the plan anymore
    """
    return production_plan

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
            production_plan = get_production_plan_new(recipe, qty, [])
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

# Prevent infinite looping
MAX_ITER = 100

### Main code ###
if __name__=='__main__':
    # main()
    example_run()