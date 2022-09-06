# db2

Script to help you to manage a folder of YAML files that can be loaded as objects that represent graph database.

## How to create folder with starting files

Call `load(dbname)`. A folder named `dbname` will be created on current working directory.


## Load objects

Also call `load(dbname)`. This module's dict objects such as `node`, `col`, `prop`, `rel`, `nodecol`, `nodeprop`, `noderel` etc will be populated.


## What is col?

It stands for collection. A collection is just a way to have a subset list of nodes. A node can be in multiple collections.


## What is the difference between `col` and `nodecol`?

The keys for `col` dict are col ids, while the keys for `nodecol` are node ids.

You use `col` dict to find out what nodes are in a collection and `nodecol` dict to find out all collections a node is in.

The same applies to other pairs like `prop` and `nodeprop`, `rel` and `noderel` etc.


## How to add/remove nodes/properties/relationships?

Call functions like `setnode`, `setnodecol`, `setnodeprop`, `setnoderel` etc.

The counterparts for removal are `remnode`, `remnodecol`, `remnodeprop`, `remnoderel` etc.

These functions will update the files if there are changes. They also ensure the dict objects remain consistent, e.g., between `col` and `nodecol`.

These functions will add nodes, properties etc if they don't already exist, instead of being strict by throwing errors.


## How to add nodes/properties/relationships quickly?

There is a function `qset` (quick set) that will keep asking user for input until `q` is typed.

The input has certain syntax:

Add a node:

`slime`

If node already exists, nothing will happen (no duplicate is created).

Add a node and put into a collection:

`slime:monster`

If the collection doesn't yet exist, it will be created.

You can put the node in multiple collections at once like this:

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

And just like above examples, it can be combined with adding collections and properties:

`slime:monster:pet.health=100,element='water'>drops.probability=0.5>potion:healingitem.sellprice=50`

You can add multiple relationship targets like this:

`slime>drops>potion;jelly`

In fact you can also specify multiple sources like this:

`slime;goblin>drops>potion;jelly`

It means both these monsters drop the same set of items.

Even though complex statements are possible, e.g.:

`slime:monster.health=100>drops>potion:healingitem.sellprice=50;jelly:food.sellprice=100,hungerfill=0.1`

it might be more intuitive to iterate with shorter statements like this:

`slime:monster`

`slime.health=100`

`slime>drops>potion;jelly`

`potion:healingitem.sellprice=50`

`jelly:food.sellprice=100`

`jelly.hungerfill=0.1`

Note if slime drops potion and jelly at different probabilites, it has to be specified separately:

`slime>drops.probability=0.5>potion`

`slime>drops.probability=0.2>jelly`

The syntax for adding property to relationship is admittedly more annoying than others.


## What to do after loading objects?

Currently the script doesn't take care much about querying.

You can use Python list constructor, in statement, list comprehension and dict comprehension etc on the dict objects to query like a database.

`list(node) # list all nodes`

`list(col['monster']) # list all monsters (all nodes in monster collection)`

`'slime' in col['monster'] # check if there's slime in monster collection`

`[nodeid for nodeid in node if nodeid in col['monster'] and nodeid in col['pet']] # list all nodes that exist in both monster and pet collection`

`{nodeid : nodeprop[nodeid]['health'] for nodeid in col['monster'] and 'health' in nodeprop[nodeid]} # list all monster health values (if it has health property)`

`{nodeid : [item for item in noderel[nodeid]['drops'] if item in col['material]] for nodeid in col['monster'] and 'drops' in noderel[nodeid]} # list all monster drops that are material items (i.e., not healing or other items)`
