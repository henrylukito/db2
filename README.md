# db2

Python module to help manage a folder of YAML files as a (graph) database. The data from YAML files can be loaded in Python program as dict objects, and editing these dict objects with provided functions will also update the YAML files.


## How to create new database

Call `load('path-to-db-folder')`. A folder named `path-to-db-folder` will be created according to the path name if it doesn't yet exist, together with some starting subfolders and files. The database will also be loaded (see below).


## How to load dict objects from YAML files

Call `load('path-to-db-folder')`. This module's dictionary objects such as `node`, `col`, `prop`, `rel` etc will be populated according to data from the files.


## How to save dict objects to YAML files

After you load the database, call to edititing functions such as `setnode`, `remcol`, `renameprop` etc will save the changes back to YAML files.


## What is col?

It stands for collection. A collection is just a way to have a subset list of nodes. Same node can exist in multiple collections.


## I see something like `col` and `nodecol` dicts. What is the difference?

The keys for `col` dict are col ids, while the keys for `nodecol` are node ids.

You use `col` dict to find out all nodes in a collection while `nodecol` dict is to find out all collections a node is in.

This pattern applies to other pairs of dicts like `prop` and `nodeprop`, `rel` and `noderel` etc.


## What is the difference between `rel`, `backrel`, `noderel`, `nodebackrel`, `nodetarget`, `nodesource`?

For a particular relationship instance between a source node and a target node, there is a property dict for that relationship instance.

The same relationship property dict can be accessed via 6 different dicts.

How the 6 dicts differ is the keys required to get to access property dict:

rel : `rel[relid][sourceid][targetid]`

backrel: `backrel[relid][targetid][sourceid]`

noderel: `noderel[sourceid][relid][targetid]`

nodebackrel: `nodebackrel[targetid][relid][sourceid]`

nodetarget: `nodetarget[sourceid][targetid][relid]`

nodesource: `nodesource[targetid][sourceid][relid]`

Only `rel` is saved to YAML file. The rest are derived from `rel`.

`rel[relid]` and `backrel[relid]` can be used to list all the sources and targets of a relationship respectively.

To list all relationships a node has, `noderel[sourceid]`

To list all relationships a node is 'backlinked to'/'a target of', `nodebackrel[targetid]`

If you want to know all the nodes a node links to (without caring which relationship), `nodetarget[sourceid]`. Then `nodetarget[sourceid][targetid]` lists all the relationships which link the 2 nodes (they might be linked by more than 1 relationship).

## How to edit nodes/collections/properties/relationships?

To add/update, call functions that begin with `set` like `setnode`, `setnodecol`, `setnodeprop` etc.

To remove, call functions that begin with `rem` like `remnode`, `remnodecol`, `remnodeprop` etc.

To rename, call functions like begin with `rename` `renamenode`, `renameprop`, `renamerel` etc.

These functions will update the files immediately and keep the dict objects consistent.

The `set` functions will generally add elements (e.g., node, col, prop) if they don't already exist, instead of throwing errors.

The `rem` functions will generally remove elements that have become empty (i.e., not associated to any node) (e.g., col, prop, and rel) and will also delete their YAML files.


## Quick way to set nodes/properties/relationships

There is a function `quickset` that, if you pass no argument, will keep looping for user input until it's keyboard interrupted (ctrl+c).

The function will do something based on each user input statement.

The statement should follow certain syntax:

Add a node:

`slime`

If node already exists, nothing will happen (no error is thrown).

Add a node and put into a collection:

`slime:monster`

If the collection doesn't yet exist, it will be created.

You can put node in multiple collections at once like this:

`slime:monster:pet`

Add property to node:

`slime.health=100`

Again if the property doesn't yet exist, it will be created.

Add multiple properties:

`slime.health=100,element='water'`

Note the property values are `eval`ed, that's why string values need to be quoted.

You can combine adding collections and properties:

`slime:monster:pet.health=100,element='water'`

Add relationship:

`slime>drops>potion`

You can add property to the relationship:

`slime>drops.probability=0.5>potion`

Nodes that do not yet exist, including relationship targets, will be created.

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

`quickset` is meant for iterating quickly with shorter statements like this:

`slime:monster`

`slime.health=100`

`slime.elem='water'`

`slime>drops>potion;jelly`

`potion:item:healingitem`

`potion.sellprice=50`

`jelly:item:material.sellprice=100`

`jelly:food.stomach=0.1`


## How to ensure nodes/relationships have certain properties?

You can specify what properties a node under a certain collection should have with `setcolprop`. Dictionary object is `colprop` and YAML file is `collectionproperties.yml`.

By calling `fillcolprop`, the function will search for nodes under the collection that do not yet have that property, and prompt user for the property value, which will then be saved.

Equivalent for relationship is `relprop`. By calling `fillrelprop`, it will search all relationship instances (i.e., between different source node and target node) that do not yet have the property, and prompt user for the property value.


## How to use these objects once they're loaded?

Aside from editing and ensuring the files and dict objects are consistent, the module currently doesn't do much when it comes to querying/data analysis.

To start with, you can use various Python features to query the dict objects like a database. Then you can define helper/convenience functions.

### Examples:

List all nodes:

`list(node)`

List all collections:

`list(col)`

List all nodes in monster collection:

`list(col['monster'])`

Count number of nodes in monster collection:

`len(col['monster'])`

List all collections slime is in:

`list(nodecol['slime'])`

Check if there's a node called slime:

`'slime' in node`

Check if slime is in monster collection:

`'slime' in col['monster']`

Display all slime properties:

`nodeprop['slime']`

List all water element monsters:

`[monster for monter in col['monster'] if nodeprop[monster].get('elem') == 'water']`

List all monsters that are also in pet collection (2 collections):

`[monster for monster in col['monster'] if 'pet' in nodecol.get(monster, {})]`

List all nodes that are in 3 or more certain collections:

`[nodeid for nodeid in node if {'monster', 'pet', 'npc'}.issubset(nodecol.get(node, {}))]`

Display all monster health if they have health property:

`{nodeid : nodeprop[nodeid]['health'] for nodeid in col['monster'] if 'health' in nodeprop.get(nodeid, {})}`

Display all monster that do not have health property yet:

`[nodeid for nodeid in col['monster'] if 'health' not in nodeprop.get(nodeid, {})]`
