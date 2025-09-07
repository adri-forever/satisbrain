import json
from typing import Any

### Functions ###
def pretty_dict_print(dict_: dict[Any, Any], deep: bool = True, level: int = 0):
	indent = level*'\t'
	for key, value in dict_.items():
		if isinstance(value, dict) and deep:
			print(indent+f'{key} :')
			pretty_dict_print(value, deep=True, level=level+1)
		else:
			print(f'{indent}{key} : {value}')
	
def build_item_to_recipes(alternates: bool = True) -> dict:
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
	data_baseresources: set[str] = {item
						  for item, recipes in data_itemtodefaultrecipes.items()
						  if (not recipes)}
	
	data_baseresources |= {
		'Desc_OreIron_C',
		'Desc_OreBauxite_C',
		'Desc_OreGold_C',
		'Desc_OreCopper_C',
		'Desc_OreUranium_C',
		'Desc_Stone_C',
		'Desc_Coal_C',
		'Desc_Sulfur_C',
		'Desc_RawQuartz_C',
		'Desc_Water_C',
		'Desc_LiquidOil_C',
		'Desc_NitrogenGas_C'
	}

	return data_baseresources


### Script code ###
data_recipes: dict[str, list[dict[str, Any]]]
data_items: dict[str, list[dict[str, Any]]]
data_buildings: dict[str, list[dict[str, Any]]]

try:
	# Source: https://satisfactory.wiki.gg/wiki/Template:DocsRecipes.json
	with open('static\\gamedata\\DocsRecipes.json', encoding='utf8') as f:
		data_recipes = json.load(f)
except FileNotFoundError:
	print('Could not find recipes file. Program will not work')
	exit()
try:
	# Source: https://satisfactory.wiki.gg/wiki/Template:DocsItems.json
	with open('static\\gamedata\\DocsItems.json', encoding='utf8') as f:
		data_items = json.load(f)
except FileNotFoundError:
	print('Could not find items file. Program will not work')
	exit()
try:
	# Source: https://satisfactory.wiki.gg/wiki/Template:DocsBuildings.json
	with open('static\\gamedata\\DocsBuildings.json', encoding='utf8') as f:
		data_buildings = json.load(f)
except FileNotFoundError:
	print('Could not find building file. Program will not work')
	exit()

#Generate item to recipes
data_itemtorecipes = build_item_to_recipes()
data_itemtodefaultrecipes = build_item_to_recipes(alternates=False)

#Generate base resources
data_baseresources: set[str] = build_baseresources()

if __name__=='__main__':
	print('Execution complete')