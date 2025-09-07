import json

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
    To change: DONT TAKE PACKAGER/UNPACKAGER
    or make oil baseresource ?
    """
    data_itemtorecipes = {}
    
    for item_k in data_items:
        data_itemtorecipes[item_k] = []
        
        for recipe_k, recipe_vl in data_recipes.items():
            recipe_v = recipe_vl[0]
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


### Script code ###
data_recipes: dict
data_items: dict
data_buildings: dict

try:
    # Source: https://satisfactory.wiki.gg/wiki/Template:DocsRecipes.json
    with open('resource\\DocsRecipes.json', encoding='utf8') as f:
        data_recipes = json.load(f)
except FileNotFoundError:
    print('Could not find recipes file. Program will not work')
    exit()
try:
    # Source: https://satisfactory.wiki.gg/wiki/Template:DocsItems.json
    with open('resource\\DocsItems.json', encoding='utf8') as f:
        data_items = json.load(f)
except FileNotFoundError:
    print('Could not find items file. Program will not work')
    exit()
try:
    # Source: https://satisfactory.wiki.gg/wiki/Template:DocsBuildings.json
    with open('resource\\DocsBuildings.json', encoding='utf8') as f:
        data_buildings = json.load(f)
except FileNotFoundError:
    print('Could not find building file. Program will not work')
    exit()

#Generate item to recipes
data_itemtorecipes = build_item_to_recipes()
data_itemtodefaultrecipes = build_item_to_recipes(alternates=False)

#Generate base resources
data_baseresources = build_baseresources()

if __name__=='__main__':
    print('Execution complete')