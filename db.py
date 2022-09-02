from pathlib import Path
import yaml


dbpath = None

nodes = {}
collections = {}

nodecollections = {}


class NodeExistError(Exception): pass
class NodeNotExistError(Exception): pass
class CollectionExistError(Exception): pass
class CollectionNotExistError(Exception): pass


def nodespath():
  return dbpath / 'nodes.yml'


def collectionpath(collectionid):
  return dbpath / 'collections' / (collectionid + '.yml')


def clear():

  global dbpath

  dbpath = None

  nodes.clear()
  collections.clear()

  nodecollections.clear()


def use(dirpath):

  clear()

  global dbpath
  global nodes

  dbpath = Path(dirpath)

  nodes = dict.fromkeys(yaml.safe_load(nodespath().read_text(encoding='utf-8')) or {})

  for collectionpath in (x for x in (dbpath / 'collections').iterdir() if x.is_file()):
    collections[collectionpath.stem] = dict.fromkeys(yaml.safe_load(collectionpath.read_text(encoding='utf-8')) or {})

  for collectionid in collections:
    for nodeid in collections[collectionid]:
      if nodeid not in nodes:
        raise NodeNotExistError
      nodecollections.setdefault(nodeid, {}).setdefault(collectionid)


def create(dirpath):

  (Path(dirpath) / 'collections').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'properties').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'relationships').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'nodes.yml').touch(exist_ok=True)


def savenodes():

  with nodespath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(nodes), fp, default_flow_style=False)


def savecollection(collectionid):

  with collectionpath(collectionid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(collections[collectionid]), fp, default_flow_style=False)


def addnode(nodeid):

  if nodeid in nodes:
    raise NodeExistError

  nodes.setdefault(nodeid)
  savenodes()


def removenode(nodeid):

  if nodeid not in nodes:
    raise NodeNotExistError

  nodes.pop(nodeid, None)
  savenodes()

  if nodeid in nodecollections:

    for collectionid in nodecollections[nodeid]:
      collections[collectionid].pop(nodeid, None)
      savecollection(collectionid)

    nodecollections.pop(nodeid, None)


def addcollection(collectionid):

  if collectionid in collections:
    raise CollectionExistError

  collections.setdefault(collectionid, {})
  savecollection(collectionid)


def removecollection(collectionid):

  if collectionid not in collections:
    raise CollectionNotExistError

  for nodeid in collections[collectionid]:
    nodecollections[nodeid].pop(collectionid, None)

  collections.pop(collectionid, None)
  collectionpath(collectionid).unlink()


def setnodecollection(nodeid, collectionid):
  
  if nodeid not in nodes:
    raise NodeNotExistError

  if collectionid not in collections:
    raise CollectionNotExistError
  
  collections.setdefault(collectionid, {}).setdefault(nodeid)
  nodecollections.setdefault(nodeid, {}).setdefault(collectionid)

  savecollection(collectionid)


def unsetnodecollection(nodeid, collectionid):

  if nodeid not in nodes:
    raise NodeNotExistError

  if collectionid not in collections:
    raise CollectionNotExistError

  collections[collectionid].pop(nodeid, None)
  nodecollections[nodeid].pop(collectionid, None)

  savecollection(collectionid)