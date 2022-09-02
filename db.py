from pathlib import Path
import yaml


dbpath = None

node = {}
col = {}
prop = {}

nodecol = {}
nodeprop = {}


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


def setup(dirpath):

  (Path(dirpath) / 'collections').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'properties').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'relationships').mkdir(parents=True, exist_ok=True)
  (Path(dirpath) / 'nodes.yml').touch(exist_ok=True)

  load(dirpath)


def load(dirpath):

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
        addnode(nodeid)
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  for filepath in (x for x in (dbpath / 'properties').iterdir() if x.is_file()):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for propid in prop:
    for nodeid in prop[propid]:
      if nodeid not in node:
        addnode(nodeid)
      nodeprop.setdefault(nodeid, {}).setdefault(propid, prop[propid][nodeid])


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
    return

  node.setdefault(nodeid)
  savenode()


def remnode(nodeid):

  if nodeid not in node:
    return

  node.pop(nodeid, None)
  savenode()

  if nodeid in nodecol:

    for colid in nodecol[nodeid]:
      col[colid].pop(nodeid, None)
      savecol(colid)

    nodecol.pop(nodeid, None)


def addcol(colid):

  if colid in col:
    return

  col.setdefault(colid, {})
  savecol(colid)


def remcol(colid):

  if colid not in col:
    return

  for nodeid in col[colid]:
    nodecol[nodeid].pop(colid, None)

  col.pop(colid, None)
  colpath(colid).unlink()


def setnodecol(nodeid, colid):
  
  if nodeid not in node:
    addnode(nodeid)

  if colid not in col:
    addcol(colid)
  
  col.setdefault(colid, {}).setdefault(nodeid)
  nodecol.setdefault(nodeid, {}).setdefault(colid)

  savecol(colid)


def unsetnodecol(nodeid, colid):

  if nodeid not in node:
    return

  if colid not in col:
    return

  if nodeid not in col[colid]:
    return

  col[colid].pop(nodeid, None)
  nodecol[nodeid].pop(colid, None)

  savecol(colid)


def addprop(propid):

  if propid in prop:
    return

  prop.setdefault(propid, {})
  saveprop(propid)


def remprop(propid):

  if propid not in prop:
    return

  for nodeid in prop[propid]:
    nodeprop[nodeid].pop(propid, None)

  prop.pop(propid, None)
  proppath(propid).unlink()


def setnodeprop(nodeid, propid, propvalue):
  
  if nodeid not in node:
    addnode(nodeid)

  if propid not in prop:
    addprop(propid)
  
  prop.setdefault(propid, {})[nodeid] = propvalue
  nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]

  saveprop(propid)


def unsetnodeprop(nodeid, propid):

  if nodeid not in node:
    return

  if propid not in prop:
    return

  if nodeid not in prop[propid]:
    return

  prop[propid].pop(nodeid, None)
  nodeprop[nodeid].pop(propid, None)

  saveprop(propid)