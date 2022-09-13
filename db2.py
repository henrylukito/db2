from pathlib import Path
import yaml

dbpath = Path()
is_loaded = False

node = {}
col = {}

nodeempty = {}
nodecol = {}

###############################################################################

def reset():
  global is_loaded
  is_loaded = False

  node.clear()
  col.clear()

  nodeempty.clear()
  nodecol.clear()

###############################################################################

def load(dirpath=None):

  reset()

  if dirpath:
    global dbpath
    dbpath = Path(dirpath)
  
  (dbpath / 'collections').mkdir(parents=True, exist_ok=True)
  (dbpath / 'emptynodes.yml').touch(exist_ok=True)

  for filepath in (filepath for filepath in (dbpath/'collections').iterdir() if filepath.is_file() and filepath.suffix == '.yml'):
    col[filepath.stem] = dict.fromkeys(yaml.safe_load(filepath.read_text(encoding='utf-8')) or [])

  for colid in col:
    for nodeid in col[colid]:
      node.setdefault(nodeid)
      nodecol.setdefault(nodeid, {}).setdefault(colid)

  nodeempty.update(dict.fromkeys(yaml.safe_load((dbpath / 'emptynodes.yml').read_text(encoding='utf-8')) or []))

  nodeemptyhaschange = False

  for nodeid in list(nodeempty):
    if nodeid in node:
      del nodeempty[nodeid]
      nodeemptyhaschange = True

  if nodeemptyhaschange:
    _savenodeempty()

  node.update(nodeempty)

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

def isnodeempty(nodeid):

# check whether node is empty, not whether it's in nodeempty
# but whether it's in any of nodecol, nodeprop, etc
# this is usually called when removing node from nodecol, nodeprop etc
# to check whether node has become empty, so it can be put to nodeempty

  if not nodeid:
    return
  
  _loadifnotloaded()
  
  if nodeid in nodecol:
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
# since node might etc have col, need to etc clean up by calling remnodecol
# node might be empty node, so need to remove it from nodeempty

  if not nodeid:
    return

  _loadifnotloaded()

  if nodeid not in node:
    return

  if nodeid in nodecol:
    for colid in list(nodecol[nodeid]):
      remnodecol(nodeid, colid)

  if nodeid in nodeempty:
    del nodeempty[nodeid]
    _savenodeempty()

  del node[nodeid]

###############################################################################

def renamenode(oldnodeid, newnodeid):

# rename node if exist
# newnodeid might be new or it might already exist
# if already exist, we're kinda doing merge and then remove oldnodeid

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

  if not colid:
    return

  _loadifnotloaded()

  if colid not in col:
    return

  nodeemptyhaschange = False

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