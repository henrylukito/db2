from lib2to3.pgen2.parse import ParseError
from pathlib import Path
from xml.dom import NotFoundErr
import yaml


dbpath = None

node = {} # node[nodeid] = None
col = {} # col[colid][nodeid] = None
prop = {} # prop[propid][nodeid] = propvalue
rel = {} # rel[relid][sourceid][targetid] = relpropdict
backrel = {} # backrel[relid][targetid][sourceid] = relpropdict

nodecol = {} # nodecol[nodeid][colid] = None
nodeprop = {} # nodeprop[nodeid][propid] = propvalue
noderel = {} # noderel[sourceid][relid][targetid] = relpropdict
nodebackrel = {} # nodebackrel[targetid][relid][sourceid] = relpropdict

# rel, backrel, noderel, noderbackrel references the same relpropdict
# relpropdict[relpropid] = relpropvalue


def nodepath(): return dbpath / 'nodes.yml'
def colpath(colid): return dbpath / 'collections' / (colid + '.yml')
def proppath(propid): return dbpath / 'properties' / (propid + '.yml')
def relpath(relid): return dbpath / 'relationships' / (relid + '.yml')


def load(dirpath):

  node.clear()
  col.clear()
  prop.clear()
  rel.clear()
  backrel.clear()

  nodecol.clear()
  nodeprop.clear()
  noderel.clear()
  nodebackrel.clear()

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
      setnode(nodeid)
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  for filepath in (x for x in (dbpath / 'properties').iterdir() if x.is_file()):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for propid in prop:
    for nodeid in prop[propid]:
      setnode(nodeid)
      nodeprop.setdefault(nodeid, {}).setdefault(propid, prop[propid][nodeid])

  for filepath in (x for x in (dbpath / 'relationships').iterdir() if x.is_file()):
    rel[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for relid in rel:
    for sourceid in rel[relid]:
      setnode(sourceid)
      for targetid in rel[relid][sourceid]:
        setnode(targetid)
        noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, rel[relid][sourceid][targetid])
        backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])
        nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])


def savenode():

  with nodepath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(node), fp, default_flow_style=False)


def setnode(nodeid):

  if nodeid in node:
    return

  node.setdefault(nodeid)
  savenode()


def remnode(nodeid):

  if nodeid not in node:
    return

  # node might be in collections, might have properties and relationships etc
  # so it's not sufficient to just remove them

  if nodeid in nodecol:
    for colid in list(nodecol[nodeid]): # copy to list because nodecol might change during iteration
      remnodecol(nodeid, colid) # this will call savecol, remcol etc when needed

  if nodeid in nodeprop:
    for propid in list(nodeprop[nodeid]):
      remnodeprop(nodeid, propid)

  if nodeid in noderel:
    for relid in list(noderel[nodeid]):
      remnoderel(nodeid, relid)

  del node[nodeid]
  savenode()


def renamenode(nodeid, newnodeid):

  if nodeid not in node:
    return

  if newnodeid in node:
    raise Exception("there's already a node with that id")

  del node[nodeid]
  node.setdefault(newnodeid)

  if nodeid in nodecol:
    for colid in nodecol[nodeid]:
      col[colid].setdefault(newnodeid)
      del col[colid][nodeid]
      savecol(colid)
    nodecol[newnodeid] = nodecol[nodeid]
    del nodecol[nodeid]

  if nodeid in nodeprop:
    for propid in nodeprop[nodeid]:
      prop[propid][newnodeid] = prop[propid][nodeid]
      del prop[propid][nodeid]
      saveprop(propid)
    nodeprop[newnodeid] = nodeprop[nodeid]
    del nodeprop[nodeid]

  if nodeid in noderel:

    for relid in noderel[nodeid]:
      rel[relid][newnodeid] = rel[relid][nodeid]
      del rel[relid][nodeid]
      saverel(relid)

      for targetid in rel[relid][newnodeid]:
        backrel[relid][targetid][newnodeid] = backrel[relid][targetid][nodeid]
        del backrel[relid][targetid][nodeid]
        nodebackrel[targetid][relid][newnodeid] = nodebackrel[targetid][relid][nodeid]
        del nodebackrel[targetid][relid][nodeid]

    noderel[newnodeid] = noderel[nodeid]
    del noderel[nodeid]

  if nodeid in nodebackrel:

    for relid in nodebackrel[nodeid]:
      backrel[relid][newnodeid] = backrel[relid][nodeid]
      del backrel[relid][nodeid]

      for sourceid in backrel[relid][newnodeid]:
        rel[relid][sourceid][newnodeid] = rel[relid][sourceid][nodeid]
        del rel[relid][sourceid][nodeid]
        noderel[sourceid][relid][newnodeid] = noderel[sourceid][relid][nodeid]
        del noderel[sourceid][relid][nodeid]
        saverel(relid)

    nodebackrel[newnodeid] = nodebackrel[nodeid]
    del nodebackrel[nodeid]

  savenode()


def savecol(colid):

  with colpath(colid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(col[colid]), fp, default_flow_style=False)


def setnodecol(nodeid, colid):
  
  setnode(nodeid) # will create node and store in node dict if not exist

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

  del col[colid][nodeid]
  del nodecol[nodeid][colid]

  if not nodecol[nodeid]: # if nodecol[nodeid] become empty as result of removing col
    del nodecol[nodeid] # remove nodeid from nodecol (this means node has no collection)

  if not col[colid]: # if col[colid] become empty as result of removing node
    remcol(colid) # will delete col file
  else:
    savecol(colid) 


def remcol(colid):

  if colid not in col:
    return

  for nodeid in col[colid]:
    del nodecol[nodeid][colid]

  del col[colid]
  colpath(colid).unlink()


def saveprop(propid):

  with proppath(propid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(prop[propid], fp, default_flow_style=False)


def setnodeprop(nodeid, propid, propvalue):
  
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

  del prop[propid][nodeid]
  del nodeprop[nodeid][propid]

  if not nodeprop[nodeid]:
    del nodeprop[nodeid]

  if not prop[propid]:
    remprop(propid)
  else:
    saveprop(propid)


def remprop(propid):

  if propid not in prop:
    return

  for nodeid in prop[propid]:
    nodeprop[nodeid].pop(propid, None)

  prop.pop(propid, None)
  proppath(propid).unlink()


def saverel(relid):

  with relpath(relid).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(rel[relid], fp, default_flow_style=False) 


def setnoderel(sourceid, relid, targetid, propid=None, propvalue=None):

  setnode(sourceid)

  setnode(targetid)

  if relid in rel and sourceid in rel[relid] and targetid in rel[relid][sourceid]:
    if propid is None: # if don't specify property and relationship already exists
      return
    if propid is not None and propid in rel[relid][sourceid][targetid] and rel[relid][sourceid][targetid][propid] == propvalue: # if specify property but property exist and has same value
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

  del rel[relid][sourceid][targetid][propid] # no need to do backrel, noderel, nodebackrel since they refer to same dict object

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
  if not rel[relid][sourceid]: # if a source's relationship no longer has target
    del rel[relid][sourceid]
  if not rel[relid]: # if no more source in relationship
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

  if relid not in rel: # we deleted the relationship above
    relpath(relid).unlink()
  else:
    saverel(relid)


def remnoderel(sourceid, relid):

  targetids = list(rel[relid][sourceid])

  for targetid in targetids:
    remnodereltarget(sourceid, relid, targetid)


def remrel(relid):

  sourceids = list(rel[relid])

  for sourceid in sourceids:
    remnoderel(sourceid, relid)


def quickset(arg=None):

  def parseset(arg):

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

    relsplit = [x.strip() for x in arg.split('>')]

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

  if arg is None:
    try:
      while True:
        parseset(input())
    except KeyboardInterrupt:
      pass

  elif isinstance(arg, str):
    parseset(arg)

  elif isinstance(arg, list) and all(isinstance(e, str) for e in arg):
    for e in arg:
      parseset(e)

  else:
    raise TypeError
