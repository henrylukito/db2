# db2

Python module to help manage a folder of YAML files as a (graph) database. The data from YAML files can be loaded in Python program as dict objects, and editing these dict objects with provided functions will also update the YAML files.


## How to create new database

Call `load('path-to-db-folder')`. A folder named `path-to-db-folder` will be created according to the path name if it doesn't yet exist, together with some starting subfolders and files. The database will also be loaded (see below).


## How to load dict objects from YAML files

Call `load('path-to-db-folder')`. This module's dictionary objects such as `node`, `col`, `prop`, `rel` etc will be populated according to data from the files.


## How to save dict objects to YAML files

After you load the database, any call to provided functions such as `setnode`, `setnodeprop`, `remnode` etc will save the changes to YAML files.


## What is col?

It stands for collection. A collection is just a way to have a subset list of nodes. Same node can exist in multiple collections.


## I see something like `col` and `nodecol` dicts. What is the difference?

The keys for `col` dict are col ids, while the keys for `nodecol` are node ids.

You use `col` dict to find out all nodes in a collection and `nodecol` dict to find out all collections a node is in.

This pattern applies to other pairs of dicts like `prop` and `nodeprop`, `rel` and `noderel` etc.


## How to edit nodes/collections/properties/relationships?

To add/update, call functions that begin with `set` like `setnode`, `setnodecol`, `setnodeprop` etc.

To remove, call functions that begin with `rem` like `remnode`, `remnodecol`, `remnodeprop` etc.

To rename, call functions like begin with `rename` `renamenode`, `renameprop`, `renamerel` etc.

These functions will update the files immediately and keep the dict objects consistent.

The `set` functions will generally add nodes, collections, properties etc if they don't already exist, instead of throwing errors.

The `rem` functions will generally remove collections, properties, relationships etc that have become empty and will also delete their YAML files.


## Quicker way to add nodes/properties/relationships

There is a function `quickset` that, if you pass no argument, will keep looping for user input until it's keyboard interrupted (ctrl+c).

The function will do something based on each user input statement.

The statement has certain syntax:

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

Add multiple properties:

`slime.health=100,element='water'`

Note the property values are `eval`ed, that's why string values need quotes.

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

It means both these monsters drop the same set of items and both at same probability for both items

Even though complex statements are possible, e.g.:

`slime:monster.health=100.elem='water'>drops>potion:item:healingitem.sellprice=50;jelly:item:material:food.sellprice=100,hungerfill=0.1`

`quickset` is meant for iterating quickly with shorter statements like this:

`slime:monster`

`slime.health=100`

`slime.elem='water'`

`slime>drops>potion;jelly`

`potion:item:healingitem`

`potion.sellprice=50`

`jelly:item:material.sellprice=100`

`jelly:food.hungerfill=0.1`


# How to ensure nodes/relationships have certain properties?

You can specify what properties a node under a certain collection should have with `setcolprop`. Object is `colprop` and YAML file is `collectionproperties.yml`.

By calling `fillcolprop`, the function will search for nodes under the collection that do not have the property yet, and prompt user for property value.

Equivalent for relationship is `relprop`. By calling `fillrelprop`, it will search all relationship instances, and prompt user for property value.


## How to use these objects once they're loaded?

Aside from editing nodes/properties/relationships etc, and ensure the files and the dicts are consistent, currently the script doesn't help much when it comes to querying the objects.

You can use Python features like list constructor, in operator, list comprehension and dict comprehension etc on the dict objects to query like a database.

`list(node) # list all nodes`

`list(col['monster']) # list all monsters (all nodes in monster collection)`

`'slime' in col['monster'] # check if there's slime in monster collection`

`[nodeid for nodeid in node if nodeid in col['monster'] and nodeid in col['pet']] # list all nodes that exist in both monster and pet collection`

`{nodeid : nodeprop[nodeid]['health'] for nodeid in col['monster'] and 'health' in nodeprop[nodeid]} # list all monster health values (if it has health property)`

`{nodeid : [item for item in noderel[nodeid]['drops'] if item in col['material]] for nodeid in col['monster'] and 'drops' in noderel[nodeid]} # list all monster drops that are material items (i.e., not healing or other items)`
