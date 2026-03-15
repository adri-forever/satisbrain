import copy, os, sys, time
from typing import Literal
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent))

# personal imports
from python import data
from python import utils

# Constants
DEBUG: bool = False
ERROR_ON_WARNING: bool = True
MAX_ITER: int = 40  # Prevent infinite looping
EPSILON: float = 1e-6

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

def selectRecipe(item: str, alternates: Literal['favor', 'forbid', 'unfavor', 'indifferent'] = 'unfavor') -> str:
    recipe: str = ''
    recipes: list[str] = data.data_itemtorecipes[item]

    rec_score: dict[str, int] = {}

    """
    How should we choose recipes
    1- Default recipe, and main product // 3
    2- Alternate recipe, main product // 2
    3- Default recipe, byproduct // 1
    4- Alternate recipe, byproduct // 0
    5- (Un)Packaging // -1
    """
    altscore: int = 1
    if alternates == 'favor':
        altscore = 3
    elif alternates == 'indifferent':
        altscore = 0
    
    for i in range(len(recipes)):
        rec = recipes[i]
        score = 0
        # if main product
        if item == data.data_recipes[rec][0]['products'][0]['item']:
            score += 2
        if not data.data_recipes[rec][0]['alternate']:  # if default recipe
            score += altscore
        else:
            if alternates=='forbid':
                continue
        # if packaging/unpackaging
        if data.data_recipes[rec][0]['producedIn'][0] == 'Desc_Packager_C':
            score = -1

        rec_score[rec] = score

    if recipes:
        recipe = max(rec_score, key=rec_score.get)
    else:
        print(f'No recipe found for item {data.data_items[item][0]['name']}')
    return recipe

def getProductQuantity(recipe_data: dict, item: str) -> float:
    # for multi product recipes, find the produced quantity of desired 

    qty: float = -1

    for product in recipe_data["products"]:
        if product['item'] == item:
            qty = product['amount']
            break
    
    if qty<0:
        raise ValueError(f'Could not find product {item} in recipe {recipe_data['className']}')
    
    return qty

def alter_itempool(itempool: dict[str, float], recipe_data: dict, machine_qty: float, key: Literal['products', 'ingredients'] | None = None):
    # Apply the effects of a recipe on the current itempool (substract the products, add the ingredients)
    # Must be used once as
    if key is None:
        itempool = alter_itempool(
            itempool, recipe_data, machine_qty, 'products')
        itempool = alter_itempool(
            itempool, recipe_data, machine_qty, 'ingredients')
    else:
        for product in recipe_data[key]:
            product_item = product['item']
            product_qty = 60 * machine_qty * \
                product['amount'] / recipe_data['duration']

            if product_item not in itempool:
                itempool[product_item] = 0
            if key == 'products':
                product_qty *= -1
            itempool[product_item] += product_qty

    return itempool


def get_production_plan(target_item: str, base_resources: set[str], recipes: dict[str, str] = {}, qty: float = 1.) -> tuple[dict]:
    # Contains steps
    production_plan = []
    production_plan.append({'itempool': {target_item: qty}})

    if qty <= 0:
        print('Cannot produce negative amount of items. Let us make 1 of these per minute')
        qty = 1

    itempool: dict[str, float]
    left_items: list[str]
    for i in range(1, MAX_ITER):  # change to while once we got the condition
        # Make room for current tier

        itempool = copy.deepcopy(production_plan[i-1]['itempool'])
        # next_itempool: dict[str: float] = copy.deepcopy(itempool) # questionable
        # on certain occasions, not separating the pools this will compress a recipe to one tier higher than it shoulde be
        # However, separating the pools may cause some error when a single recipe has a byproduct

        # how to handle the 1 tier up situation:
        # if the item you are currently treating is child of other items in the tier,
        # skip to compute on next tie
        #
        # do that during tier building or during plan refinement ?
        # the advantage of doing that during tier building is that we have left_items to refer to

        # List all items to produce in said tier
        left_items = [item_ for item_, qty_ in itempool.items()
                      if qty_ > EPSILON and item_ not in base_resources]

        if not left_items:
            # if no items are left to craft, exit loop (and dont make a next tier)
            break

        production_plan.append(
            {'itempool': {}, 'recipepool': {}, 'itemtorec': {}})

        for item in left_items:
            if item in recipes:
                recipe = recipes[item]
            else:
                recipe = selectRecipe(item)
                # this way any recipe that was not chosen is added to the dict
                recipes[item] = recipe

            if not recipe:
                base_resources.add(item)
                print(f'No available recipe for {data.data_items[item][0]['name']}. It has been added to base resources')
                continue

            production_plan[i]['itemtorec'][item] = recipe

            recipe_data = data.data_recipes[recipe][0]

            # decide number of machines for recipe: divide asked quantity by recipe rate (/min)
            machine_qty = itempool[item] / (60 * getProductQuantity(recipe_data, item) / recipe_data['duration'])

            # Alter recipe pool
            production_plan[i]['recipepool'][recipe] = machine_qty

            # Apply changes from recipe usage to item pool
            itempool = alter_itempool(itempool, recipe_data, machine_qty)

        if i == MAX_ITER-1:
            print(f'WARNING: Max recipe iterations reached. Looping may have occured.')

        # Remove items with quantity 0
        empty_items = [item_ for item_, qty_ in itempool.items() if abs(
            qty_) < EPSILON]  # Ignore items with too low of a quantity
        for empty_item in empty_items:
            itempool.pop(empty_item)

        production_plan[i]['itempool'] = itempool

    # Refine plan: concatenate recipes that appear several times to lowest tier
    for item, recipe in recipes.items():
        # Find all tiers where recipe appear
        tiers_recipe: list[int] = []
        recipetotal = 0
        for i, tier in enumerate(production_plan):
            # Count recipe qty
            if 'recipepool' in tier:
                if recipe in tier['recipepool']:
                    tiers_recipe.append(i)
                    recipetotal += tier['recipepool'][recipe]

        # Find all tiers where the item should appears (from the tier it is needed to the tier it is fulfilled)
        tiers_item: list[int] = []
        for i, tier in enumerate(production_plan):
            if 'itempool' in tier:
                if item in tier['itempool']:
                    tiers_item.append(i)

        # Push recipe down lowest
        if len(tiers_recipe) > 1:
            for i in tiers_recipe:
                production_plan[i]['recipepool'].pop(recipe)
                if item in production_plan[i]['itemtorec']: # item may not be in itemtorec if the recipe has the item as byproduct and has not been chosen for this purpose
                    production_plan[i]['itemtorec'].pop(item)
            production_plan[tiers_recipe[-1]]['recipepool'][recipe] = recipetotal
            production_plan[tiers_recipe[-1]]['itemtorec'][item] = recipe

        # Propagate item quantities
        itemtotal = 0
        if len(tiers_item) > 1:
            # do not touch the last tier where it appears
            for i in range(len(tiers_item)-1):
                plan = production_plan[i]
                if item not in plan['itempool']:
                    plan['itempool'][item] = 0
                plan['itempool'][item] += itemtotal
                itemtotal = plan['itempool'][item]

    return production_plan, recipes, base_resources

# --------------- V2 ---------------------
def createCustomRecipe(items: dict[str, float]) -> dict[str]:
    recipe_data: dict[str, list[dict[str]]] = {"ingredients": [], "products": [], "duration": 60}

    for item, amount in items.items():
        recipe_data["ingredients"].append({"item": item, "amount": amount})

    return recipe_data

class Node():
    """
    Graph node
    """
    id: str                         # name of the node
    depth: int                      # distance from top. guides order of execution
    type: Literal["recipe", "item"]
    children: dict[str, float]      # lists all children nodes and the item quantities
    parents: dict[str, float]       # lists all parent nodes and the item quantities
    activeparents: dict[str, float] # lists all parent nodes requesting this recipe and the recipe quantities
    graph: "Graph" 

    def __init__(self, id: str, depth: float, type: Literal["recipe", "item"]):
        # initialize here otherwise all nodes point to the same object
        self.children = {}
        self.parents = {}
        self.activeparents = {}

        self.id = id
        self.depth = depth
        self.type = type

    def flatten(self) -> dict[str]:
        return {"id": self.id, "depth": self.depth, "type": self.type, "children": self.children, "parents": self.parents, "activeparents": self.activeparents}

    def isOrphaned(self) -> bool:
        """
        Orphaned recipe: if it has no active parents
        Orphaned item: if it has no parents and no children
        """
        orphaned: bool = False
        if self.id != self.graph.start:
            if self.type == 'recipe':
                orphaned = float(sum(self.activeparents.values())) <= 0
            else:
                # is this wrong ?
                # try to think about a case where you would actually need to remove an item from here
                # you can delete a recipe, and then the item is recomputed using createChidren so all should be fine
                orphaned = len(self.children)==0 and len(self.parents)==0
        return orphaned

    def getRequired(self, key: str = '') -> float:
        """
        ITEMS:
            gives net required of quantities. Negative means excess items
            sums all parent amounts and substracts children amounts
            key allows to exclude a part of the children/parents
            result is given in items/min
        RECIPE:
            key is the item for which this recipe has been chosen
            as such, the requested key quantity decides of the recipe amount
            result is given in number of machines
        """
        total: float
        if self.type == "item":
            total = sum(self.parents.values()) - sum(self.children.values())
            if key in self.parents:
                total -= self.parents[key]
            if key in self.children:
                total += self.children[key]
        else:
            if key and key not in self.activeparents:
                raise ValueError(f'Item {key} is not in recipe {self.id} active parents')
            if key:
                total = self.activeparents[key]
            else:
                total = sum(self.activeparents.values())


        return float(total)
    
    def updateDepth(self):
        """
        items, in terms of availability, should be the deepest possible (its there as soon as its needed)
        on the other hand, recipes should come at the shallowest position (just before the deepest of its parents)
        """
        parentdepths: list[int]
        if self.type=='item':
            parentdepths = [node.depth for id, node in self.graph.nodes.items() if id in self.parents]
        else:
            parentdepths = [node.depth for id, node in self.graph.nodes.items() if id in self.activeparents]
        # newdepth: int

        if len(parentdepths) > 0:
            self.depth = max(parentdepths)+1

            # if self.type=='item':
            #     newdepth = max(parentdepths)
            # else:
            #     newdepth = min(parentdepths)
            # self.depth = newdepth+1
        else:
            self.depth = 0
    
    def updateDepthAndChildren(self, ancestry: list[str] = []):
        """
        Is this going to loop or am I smart as fuck ?
            it looped after a while :(
        what even is the purpose of this honestly
        """
        if len(ancestry) == MAX_ITER:
            raise ValueError('Looping !')
        if DEBUG:
            print(f'Updating depth for node {self.id}')

        newancestry: list[str] = ancestry.copy()
        newancestry.append(self.id)

        depth: int = self.depth
        self.updateDepth()
        if depth != self.depth or self.id not in ancestry:
            # force check all nodes once
            if DEBUG:
                print(f'\tDepth changed from {depth} to {self.depth}')
            for child in self.children:
                self.graph.nodes[child].updateDepthAndChildren(newancestry)

    def disconnectChild(self, child: str):
        self.children.pop(child)
        self.graph.nodes[child].parents.pop(self.id)

    def connectChild(self, child: str, itemamount: float, recamount: float, active: bool):
        """
        create relations between self and child. maybe add some checks to this
        """
        node: Node = self.graph.nodes[child]
        if itemamount > 0:
            self.children[child] = itemamount
            node.parents[self.id] = itemamount
        else:
            self.children.pop(child)
            node.parents.pop(self.id)

        if active and self.type=='item':
            if recamount > 0:
                # indicate to recipe the reason for which its been created
                node.activeparents[self.id] = recamount
            else:
                node.activeparents.pop(self.id)

    def createChild(self, type: Literal["recipe", "item"], id: str, itemamount: float, recamount: float, ancestry: list[str] = []):
        """
        itemamount in items/min
        recamount in number of machines. equal to 0 if self is recipe
        """
        node: Node
        newnode: bool = id not in self.graph.nodes
        nonpos: bool = itemamount < EPSILON

        debugamount: float = itemamount if type=='item' else recamount

        if newnode and nonpos:
            # if node doesnt exist and requested negative quantity, do nothing
            if DEBUG:
                print(f'Needed child amount of {id} for node {self.id} is non positive ({debugamount})')
            return
        elif newnode:
            # new node positive
            if DEBUG:
                print(f'Creating node {id}, child of {self.id} (amount {debugamount})')
            node = Node(id, self.depth+1, type) # create node
            self.graph.addNode(node) # add it to graph
        elif nonpos:
            pass
            # connectChild will handle the removal of active parents for recipe
        else:
            if DEBUG:
                print(f'Found node {id} to be child of {self.id} (amount {debugamount})')
            node = self.graph.nodes[id]
        
        self.connectChild(id, itemamount, recamount, True) # update family
        if not nonpos:
            node.createChildren(ancestry) # update its children (recurse)
        # if the recipe is negative, dont create its children
        # item quantity cannot be negativ

    def createParent(self, type: Literal["recipe", "item"], id: str, amount: float, ancestry: list[str] = []):
        node: Node
        newnode: bool = id not in self.graph.nodes
        if type=='recipe':
            raise ValueError('Item cannot create its parent recipe')
        if newnode:
            if DEBUG:
                print(f'Creating node {id}, parent of {self.id} (amount {amount})')
            node = Node(id, 0, type) # create node
            self.graph.addNode(node) # add it to graph
        else:
            if DEBUG:
                print(f'Found node {id} to be parent of {self.id} (amount {amount})')
            node = self.graph.nodes[id]

        node.connectChild(self.id, amount, 0, False) # create family
        node.createChildren(ancestry) # children can be created without worry - if you are creating the parent, it means the created parent is byproduct of the current recipe, hence will not loop back to this recipe to be created

    def createChildren(self, ancestry: list[str]):
        father: str = ''
        if len(ancestry) > 0:
            father = ancestry[-1]
        # --- ERROR AND DEBUGS ---
        message: str
        if (self.id in ancestry):
            index: int = ancestry.index(self.id)
            looped: list[str] = ancestry[index:]
            
            print(f'Family tree is looping for nodes {', '.join(looped)}. Resetting active recipes and recomputing node')
            
            for id in looped:
                # reset all active recipes for problematic items
                if self.graph.nodes[id].type=='item' and id in self.graph.recipes:
                    self.graph.recipes.pop(id)
            
            self.graph.nodes[looped[0]].connectChild(looped[1], 0, 0, True) # Looping will be detected on an item. sever its recipe
            self.graph.nodes[looped[0]].createChildren(ancestry[:index]) # recompute item
            
            # return

        if len(ancestry) == MAX_ITER-1:
            message = f'Max recipe iterations reached. Looping may have occured\n\tStopped at node {self.id}. Parents: {', '.join(ancestry)}'
            if ERROR_ON_WARNING:
                raise ValueError(message)
            else:
                print(f'WARNING: {message}')
                return

        if DEBUG:
            self.graph.show()

            print(f'Evaluating children for node {self.id} ({self.type}), called from node {father}')

        # --- PROCESSING ---
        newancestry: list[str] = ancestry.copy()
        newancestry.append(self.id)

        total: float # item / min
        if self.type=="item":
            if self.id not in self.graph.baseresource: # only try to create a child if its not a base resource
                if self.id in self.graph.recipes:
                    recipe = self.graph.recipes[self.id]
                else:
                    recipe = selectRecipe(self.id)
                    self.graph.recipes[self.id] = recipe
                
                if DEBUG:
                    print(f'\tSelected recipe {recipe} for item {self.id}')

                total = self.getRequired(recipe)
                current: float = 0 # item / min
                if recipe in self.children:
                    current = self.children[recipe]

                if total != current:
                    if recipe:
                        recipe_data = data.data_recipes[recipe][0]
                        rectotal: float = recipe_data['duration'] * total / (60 * getProductQuantity(recipe_data, self.id)) # number of machines
                        self.createChild('recipe', recipe, total, rectotal, newancestry)
                    else:
                        if DEBUG:
                            print(f'\tCould not find recipe for item {self.id}. Adding to base resource')
                        self.graph.baseresource.add(self.id) # add it to base resource if no recipe is available
                elif DEBUG:
                    print(f'Item {self.id} is balanced')
            elif DEBUG:
                print(f'\tItem {self.id} is a base resource. Stopping research')
        else:
            total = self.getRequired() # number of machines

            if total < 0:
                raise ValueError(f'Tried to compute children for negative amount ({total}) of recipe {self.id}. This should not happen')

            if self.id == self.graph.start:
                recipe_data = self.graph.target
            else:
                recipe_data = data.data_recipes[self.id][0]

            comp: dict[str]
            item: str
            amount: float # item / min
            for comp in recipe_data['ingredients']:
                item = comp['item']
                amount = float(60.0 * comp['amount'] * total / recipe_data['duration'])
                self.createChild('item', item, amount, 0, newancestry)
            
            for comp in recipe_data['products']:
                item = comp['item']
                amount = float(60.0 * comp['amount'] * total / recipe_data['duration'])
                if item != father: # dont try to create calling node
                    self.createParent('item', item, amount, newancestry)

class Graph(): 
    """
    Graph
    """
    start: str = 'start'
    nodes: dict[str, Node]

    target: dict[str] # list of items to produce and their quantity as a custom recipe

    baseresource: set[str]
    recipes: dict[str, str]

    # DEBUG display
    colormap: dict[str, str] = {
        'start': '#55016e',
        'item': '#a30303',
        'recipe': '#01036e',
        'extra': "#ac0078",
        'end': '#a34e03'
    }

    # computing methods

    def __init__(self, target: dict[str] = {}, baseresource: set[str] = set(), recipes: dict[str, str] = {}):
        # initialize here otherwise all graphs will refer to the same object
        self.nodes = {}
        self.recipes = {}
        if target:
            self.setTarget(target)
        else:
            self.target = {}
        if baseresource:
            self.baseresource = baseresource
        else:
            self.baseresource = data.data_baseresources.copy()
        if recipes:
            self.recipes = recipes

        self.addNode(Node(self.start, 0, 'recipe'))
        self.nodes[self.start].activeparents = {'graph': 1}

        if DEBUG:
            print('Initiating graph')

    def setTarget(self, target: dict[str]):
        if DEBUG:
            print(f'Setting target(s):\n\t{', '.join([f'{item}: {amount}' for item, amount in target.items()])}')
        self.target = createCustomRecipe(target)
    
    def addNode(self, node: Node):
        node.graph = self
        self.nodes[node.id] = node

    def deleteNode(self, id: str):
        if DEBUG:
            print(f'\tRemoving node {id}')

        if id in self.nodes:
            children: list[str] = list(self.nodes[id].children) # create a separate object to iterate on
            for child in children:
                self.nodes[id].disconnectChild(child)
                if self.nodes[child].isOrphaned():
                    self.deleteNode(child)
                else:
                    self.nodes[child].createChildren([id]) # recompute child ?

            self.nodes.pop(id)
        else:
            if DEBUG:
                print('\t\tNode does not exist anymore')

    def cleanOprhaned(self):
        # non required nodes are nodes who have parents but the required value was set to 0
        if DEBUG:
            print('Checking orphaned and non required nodes:')

        orphaned: list[str] = []

        for id, node in self.nodes.items():
            if node.isOrphaned():
                orphaned.append(id)

        if DEBUG and len(orphaned)==0:
            print('\tNo orphaned nodes')

        for id in orphaned:
            self.deleteNode(id)

    def getBalance(self, filt: Literal['positive', 'negative', 'all'] = 'all') -> dict[str, float]:
        """
        filt (filter):
            positive: only input quantities
            negative: only extra resource
        """
        balance: dict[str, float] = {}
        amount: float
        for id, node in self.nodes.items():
            if node.type =='item':
                amount = node.getRequired()
                if ((filt=='positive' and amount > 0)
                    or (filt=='positive' and amount < 0)
                    or filt=='all'):
                    balance[id] = amount
        return balance

    def getUnbalanced(self) -> list[str]:
        if DEBUG:
            print('Checking node balance...')
        
        unbalanced: list[str] = []
        balance = self.getBalance()
        for id, amount in balance.items():
            if amount > 0 and id not in self.baseresource:
                unbalanced.append(id)
                if DEBUG:
                    print(f'\tNode {id} has a balance of {balance[id]:+}')

        if DEBUG and len(unbalanced)==0:
            print('\tAll nodes are balanced !')

        return unbalanced
    
    def compute(self, fromnode: str = 'start'):
        if DEBUG:
            print(f'Computing graph from node {fromnode}')
        if fromnode not in self.nodes:
            raise ValueError(f'Node {fromnode} does not exist in this graph')
        
        unbalanced: list[str] = [fromnode]
        i: int = 0
        while len(unbalanced) > 0 and i < MAX_ITER:
            if DEBUG:
                print(f'Computing round number {i}')
            self.nodes[unbalanced[0]].createChildren([]) # start of computation has no parent

            self.cleanOprhaned()

            unbalanced: list[str] = self.getUnbalanced()
            if DEBUG:
                print(f'Unbalanced nodes at round {i}: {', '.join(unbalanced)}')
            i += 1
        if i >= MAX_ITER:
            message: str = f'Could not balance graph after {MAX_ITER} attempts: {', '.join(unbalanced)}'
            if (ERROR_ON_WARNING):
                raise ValueError(message)
            else:
                print(f'WARNING: {message}')

        self.nodes[fromnode].updateDepthAndChildren()

        topop: list[str] = []
        for item in self.recipes: # remove items that disappeared
            if item not in self.nodes:
                topop.append(item)

        print(f'Removing unused recipes: {', '.join(topop)}')

        for item in topop:
            self.recipes.pop(item)

        if DEBUG:
            print('Graph computation completed')

    def alterRecipe(self, item: str, recipe: str, recompute: bool = True):
        if DEBUG:
            print(f'Setting recipe for item {item} to {recipe}')

        # if item not in self.nodes:
        #     raise ValueError(f'Item {item} is not part of this plan')
        
        hasnode: bool = item in self.recipes
        oldrecipe: str
        if hasnode:
            oldrecipe = self.recipes[item]

        self.recipes[item] = recipe

        if item in self.baseresource:
            self.baseresource.pop(item)
        
        if recompute:
            if hasnode:
                self.nodes[item].connectChild(oldrecipe, 0, 0, True) # remove item from old recipe active parents
                if self.nodes[oldrecipe].isOrphaned(): # delete old recipe or recompute it
                    self.deleteNode(oldrecipe)
                else:
                    self.nodes[oldrecipe].createChildren([item])

            self.compute(item) # recompute children for item

    # interface methods
    def flatten(self) -> dict[str]:
        flat: dict[str] = {"start": self.start, "target": self.target, "baseresource": list(self.baseresource), "recipes": self.recipes, "nodes": {}}
        for id, node in self.nodes.items():
            flat["nodes"][id] = node.flatten()
        return flat

    def show(self, block: bool = False):
        if __name__!='__main__':
            return
        plt.clf()

        G = nx.Graph()

        node: Node
        child: str
        amount: float
        color: str
        label: str
        for node in self.nodes.values(): # first add all nodes
            if node.id == self.start:
                color = self.colormap['start']
            elif len(node.parents) == 0:
                color = self.colormap['extra']
            elif node.id in self.baseresource:
                color = self.colormap['end']
            else:
                color = self.colormap[node.type]
            label = node.id
            if node.type=='recipe':
                label += f' ({sum(node.activeparents.values()):2f})'
            G.add_node(node.id, color=color, label=label, depth=node.depth)

        for node in self.nodes.values(): # then add all connections
            for child, amount in node.children.items():
                G.add_edge(node.id, child, label=amount)

        # pos = nx.multipartite_layout(G, subset_key="depth", align='horizontal')
        # pos = {n: (x, -y) for n, (x, y) in pos.items()} # manually make it top down
        pos = nx.spring_layout(G)

        colors = [data["color"] for _, data in G.nodes(data=True)]
        node_labels = nx.get_node_attributes(G, "label")
        nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=[len(node_labels[i])**2 * 60 for i in pos])
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, pos, node_labels, font_color='white')

        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        plt.tight_layout()
        plt.axis("off")
        plt.show(block=block)

    def getDepth(self) -> int:
        maxdepth: int = 0
        for node in self.nodes.values():
            maxdepth = max(node.depth, maxdepth)
        return maxdepth

    def getNodes(self, depth: int) -> list[Node]:
        nodes: list[Node] = []
        for node in self.nodes.values():
            if node.depth == depth:
                nodes.append(node)
        return nodes

def example_run_old():
    production_plan, recipes = get_production_plan(
        'Desc_NuclearFuelRod_C', data.data_baseresources)
    # data.pretty_dict_print(production_plan)
    print(production_plan)

    path = 'output\\test.html'
    if not os.path.exists('output'):
        os.mkdir('output')
    # htmlreport.generate_html(production_plan, path)
    # webbrowser.open(path)

def example_run(debug: bool = True):
    global DEBUG
    DEBUG = debug

    target: dict[str] = {"Desc_AluminumIngot_C": 120}
    # target: dict[str] = {"Desc_Plastic_C": 120}
    # target: dict[str] = {"Desc_ModularFrame_C": 10}
    # target: dict[str] = {"Desc_ModularFrameHeavy_C": 12, "Desc_ModularFrame_C": 30}

    graph = Graph(target)

    start = time.time()
    graph.compute()
    end = time.time()
    # graph.alterRecipe('Desc_ModularFrame_C', 'Recipe_Alternate_ModularFrame_C') # place recipe change here

    end2 = time.time()
    
    print('Execution time: %s s'%(end-start))
    print('Recompute time: %s s'%(end2-end))
    print('Total time: %s s'%(end2-start))
    print('Travail terminé')
    utils.pretty_dict_print(graph.flatten())
    graph.show(True)

def computevsrecompute():
    import json
    
    target: dict[str] = {"Desc_ModularFrame_C": 10}
    
    graph1 = Graph(target)
    graph1.compute()
    graph1.alterRecipe('Desc_ModularFrame_C', 'Recipe_Alternate_ModularFrame_C', True)

    graph2 = Graph(target)
    graph2.alterRecipe('Desc_ModularFrame_C', 'Recipe_Alternate_ModularFrame_C', False)
    graph2.compute()

    with open('output\\graph1.json', 'w') as f:
        json.dump(graph1.flatten(), f)
    with open('output\\graph2.json', 'w') as f:
        json.dump(graph2.flatten(), f)



### Main code ###
if __name__ == '__main__':
    # example_run()
    # import json

    # payloadstr = """
    #     {"item": "Desc_AluminumIngot_C", "recipes": {"Desc_AluminaSolution_C": "Recipe_AluminaSolution_C", "Desc_AluminumIngot_C": "Recipe_IngotAluminum_C", "Desc_AluminumScrap_C": "Recipe_AluminumScrap_C", "Desc_Silica_C": "Recipe_Silica_C"}, "baseresource": ["Desc_Silica_C"]}
    # """
    # payload = json.loads(payloadstr)
    # item = payload['item']
    # recipes = payload['recipes']
    # baseresource = set(payload['baseresource'])

    # production_plan: dict
    # production_plan, recipes = get_production_plan(
    #     item, baseresource, recipes, 100)
    
    # print(production_plan)

    example_run()

    # computevsrecompute()
