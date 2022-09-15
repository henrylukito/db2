# db2

Python module to manage a folder of YAML files as a (graph) database. Load data from YAML files into dicts, and save changes to dicts back to YAML files.


## How to load database

Call `load('path-to-db-folder')`. If path doesn't exist, it will be created along with starting subdirectories and files. db2 dicts such as `node`, `col`, `prop` will be populated with data from YAML files.


## How to save database

Calls to db2 functions such as `setnode`, `remcol`, `renameprop` will save changes back to YAML files.


## What is col?

It stands for collection. A collection is a subset list of nodes. The same node can exist in multiple collections. Might be known as label, tag, group or set in other systems.


## What is the difference between `col` and `nodecol` dicts?

The keys for `col` dict are col ids, while the keys for `nodecol` are node ids.

So `col` dict can be used to find all nodes in a collection while `nodecol` dict is to find all collections a node is in.

Similar pattern applies to other pairs of dicts like `prop` and `nodeprop`, `rel` and `noderel` etc.


## What is the difference between `rel`, `backrel`, `noderel`, `nodebackrel`, `nodetarget`, `nodesource`?

For a particular instance of relationship between a source node and a target node, there is a property dict for it.

This dict can be accessed by `rel[relid][sourceid][targetid]`

But it can also be accessed by:

backrel: `backrel[relid][targetid][sourceid]`

noderel: `noderel[sourceid][relid][targetid]`

nodebackrel: `nodebackrel[targetid][relid][sourceid]`

nodetarget: `nodetarget[sourceid][targetid][relid]`

nodesource: `nodesource[targetid][sourceid][relid]`

Only `rel` is saved to YAML file. The rest are computed from `rel`.

`rel[relid]` and `backrel[relid]` can be used to list all the sources and targets of a relationship respectively.

`noderel[sourceid]` and `nodebackrel[targetid]` can be used to list node's all outgoing and incoming relationships respectively.

`nodesource[targetid]` and `nodetarget[sourceid]` can be used to list all nodes linked to a node (regardless of specific relationships), and for each link finds out which relationships link them.


## How to edit nodes/collections/properties/relationships?

To add/update, call functions that begin with `set` like `setnode`, `setnodecol`, `setnodeprop` etc.

To remove, call functions that begin with `rem` like `remnode`, `remnodecol`, `remnodeprop` etc.

To rename, call functions that begin with `rename` like `renamenode`, `renameprop`, `renamerel` etc.

These functions will update the files immediately and keep the dict objects consistent.

The `set` functions will generally add elements (e.g., node, col, prop) if they don't already exist, instead of throwing errors.

The `rem` functions will generally remove collections, properties or relationships that have become empty (i.e., not associated to any node) and also delete their YAML files (but not empty nodes).


## Quick way to set nodes/properties/relationships

There is a function `inputnode` that, if you pass no argument, will keep looping for user input until it's keyboard interrupted (ctrl+c).

The function will do something based on each input statement.

The statement has a certain syntax:

Add a node:

`slime`

If node already exists, nothing is done (no error is thrown, and node not reset to empty node).

Add a node and put into a collection:

`slime:monster`

If the collection doesn't exist, it will be created.

You can put node in multiple collections at once like this:

`slime:monster:pet`

Add property to node:

`slime.health=100`

Again if the property doesn't exist, it will be created.

Add multiple properties:

`slime.health=100,element='water'`

Note the property values are `eval`ed, that's why string values need to be quoted.

You can combine adding collections and properties:

`slime:monster:pet.health=100,element='water'`

Add relationship:

`slime>drops>potion`

You can add property to the relationship:

`slime>drops.probability=0.5>potion`

Nodes that do not exist, including the nodes in relationship target, will be created.

You can add multiple relationship targets like this:

`slime>drops.probability=0.5>potion;jelly`

This means slime drops potion and jelly at the same 0.5 probability.

But if slime drops jelly at different probability, it should be specified separately:

`slime>drops.probablity=0.5>potion`

`slime>drops.probability=0.1>jelly`

In fact you can also specify multiple sources like this:

`slime;goblin>drops.probability=0.5>potion;jelly`

But this means both these monsters drop the same set of items and at same probability for both items

Even though complex statements are technically possible, e.g.:

`slime:monster.health=100,elem='water'>drops>potion:item:healingitem.sellprice=50;jelly:item:material:food.sellprice=100,stomach=0.1`

`inputnode` is meant for iterating quickly with shorter statements like this:

`slime:monster`

`slime.health=100`

`slime.elem='water'`

`slime>drops>potion;jelly`

`potion:item:healingitem`

`potion.sellprice=50`

`jelly:item:material.sellprice=100`

`jelly:food.stomach=0.1`


## How to ensure nodes/relationships have certain properties?

You can specify what properties a node under a certain collection should have with `setcolprop`. The dict object is `colprop` and YAML file is `collectionproperties.yml`.

There's a special function called `fillcolprop`, which when called will search for nodes in that collection that do not yet have that property, and prompt user for the property value, which will then be saved.

The equivalent for relationship is `relprop`.


## How to use/analyze these objects once they're loaded?

The module currently doesn't extend its scope much beyond editing and ensuring the dict objects and data files are in sync.

To start with, you can use various Python features to query the dict objects like a database (e.g., list comprehension). You might want to define your own helper/convenience functions to ease the syntax.

### Examples:

List all nodes:

`list(node)`

List all collections:

`list(col)`

List all nodes in monster collection:

`list(col['monster'])`

Count number of nodes in monster collection:

`len(col['monster'])`

List all nodes not in any collection:

`[nodeid for nodeid in node if nodeid not in nodecol]`

List all collections slime is in:

`list(nodecol['slime'])`

Check if there's a node called slime:

`'slime' in node`

Check if slime is in monster collection:

`'slime' in col['monster']`

Display all slime properties:

`nodeprop['slime']`

List all water element monsters:

`[monster for monter in col['monster'] if nodeprop.get('monster', {}).get('elem') == 'water']`

List all monsters that are also in pet collection (2 collections):

`[monster for monster in col['monster'] if 'pet' in nodecol.get(monster, {})]`

List all nodes that are in 3 or more certain collections:

`[nodeid for nodeid in node if {'monster', 'pet', 'npc'}.issubset(nodecol.get(node, {}))]`

Display all monster health if they have health property:

`{nodeid : nodeprop[nodeid]['health'] for nodeid in col['monster'] if 'health' in nodeprop.get(nodeid, {})}`

Display all monster that do not have health property yet:

`[nodeid for nodeid in col['monster'] if 'health' not in nodeprop.get(nodeid, {})]`


## How to decide whether to use collection, property or relationship?

Collection is more binary than a boolean property; a node is either in collection or not. In contrast, with boolean property there exists 3 possibilites with a node: Either the node has the property and its value is either true or false, or the node doesn't have the property.

With relationship it's easier to look at the other side. For example, monsters drops items. If we want to know all the monsters that drop a specific item, it's easier to do with `backrel` which has been precomputed. But it's also not that hard to compute on demand with property.

Relationship can also have properties (property dict).
