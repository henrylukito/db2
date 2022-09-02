from pathlib import Path
import yaml


dbpath = None

node = {}
col = {}
prop = {}

nodecol = {}
nodeprop = {}


class NodeExistError(Exception): pass
class NodeNotExistError(Exception): pass
class CollectionExistError(Exception): pass
class CollectionNotExistError(Exception): pass
class PropertyExistError(Exception): pass
class PropertyNotExistError(Exception): pass


def nodepath():
  return dbpath / 'nodes.yml'


def colpath(colid):
  return dbpath / 'collections' / (colid + '.yml')


def proppath(propid):
  return dbpath / 'properties' / (propid + '.yml')


def clear():

  global dbpath
  dbpath = None

  node.clear()
  col.clear()
  prop.clear()

  nodecol.clear()
  nodeprop.clear()


def use(dirpath):

  clear()

  global dbpath
  dbpath = Path(dirpath)

  global node
  node = dict.fromkeys(yaml.safe_load(nodepath().read_text(encoding='utf-8')) or {})

  for filepath in (x for x in (dbpath / 'collections').iterdir() if x.is_file()):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or {})

  for colid in col:
    for nodeid in col[colid]:
      if nodeid not in node:
        raise NodeNotExistError
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  for filepath in (x for x in (dbpath / 'properties').iterdir() if x.is_file()):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for propid in prop:
    for nodeid in prop[propid]:
      if nodeid not in node:
        raise NodeNotExistError
      nodeprop.setdefault(nodeid, {}).setdefault(propid, prop[propid][nodeid])


def create(dirpath):

  (Path(dirpath) / 'collections').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'properties').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'relationships').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'nodes.yml').touch(exist_ok=True)

  use(dirpath)


def savenode():

  with nodepath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(node), fp, default_flow_style=False)


def savecol(colid):

  with colpath(colid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(col[colid]), fp, default_flow_style=False)


def saveprop(propid):

  with proppath(propid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(prop[propid], fp, default_flow_style=False)


def addnode(nodeid):

  if nodeid in node:
    raise NodeExistError

  node.setdefault(nodeid)
  savenode()


def removenode(nodeid):

  if nodeid not in node:
    raise NodeNotExistError

  node.pop(nodeid, None)
  savenode()

  if nodeid in nodecol:

    for colid in nodecol[nodeid]:
      col[colid].pop(nodeid, None)
      savecol(colid)

    nodecol.pop(nodeid, None)


def addcol(colid):

  if colid in col:
    raise CollectionExistError

  col.setdefault(colid, {})
  savecol(colid)


def removecol(colid):

  if colid not in col:
    raise CollectionNotExistError

  for nodeid in col[colid]:
    nodecol[nodeid].pop(colid, None)

  col.pop(colid, None)
  colpath(colid).unlink()


def setnodecol(nodeid, colid):
  
  if nodeid not in node:
    raise NodeNotExistError

  if colid not in col:
    raise CollectionNotExistError
  
  col.setdefault(colid, {}).setdefault(nodeid)
  nodecol.setdefault(nodeid, {}).setdefault(colid)

  savecol(colid)


def unsetnodecol(nodeid, colid):

  if nodeid not in node:
    raise NodeNotExistError

  if colid not in col:
    raise CollectionNotExistError

  col[colid].pop(nodeid, None)
  nodecol[nodeid].pop(colid, None)

  savecol(colid)


def addprop(propid):

  if propid in prop:
    raise PropertyExistError

  prop.setdefault(propid, {})
  saveprop(propid)


def removeprop(propid):

  if propid not in prop:
    raise PropertyNotExistError

  for nodeid in prop[propid]:
    nodeprop[nodeid].pop(propid, None)

  prop.pop(propid, None)
  proppath(propid).unlink()


def setnodeprop(nodeid, propid, propvalue):
  
  if nodeid not in node:
    raise NodeNotExistError

  if propid not in prop:
    raise PropertyNotExistError
  
  prop.setdefault(propid, {})[nodeid] = propvalue
  nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]

  saveprop(propid)


def unsetnodeprop(nodeid, propid):

  if nodeid not in node:
    raise NodeNotExistError

  if propid not in prop:
    raise PropertyNotExistError

  prop[propid].pop(nodeid, None)
  nodeprop[nodeid].pop(propid, None)

  saveprop(propid)