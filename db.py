from pathlib import Path
import yaml


dbpath = None

node = {}
col = {}

nodecol = {}


class NodeExistError(Exception): pass
class NodeNotExistError(Exception): pass
class CollectionExistError(Exception): pass
class CollectionNotExistError(Exception): pass


def nodepath():
  return dbpath / 'nodes.yml'


def colpath(colid):
  return dbpath / 'collections' / (colid + '.yml')


def clear():

  global dbpath

  dbpath = None

  node.clear()
  col.clear()

  nodecol.clear()


def use(dirpath):

  clear()

  global dbpath
  global node

  dbpath = Path(dirpath)

  node = dict.fromkeys(yaml.safe_load(nodepath().read_text(encoding='utf-8')) or {})

  for filepath in (x for x in (dbpath / 'collections').iterdir() if x.is_file()):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or {})

  for colid in col:
    for nodeid in col[colid]:
      if nodeid not in node:
        raise NodeNotExistError
      nodecol.setdefault(nodeid, {}).setdefault(colid)


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