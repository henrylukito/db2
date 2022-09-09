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

colprop = {} # colprop[colid][propid] = typestr
relprop = {} # relprop[relid][propid] = typestr


def nodepath(): return dbpath / 'nodes.yml'
def colpath(colid): return dbpath / 'collections' / (colid + '.yml')
def proppath(propid): return dbpath / 'properties' / (propid + '.yml')
def relpath(relid): return dbpath / 'relationships' / (relid + '.yml')
def colproppath(): return dbpath / 'collectionproperties.yml'
def relproppath(): return dbpath / 'relationshipproperties.yml'


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

  colprop.clear()
  relprop.clear()
  
  global dbpath
  dbpath = Path(dirpath)

  # make expected subdirectories and files if they don't exist
  (dbpath / 'collections').mkdir(parents=True, exist_ok=True)
  (dbpath / 'properties').mkdir(parents=True, exist_ok=True)
  (dbpath / 'relationships').mkdir(parents=True, exist_ok=True)
  nodepath().touch(exist_ok=True)
  colproppath().touch(exist_ok=True)
  relproppath().touch(exist_ok=True)

  # load node
  node.update(dict.fromkeys(yaml.safe_load(nodepath().read_text(encoding='utf-8')) or []))

  # load col
  for filepath in (x for x in (dbpath / 'collections').iterdir() if x.is_file()):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or [])

  # update nodecol based on col
  for colid in col:
    for nodeid in col[colid]:
      setnode(nodeid) # if node doesn't exist, create node and save to nodes.yml
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  # load prop
  for filepath in (x for x in (dbpath / 'properties').iterdir() if x.is_file()):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  # load nodeprop
  for propid in prop:
    for nodeid in prop[propid]:
      setnode(nodeid)
      nodeprop.setdefault(nodeid, {}).setdefault(propid, prop[propid][nodeid])

  # load rel
  for filepath in (x for x in (dbpath / 'relationships').iterdir() if x.is_file()):
    rel[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  # load noderel, backrel, nodebackrel based on rel
  for relid in rel:
    for sourceid in rel[relid]:
      setnode(sourceid)
      for targetid in rel[relid][sourceid]:
        setnode(targetid)
        noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, rel[relid][sourceid][targetid])
        backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])
        nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, rel[relid][sourceid][targetid])

  # load colprop
  colprop.update(yaml.safe_load(colproppath().read_text(encoding='utf-8')) or {})

  # load relprop
  relprop.update(yaml.safe_load(relproppath().read_text(encoding='utf-8')) or {})


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

  if nodeid == newnodeid:
    return

  if nodeid not in node:
    return

  if newnodeid in node:
    raise Exception("There's already node with that id")

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


def renamecol(colid, newcolid):

  if colid == newcolid:
    return

  if colid not in col:
    return

  if newcolid in col:
    raise Exception("There's already col with that id")

  for nodeid in col[colid]:
    nodecol[nodeid].setdefault(newcolid)
    del nodecol[nodeid][colid]

  col[newcolid] = col[colid]
  del col[colid]

  savecol(newcolid)
  colpath(colid).unlink()

  # rename colid in colprop
  if colid in colprop:
    if newcolid not in colprop:
      colprop[newcolid] = colprop[colid]
    del colprop[colid]
    savecolprop()


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


def renameprop(propid, newpropid):

  if propid == newpropid:
    return

  if propid not in prop:
    return

  if newpropid in prop:
    raise Exception("There's already prop with that id")

  for nodeid in prop[propid]:
    nodeprop[nodeid][newpropid] = nodeprop[nodeid][propid]
    del nodeprop[nodeid][propid]

  prop[newpropid] = prop[propid]
  del prop[propid]

  saveprop(newpropid)
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


def renamenoderelprop(sourceid, relid, targetid, propid, newpropid):

  if propid == newpropid:
    return

  if sourceid not in node:
    return

  if relid not in rel:
    return

  if sourceid not in rel[relid]:
    return

  if targetid not in rel[relid][sourceid]:
    return

  if propid not in rel[relid][sourceid][targetid]:
    return

  if newpropid not in rel[relid][sourceid][targetid]:
    rel[relid][sourceid][targetid][newpropid] = rel[relid][sourceid][targetid][propid]

  del rel[relid][sourceid][targetid][propid]

  saverel(relid)


def renamerel(relid, newrelid):

  if relid == newrelid:
    return

  if relid not in rel:
    return

  if newrelid in rel:
    raise Exception("There's already rel with that id")

  for sourceid in rel[relid]:

    for targetid in rel[relid][sourceid]:
      nodebackrel[targetid][newrelid] = nodebackrel[targetid][relid]
      del nodebackrel[targetid][relid]

    noderel[sourceid][newrelid] = noderel[sourceid][relid]
    del noderel[sourceid][relid]

  rel[newrelid] = rel[relid]
  del rel[relid]

  backrel[newrelid] = backrel[relid]
  del backrel[relid]

  saverel(newrelid)
  relpath(relid).unlink()

  # rename relid in relprop
  if relid in relprop:
    if newrelid not in relprop:
      relprop[newrelid] = relprop[relid]
    del relprop[relid]
    saverelprop()


def savecolprop():

  with colproppath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(colprop, fp, default_flow_style=False)


def setcolprop(colid, propid, proptype=None):

  # accept even if colid not yet exist, the colid might be created later

  colprop.setdefault(colid, {})[propid] = proptype

  savecolprop()


def remcolprop(colid, propid):

  if colid in colprop and propid in colprop[colid]:
    del colprop[colid][propid]

  savecolprop()


def fillcolprop(colid, propid=None):

  if colid not in col: # no colid means no node with that colid, so no node to fill prop
    return

  if colid not in colprop:
    return

  if propid and propid not in colprop[colid]: # user specify propid but propid not in colprop[colid]
    return

  propids = [propid] if propid else colprop[colid] # if propid not specified, we go through all propids of colprop[colid]

  for propid in propids:

    proptype = eval(colprop[colid][propid]) if colprop[colid][propid] else (lambda x: eval(x))

    try:

      for nodeid in col[colid]:

        if nodeid not in nodeprop or propid not in nodeprop[nodeid]:

            ans = input(f"{nodeid}.{propid}: ")

            prop.setdefault(propid, {})[nodeid] = proptype(ans)
            nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]
            saveprop(propid)

    except KeyboardInterrupt:
      break


def saverelprop():

  with relproppath().open('w', encoding='utf-8') as fp:
    yaml.safe_dump(relprop, fp, default_flow_style=False)


def setrelprop(relid, relpropid, relproptype=None):

  # accept even if relid not yet exist, the relid might be created later

  relprop.setdefault(relid, {})[relpropid] = relproptype

  saverelprop()


def remrelprop(relid, relpropid):

  if relid in relprop and relpropid in relprop[relid]:
    del relprop[relid][relpropid]

  saverelprop()


def fillrelprop(relid, relpropid=None):

  if relid not in rel:
    return

  if relid not in relprop:
    return

  if relpropid and relpropid not in relprop[relid]:
    return

  relpropids = [relpropid] if relpropid else relprop[relid]

  for relpropid in relpropids:

    relproptype = eval(relprop[relid][relpropid]) if relprop[relid][relpropid] else (lambda x: eval(x))

    try:
      
      for sourceid in rel[relid]:
        for targetid in rel[relid][sourceid]:

          if relpropid not in rel[relid][sourceid][targetid]:

            ans = input(f"{sourceid}>{relid}>{targetid} {relpropid}: ")

            rel[relid][sourceid][targetid][relpropid] = relproptype(ans)
            saverel(relid)


    except KeyboardInterrupt:
      break


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
