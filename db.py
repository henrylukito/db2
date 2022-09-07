from lib2to3.pgen2.parse import ParseError
from pathlib import Path
import yaml


dbpath = None

node = {} # node[nodeid]
col = {} # col[colid][nodeid]
prop = {} # prop[propid][nodeid]
rel = {} # rel[relid][sourceid][targetid][relpropid]
backrel = {} # backrel[relid][targetid][sourceid][relpropid]

nodecol = {} # nodecol[nodeid][colid]
nodeprop = {} # nodeprop[nodeid][propid]
noderel = {} # noderel[sourceid][relid][targetid][relpropid]
nodebackrel = {} # nodebackrel[targetid][relid][sourceid][relpropid]

def nodepath():
  return dbpath / 'nodes.yml'


def colpath(colid):
  return dbpath / 'collections' / (colid + '.yml')


def proppath(propid):
  return dbpath / 'properties' / (propid + '.yml')


def relpath(relid):
  return dbpath / 'relationships' / (relid + '.yml')


def load(dirpath):

  node.clear()
  col.clear()
  prop.clear()
  rel.clear()

  nodecol.clear()
  nodeprop.clear()
  noderel.clear()

  global dbpath
  dbpath = Path(dirpath)

  (dbpath / 'collections').mkdir(parents=True, exist_ok=True)
  (dbpath / 'properties').mkdir(parents=True, exist_ok=True)
  (dbpath / 'relationships').mkdir(parents=True, exist_ok=True)
  nodepath().touch(exist_ok=True)

  node.update(dict.fromkeys(yaml.safe_load(nodepath().read_text(encoding='utf-8')) or []))

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

  for filepath in (x for x in (dbpath / 'relationships').iterdir() if x.is_file()):
    rel[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for relid in rel:
    for sourceid in rel[relid]:
      if sourceid not in node: setnode(sourceid)
      for targetid in rel[relid][sourceid]:
        if targetid not in node: setnode(targetid)
        noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, rel[relid][sourceid][targetid])
        backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])
        nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])


def savenode():

  with nodepath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(node), fp, default_flow_style=False)


def savecol(colid):

  with colpath(colid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(col[colid]), fp, default_flow_style=False)


def saveprop(propid):

  with proppath(propid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(prop[propid], fp, default_flow_style=False)


def saverel(relid):

  with relpath(relid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(rel[relid], fp, default_flow_style=False) 


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


def setnoderel(sourceid, relid, targetid, propid=None, propvalue=None):

  if sourceid not in node:
    setnode(sourceid)

  if targetid not in node:
    setnode(targetid)

  if relid in rel and sourceid in rel[relid] and targetid in rel[relid][sourceid] and propid is not None and propid in rel[relid][sourceid][targetid] and rel[relid][sourceid][targetid][propid] == propvalue:
    return

  rel.setdefault(relid, {}).setdefault(sourceid, {}).setdefault(targetid, {})

  if propid is not None:
    rel[relid][sourceid][targetid][propid] = propvalue

  noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, rel[relid][sourceid][targetid])

  backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])

  nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])

  saverel(relid)


def remnoderelprop(sourceid, relid, targetid, propid):

  if sourceid not in node:
    return

  if relid not in rel:
    return

  if targetid not in node:
    return

  if sourceid not in rel[relid]:
    return

  if targetid not in rel[relid][sourceid]:
    return

  if propid not in rel[relid][sourceid][targetid]:
    return

  del rel[relid][sourceid][targetid][propid]

  saverel(relid)


def remnodereltarget(sourceid, relid, targetid):

  if sourceid not in node:
    return

  if relid not in rel:
    return

  if targetid not in node:
    return

  if sourceid not in rel[relid]:
    return

  if targetid not in rel[relid][sourceid]:
    return

  del rel[relid][sourceid][targetid]
  if not rel[relid][sourceid]:
    del rel[relid][sourceid]
  if not rel[relid]:
    del rel[relid]

  del noderel[sourceid][relid][targetid]
  if not noderel[sourceid][relid]:
    del noderel[sourceid][relid]
  if not noderel[sourceid]:
    del noderel[sourceid]

  del backrel[relid][targetid][sourceid]
  if not backrel[relid][targetid]:
    del backrel[relid][targetid]
  if not backrel[relid]:
    del backrel[relid]

  del nodebackrel[targetid][relid][sourceid]
  if not nodebackrel[targetid][relid]:
    del nodebackrel[targetid][relid]
  if not nodebackrel[targetid]:
    del nodebackrel[targetid]

  saverel(relid) if relid in rel else relpath(relid).unlink()


def remnoderel(sourceid, relid):

  targetids = list(rel[relid][sourceid])

  for targetid in targetids:
    remnodereltarget(sourceid, relid, targetid)


def remrel(relid):

  sourceids = list(rel[relid])

  for sourceid in sourceids:
    remnoderel(sourceid, relid)


def quickset():

  while True:

    res = input()

    def parseprop(propstr):

      propdict = {}

      propstrs = [x.strip() for x in propstr.split(',')]

      for propstr in propstrs:
        propid, propval = [x.strip() for x in propstr.split('=')]
        propdict[propid] = eval(propval)

      return propdict

    def parsenode(nodestr):

      propsplit = [x.strip() for x in nodestr.split('.', 1)]
      colsplit = [x.strip() for x in propsplit[0].split(':')]

      nodeid = colsplit[0]

      setnode(nodeid)

      if len(colsplit) > 1:
        colids = colsplit[1:]
        for colid in colids:
          setnodecol(nodeid, colid)

      if len(propsplit) == 2:
        propstr = propsplit[1]
        propdict = parseprop(propstr)
        for propid, propval in propdict.items():
          setnodeprop(nodeid, propid, propval)

      return nodeid

    relsplit = [x.strip() for x in res.split('>')]

    if len(relsplit) != 1 and len(relsplit) != 3:
      raise ParseError

    lnodestrs = [x.strip() for x in relsplit[0].split(';')]
    lnodes = [parsenode(lnodestr) for lnodestr in lnodestrs]

    if len(relsplit) == 3:
      rnodestrs = [x.strip() for x in relsplit[2].split(';')]
      rnodes = [parsenode(rnodestr) for rnodestr in rnodestrs]

      relpropsplit = [x.strip() for x in relsplit[1].split('.', 1)]
      relid = relpropsplit[0]
      if len(relpropsplit) > 1:
        relpropdict = parseprop(relpropsplit[1])

      for lnode in lnodes:
        for rnode in rnodes:
          if len(relpropsplit) > 1:
            for relpropid, relpropvalue in relpropdict.items():
              setnoderel(lnode, relid, rnode, relpropid, relpropvalue)
          else:
            setnoderel(lnode, relid, rnode)
