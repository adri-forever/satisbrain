import webbrowser, copy, os
from typing import Literal
import numpy as np

# personal imports
import data, htmlreport

# Constants
MAX_ITER = 100 # Prevent infinite looping

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
        idmax = np.array(rec_score).argmax()
        recipe = recipes[idmax]
    else:
        print(f'No recipe found for item {data.data_items[item][0]['name']}')
    return recipe

def get_production_plan(target_item: str, qty: float, recipes: dict[str, str], base_resources: set[str]):
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
        
        itempool: dict[str, float] = copy.deepcopy(production_plan[previoustier]['itempool'])
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
                print(f'No available recipe for {data.data_items[item][0]['name']}. It has been added to base resources')
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

### Main code ###
if __name__=='__main__':
    example_run()
    
    print('Travail terminé')