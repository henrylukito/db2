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


def load(dirpath):

  global node
  node.clear()
  col.clear()
  prop.clear()

  nodecol.clear()
  nodeprop.clear()

  global dbpath
  dbpath = Path(dirpath)

  (dbpath / 'collections').mkdir(parents=True, exist_ok=True)
  (dbpath / 'properties').mkdir(parents=True, exist_ok=True)
  (dbpath / 'relationships').mkdir(parents=True, exist_ok=True)
  nodepath().touch(exist_ok=True)

  node = dict.fromkeys(yaml.safe_load(nodepath().read_text(encoding='utf-8')) or [])

  for filepath in (x for x in (dbpath / 'collections').iterdir() if x.is_file()):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or [])

  for colid in col:
    for nodeid in col[colid]:
      if nodeid not in node: setnode(nodeid)
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  for filepath in (x for x in (dbpath / 'properties').iterdir() if x.is_file()):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for propid in prop:
    for nodeid in prop[propid]:
      if nodeid not in node: setnode(nodeid)
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


def setnode(nodeid):

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


def remcol(colid):

  if colid not in col:
    return

  for nodeid in col[colid]:
    nodecol[nodeid].pop(colid, None)

  col.pop(colid, None)
  colpath(colid).unlink()


def setnodecol(nodeid, colid):
  
  if nodeid not in node:
    setnode(nodeid)

  if colid in col and nodeid in col[colid]:
    return
  
  col.setdefault(colid, {}).setdefault(nodeid)
  nodecol.setdefault(nodeid, {}).setdefault(colid)

  savecol(colid)


def remnodecol(nodeid, colid):

  if nodeid not in node:
    return

  if colid not in col:
    return

  if nodeid not in col[colid]:
    return

  col[colid].pop(nodeid, None)
  nodecol[nodeid].pop(colid, None)

  if not nodecol[nodeid]:
    nodecol.pop(nodeid, None)

  savecol(colid) if col[colid] else remcol(colid)


def remprop(propid):

  if propid not in prop:
    return

  for nodeid in prop[propid]:
    nodeprop[nodeid].pop(propid, None)

  prop.pop(propid, None)
  proppath(propid).unlink()


def setnodeprop(nodeid, propid, propvalue):
  
  if nodeid not in node:
    setnode(nodeid)

  if propid in prop and nodeid in prop[propid] and prop[propid][nodeid] == propvalue:
    return
  
  prop.setdefault(propid, {})[nodeid] = propvalue
  nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]

  saveprop(propid)


def remnodeprop(nodeid, propid):

  if nodeid not in node:
    return

  if propid not in prop:
    return

  if nodeid not in prop[propid]:
    return

  prop[propid].pop(nodeid, None)
  nodeprop[nodeid].pop(propid, None)

  if not nodeprop[nodeid]:
    nodeprop.pop(nodeid, None)

  saveprop(propid) if prop[propid] else remprop(propid)