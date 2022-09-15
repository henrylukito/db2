from pathlib import Path
import yaml

dbpath = Path()
is_loaded = False

node = {}
col = {}
prop = {}
rel = {}
backrel = {}

nodeempty = {}
nodecol = {}
nodeprop = {}
noderel = {}
nodebackrel = {}
nodereltarget = {}
noderelsource = {}

colprop = {}

###############################################################################

def reset():
  global is_loaded
  is_loaded = False

  node.clear()
  col.clear()
  prop.clear()
  rel.clear()
  backrel.clear()

  nodeempty.clear()
  nodecol.clear()
  nodeprop.clear()
  noderel.clear()
  nodebackrel.clear()
  nodereltarget.clear()
  noderelsource.clear()

  colprop.clear()

###############################################################################

def load(dirpath=None):

  reset()

  if dirpath:
    global dbpath
    dbpath = Path(dirpath)
  
  (dbpath / 'collections').mkdir(parents=True, exist_ok=True)
  (dbpath / 'properties').mkdir(parents=True, exist_ok=True)
  (dbpath / 'relationships').mkdir(parents=True, exist_ok=True)
  (dbpath / 'emptynodes.yml').touch(exist_ok=True)
  (dbpath / 'collectionproperties.yml').touch(exist_ok=True)

  for filepath in (filepath for filepath in (dbpath/'collections').iterdir() if filepath.is_file() and filepath.suffix == '.yml'):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or [])

  for colid in col:
    for nodeid in col[colid]:
      node.setdefault(nodeid)
      nodecol.setdefault(nodeid, {})[colid] = None

  for filepath in (filepath for filepath in (dbpath/'properties').iterdir() if filepath.is_file() and filepath.suffix == '.yml'):
    prop[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for propid in prop:
    for nodeid in prop[propid]:
      node.setdefault(nodeid)
      nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]

  for filepath in (filepath for filepath in (dbpath/'relationships').iterdir() if filepath.is_file() and filepath.suffix == '.yml'):
    rel[filepath.stem] = yaml.safe_load(filepath.read_text(encoding='utf-8')) or {}

  for relid in rel:
    for sourceid in rel[relid]:
      node.setdefault(sourceid)
      for targetid in rel[relid][sourceid]:
        node.setdefault(targetid)

        relpropdict = rel[relid][sourceid][targetid]

        backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, relpropdict)
        noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, relpropdict)
        nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, relpropdict)
        nodereltarget.setdefault(sourceid, {}).setdefault(targetid, {}).setdefault(relid, relpropdict)
        noderelsource.setdefault(targetid, {}).setdefault(sourceid, {}).setdefault(relid, relpropdict)

  nodeempty.update(dict.fromkeys(yaml.safe_load((dbpath / 'emptynodes.yml').read_text(encoding='utf-8')) or []))

  nodeemptyhaschange = False

  for nodeid in list(nodeempty):
    if nodeid in node:
      del nodeempty[nodeid]
      nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty()

  node.update(nodeempty)

  colprop.update(yaml.safe_load((dbpath / 'collectionproperties.yml').read_text(encoding='utf-8')) or {})

  global is_loaded
  is_loaded = True

###############################################################################

def _loadifnotloaded():
  if not is_loaded:
    load()

###############################################################################

def _savenodeempty():
  with (dbpath/'emptynodes.yml').open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(nodeempty), fp, default_flow_style=False)

###############################################################################

def _savecol(colid):

  with (dbpath / 'collections' / (colid + '.yml')).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(list(col[colid]), fp, default_flow_style=False)

###############################################################################

def _delcol(colid):

  (dbpath / 'collections' / (colid + '.yml')).unlink()

###############################################################################

def _saveprop(propid):

  with (dbpath / 'properties' / (propid + '.yml')).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(prop[propid], fp, default_flow_style=False)

###############################################################################

def _delprop(propid):

  (dbpath / 'properties' / (propid + '.yml')).unlink()

###############################################################################

def _saverel(relid):

  with (dbpath / 'relationships' / (relid + '.yml')).open('w', encoding='utf-8') as fp:
    yaml.safe_dump(rel[relid], fp, default_flow_style=False)

###############################################################################

def _delrel(relid):

  (dbpath / 'relationships' / (relid + '.yml')).unlink()

###############################################################################

def _savecolprop():

  with (dbpath / 'collectionproperties.yml').open('w', encoding='utf-8') as fp:
    yaml.safe_dump(colprop, fp, default_flow_style=False)

###############################################################################

def isnodeempty(nodeid):

# check whether node is empty, not whether it's in nodeempty
# but whether it's in any of nodecol, nodeprop, etc
# this is usually called when removing node from nodecol, nodeprop etc
# to check whether node has become empty, if so put to nodeempty

  if not nodeid:
    return
  
  _loadifnotloaded()
  
  if nodeid in nodecol:
    return False

  if nodeid in nodeprop:
    return False

  if nodeid in noderel:
    return False

  if nodeid in nodebackrel:
    return False

  return True

###############################################################################

def setnode(nodeid):

# create node if not already exist
# if we create node, since it's empty node, also put in nodeempty

  if not nodeid:
    return

  _loadifnotloaded()

  if nodeid in node:
    return

  nodeempty.setdefault(nodeid)
  _savenodeempty()

  node.setdefault(nodeid)

###############################################################################

def remnode(nodeid):

# remove node if exist
# since node might be in collection or have property, need to clean up by calling rem functions
# node might be empty node, so need to remove it from nodeempty

  if not nodeid:
    return

  _loadifnotloaded()

  if nodeid not in node:
    return

  if nodeid in nodecol:
    for colid in list(nodecol[nodeid]):
      remnodecol(nodeid, colid)

  if nodeid in nodeprop:
    for propid in list(nodeprop[nodeid]):
      remnodeprop(nodeid, propid)

  if nodeid in nodebackrel:
    for relid in list(nodebackrel[nodeid]):
      for sourceid in nodebackrel[nodeid][relid]:
        remnodereltarget(sourceid, relid, nodeid)

  if nodeid in noderel:
    for relid in list(noderel[nodeid]):
      remnoderel(nodeid, relid)

  if nodeid in nodeempty:
    del nodeempty[nodeid]
    _savenodeempty()

  del node[nodeid]

###############################################################################

def renamenode(oldnodeid, newnodeid):

# rename node if exist
# newnodeid might be new or already exist
# if already exist, operation is like merge and then remove old name

  if not oldnodeid or not newnodeid:
    return

  _loadifnotloaded()

  if oldnodeid not in node:
    return

  del node[oldnodeid]
  node.setdefault(newnodeid)

  hasnodeemptychange = False

  if oldnodeid in nodeempty:
    del nodeempty[oldnodeid]
    hasnodeemptychange = True
    # here we don't add newnodeid to nodeempty because newnodeid might already exist
    # and it might not be empty node
    # last part we check if newnodeid is empty and not in nodeempty, then we'll add to nodeempty

  if oldnodeid in nodecol:
    for colid in nodecol[oldnodeid]:
      del col[colid][oldnodeid]
      col[colid].setdefault(newnodeid)
      _savecol(colid)
    nodecol.setdefault(newnodeid, {}).update(nodecol[oldnodeid])
    # above we merge and not overwrite because newnodeid might already exist and have existing col
    del nodecol[oldnodeid]
    # since newnodeid has some col, it shouldn't exist in nodeempty
    if newnodeid in nodeempty:
      del nodeempty[newnodeid]
      hasnodeemptychange = True

  if oldnodeid in nodeprop:
    for propid in nodeprop[oldnodeid]:
      # if newnodeid already exist and has property,
      # we choose to keep newnodeid property value rather than set it with oldnodeid property value
      if newnodeid not in prop[propid]:
        prop[propid][newnodeid] = prop[propid][oldnodeid]
        nodeprop.setdefault(newnodeid, {})[propid] = prop[propid][newnodeid]
      del prop[propid][oldnodeid]
      _saveprop(propid)
    del nodeprop[oldnodeid]
    if newnodeid in nodeempty:
      del nodeempty[newnodeid]
      hasnodeemptychange = True

  # if newnodeid is empty but not in nodeempty, it should be added to nodeempty
  if isnodeempty(newnodeid) and newnodeid not in nodeempty:
    nodeempty.setdefault(newnodeid)
    hasnodeemptychange = True

  if hasnodeemptychange:
    _savenodeempty()

###############################################################################

def setnodecol(nodeid, colid):

# set node to collection
# node and collection will be created if not exist

  if not nodeid or not colid:
    return

  _loadifnotloaded()

  if colid in col and nodeid in col[colid]:
    return

  node.setdefault(nodeid)
  col.setdefault(colid, {}).setdefault(nodeid)
  nodecol.setdefault(nodeid, {}).setdefault(colid)

  # because node is now in collection, it it was empty node before
  # it should now be removed from nodeempty
  if nodeid in nodeempty:
    del nodeempty[nodeid]
    _savenodeempty()

  _savecol(colid)

###############################################################################

def remnodecol(nodeid, colid):

# remove node from collection if they exist

  if not nodeid or not colid:
    return

  _loadifnotloaded()

  if nodeid not in node:
    return

  if colid not in col:
    return
  
  if nodeid not in col[colid]:
    return

  del col[colid][nodeid]
  del nodecol[nodeid][colid]

  if not nodecol[nodeid]:
    del nodecol[nodeid]

    # since we remove node from nodecol, there's possibility node has now become empty node,
    # if so, it should be added to nodeempty
    if isnodeempty(nodeid):
      nodeempty.setdefault(nodeid)
      _savenodeempty()

  # if collection is now empty, should delete file. Else, save file
  if not col[colid]:
    _delcol(colid)
  else:
    _savecol(colid)

###############################################################################

def remcol(colid):

# remove collection

  if not colid:
    return

  _loadifnotloaded()

  if colid not in col:
    return

  nodeemptyhaschange = False

  # need to clean up nodecol
  # even put nodeid that has become empty to nodeempty
  for nodeid in col[colid]:
    del nodecol[nodeid][colid]
    if not nodecol[nodeid]:
      del nodecol[nodeid]

      if isnodeempty(nodeid):
        nodeempty.setdefault(nodeid)
        nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty()

  del col[colid]
  _delcol(colid)

###############################################################################

def renamecol(oldcolid, newcolid):

  if oldcolid == newcolid:
    return

  if not oldcolid or not newcolid:
    return

  _loadifnotloaded()

  if oldcolid not in col:
    return

  for nodeid in col[oldcolid]:
    nodecol[nodeid].setdefault(newcolid)
    del nodecol[nodeid][oldcolid]

  col.setdefault(newcolid, {}).update(col[oldcolid])
  del col[oldcolid]

  _delcol(oldcolid)
  _savecol(newcolid)

###############################################################################

def setnodeprop(nodeid, propid, propvalue):

# set node property
# node and property will be created if not exist

  if not nodeid or not propid:
    return

  _loadifnotloaded()

  if propid in prop and nodeid in prop[propid] and prop[propid][nodeid] == propvalue:
    return

  prop.setdefault(propid, {})[nodeid] = propvalue
  nodeprop.setdefault(nodeid, {})[propid] = prop[propid][nodeid]

  if nodeid in nodeempty:
    del nodeempty[nodeid]
    _savenodeempty()

  _saveprop(propid)

###############################################################################

def remnodeprop(nodeid, propid):

# remove node property if exist

  if not nodeid or not propid:
    return

  _loadifnotloaded()

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

    if isnodeempty(nodeid):
      nodeempty.setdefault(nodeid)
      _savenodeempty()

  if not prop[propid]:
    _delprop(propid)
  else:
    _saveprop(propid)

###############################################################################

def remprop(propid):

# remove property

  if not propid:
    return

  _loadifnotloaded()

  if propid not in prop:
    return

  nodeemptyhaschange = False

  for nodeid in prop[propid]:
    del nodeprop[nodeid][propid]
    if not nodeprop[nodeid]:
      del nodeprop[nodeid]

      if isnodeempty(nodeid):
        nodeempty.setdefault(nodeid)
        nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty()

  del prop[propid]
  _delprop(propid)

###############################################################################

def renameprop(oldpropid, newpropid):

  if oldpropid == newpropid:
    return

  if not oldpropid or not newpropid:
    return

  _loadifnotloaded()

  if oldpropid not in prop:
    return

  prop.setdefault(newpropid, {})

  for nodeid in prop[oldpropid]:
    if nodeid not in prop[newpropid]:
      prop[newpropid][nodeid] = prop[oldpropid][nodeid]
      nodeprop.setdefault(nodeid, {})[newpropid] = prop[newpropid][nodeid]
    del nodeprop[nodeid][oldpropid]

  del prop[oldpropid]

  _delprop(oldpropid)
  _saveprop(newpropid)

###############################################################################

def setnoderel(sourceid, relid, targetid, propid=None, propvalue=None):

  if not sourceid or not relid or not targetid:
    return

  _loadifnotloaded()

  node.setdefault(sourceid)
  node.setdefault(targetid)

  if relid in rel and sourceid in rel[relid] and targetid in rel[relid][sourceid]:
    if propid is None:
      return
    if propid is not None and propid in rel[relid][sourceid][targetid] and rel[relid][sourceid][targetid][propid] == propvalue: # if specify property but property exist and has same value
      return

  rel.setdefault(relid, {}).setdefault(sourceid, {}).setdefault(targetid, {})
  relpropdict = rel[relid][sourceid][targetid]

  if propid is not None:
    relpropdict[propid] = propvalue

  backrel.setdefault(relid, {}).setdefault(targetid, {}).setdefault(sourceid, relpropdict)
  noderel.setdefault(sourceid, {}).setdefault(relid, {}).setdefault(targetid, relpropdict)
  nodebackrel.setdefault(targetid, {}).setdefault(relid, {}).setdefault(sourceid, relpropdict)
  nodereltarget.setdefault(sourceid, {}).setdefault(targetid, {}).setdefault(relid, relpropdict)
  noderelsource.setdefault(targetid, {}).setdefault(sourceid, {}).setdefault(relid, relpropdict)

  nodeemptyhaschange = False

  if sourceid in nodeempty:
    del nodeempty[sourceid]
    nodeemptyhaschange = True

  if targetid in nodeempty:
    del nodeempty[targetid]
    nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty()

  _saverel(relid)

###############################################################################

def remnoderelprop(sourceid, relid, targetid, propid):

  if not sourceid or not relid or not targetid or not propid:
    return

  _loadifnotloaded()

  if sourceid not in node or relid not in rel or targetid not in node:
    return

  if sourceid not in rel[relid]:
    return

  if targetid not in rel[relid][sourceid]:
    return

  if propid not in rel[relid][sourceid][targetid]:
    return

  del rel[relid][sourceid][targetid][propid] # no need to do backrel, noderel, nodebackrel since they refer to same dict object

  _saverel(relid)

###############################################################################

def remnodereltarget(sourceid, relid, targetid):

  if not sourceid or not relid or not targetid:
    return

  _loadifnotloaded()

  if sourceid not in node or relid not in rel or targetid not in node:
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

  del backrel[relid][targetid][sourceid]
  if not backrel[relid][targetid]:
    del backrel[relid][targetid]
  if not backrel[relid]:
    del backrel[relid]

  del noderel[sourceid][relid][targetid]
  if not noderel[sourceid][relid]:
    del noderel[sourceid][relid]
  if not noderel[sourceid]:
    del noderel[sourceid]

  del nodebackrel[targetid][relid][sourceid]
  if not nodebackrel[targetid][relid]:
    del nodebackrel[targetid][relid]
  if not nodebackrel[targetid]:
    del nodebackrel[targetid]

  del nodereltarget[sourceid][targetid][relid]
  if not nodereltarget[sourceid][targetid]:
    del nodereltarget[sourceid][targetid]
  if not nodereltarget[sourceid]:
    del nodereltarget[sourceid]

  del noderelsource[targetid][sourceid][relid]
  if not noderelsource[targetid][sourceid]:
    del noderelsource[targetid][sourceid]
  if not noderelsource[targetid]:
    del noderelsource[targetid]

  nodeemptyhaschange = False

  if isnodeempty(sourceid):
    nodeempty.setdefault(sourceid)
    nodeemptyhaschange = True

  if isnodeempty(targetid):
    nodeempty.setdefault(targetid)
    nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty() 

  if relid not in rel: # we deleted the relationship above
    _delrel(relid)
  else:
    _saverel(relid)

###############################################################################

def remnoderel(sourceid, relid):

  if not sourceid or not relid:
    return

  _loadifnotloaded()

  if sourceid not in node or relid not in rel:
    return

  if sourceid not in rel[relid]:
    return

  for targetid in list(rel[relid][sourceid]):
    remnodereltarget(sourceid, relid, targetid)

###############################################################################

def remrel(relid):

  if not relid:
    return

  _loadifnotloaded()

  if relid not in rel:
    return

  for sourceid in list(rel[relid]):
    remnoderel(sourceid, relid)

###############################################################################

def renamenoderelprop(sourceid, relid, targetid, propid, newpropid):

  if propid == newpropid:
    return

  if not sourceid or not relid or not targetid or not propid or not newpropid:
    return

  _loadifnotloaded()

  if sourceid not in node or relid not in rel or targetid not in node:
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

  _saverel(relid)

###############################################################################

def renamerel(oldrelid, newrelid):

  if oldrelid == newrelid:
    return

  if not oldrelid or not newrelid:
    return

  _loadifnotloaded()

  if oldrelid not in rel:
    return

  rel.setdefault(newrelid, {})

  for sourceid in rel[oldrelid]:
    rel[newrelid].setdefault(sourceid, {})

    for targetid in rel[oldrelid][sourceid]:
      rel[newrelid][sourceid].setdefault(targetid, {})

      rel[oldrelid][sourceid][targetid].update(rel[newrelid][sourceid][targetid])

      nodebackrel[targetid].setdefault(newrelid, {}).update(nodebackrel[targetid][oldrelid])
      del nodebackrel[targetid][oldrelid]

      nodereltarget[sourceid][targetid].setdefault(newrelid, {}).update(nodereltarget[sourceid][targetid][oldrelid])
      del nodereltarget[sourceid][targetid][oldrelid]

      noderelsource[targetid][sourceid].setdefault(newrelid, {}).update(noderelsource[targetid][sourceid][oldrelid])
      del noderelsource[targetid][sourceid][oldrelid]

    noderel[sourceid].setdefault(newrelid, {}).update(noderel[sourceid][oldrelid])
    del noderel[sourceid][oldrelid]

  rel.setdefault(newrelid, {}).update(rel[oldrelid])
  del rel[oldrelid]

  backrel.setdefault(newrelid, {}).update(backrel[oldrelid])
  del backrel[oldrelid]

  _delrel(oldrelid)
  _saverel(newrelid)

###############################################################################

def inputnode(arg=None):

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

      if len(colsplit) == 1:
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
      raise Exception('relationship must have target')

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

###############################################################################

def setcolprop(colid, propid, proptype=None):

  if not colid or not propid:
    return

  _loadifnotloaded()

  colprop.setdefault(colid, {}).setdefault(propid)
  if proptype:
    colprop[colid][propid] = proptype

  _savecolprop()

###############################################################################

def remcolprop(colid, propid=None):

  if not colid:
    return
  
  _loadifnotloaded()

  if colid not in colprop:
    return

  if not propid:
    del colprop[colid]
    _savecolprop()
    return

  if propid not in colprop[colid]:
    return

  del colprop[colid][propid]

  if not colprop[colid]:
    del colprop[colid]

  _savecolprop()

###############################################################################

def inputcolprop(colid, propids=None):

  if not colid:
    return

  _loadifnotloaded()

  if colid not in colprop:
    return

  if colid not in col: # this means no node in collection
    return

  if not propids:
    propids = list(colprop[colid])

  elif isinstance(propids, str):
    propids = [propids]

  propids = [propid for propid in propids if propid in colprop[colid]]

  proptypes = { propid : eval(colprop[colid][propid]) if colprop[colid][propid] else (lambda x: x) for propid in propids }

  nodeids = list(col[colid])

  try:

    for nodeid in nodeids:
      for propid in propids:
        if nodeid in nodeprop and propid in nodeprop[nodeid]:
          continue

        ans = input(f"{nodeid}.{propid}: ").strip()

        if not ans: # skip this node
          continue

        setnodeprop(nodeid, propid, proptypes[propid](ans))
  
  except KeyboardInterrupt:
    print('')

###############################################################################

def inputnodesprop(nodeids, propid, proptype=None):

  nodeids = list(nodeids)

  def convert(value):
    try:
      return int(value)
    except ValueError:
      pass
    try:
      return float(value)
    except ValueError:
        pass
    try:
      return str(value)
    except ValueError:
      return value

  proptype = eval(proptype) if proptype else convert

  try:
    for nodeid in nodeids:
      
      ans = input(f"{nodeid}.{propid}: ").strip()
      if not ans:
        continue

      setnodeprop(nodeid, propid, proptype(ans))

  except KeyboardInterrupt:
    print('')

###############################################################################