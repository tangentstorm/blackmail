"""
imports a mailbox to the sqlite database
"""
import os, sys, itertools as it
from local import sdb, cfg
from mailbox import mbox
from email.message import Message

MimeType = str

cur = sdb.cursor()


## sql helpers

def csv(args:[str])->str:
    """create a string of comma-separated values"""
    return ','.join(args)

def sepkv(d:dict)->([str],[object]):
    """keys and values for a dict, in matching order"""
    keys = d.keys()
    return keys, [d[k] for k in keys]

def ins(tbl:str, **kv):
    """sql insert into"""
    keys, vals = sepkv(kv)
    sql = ('insert into {0} ({1}) values ({2})'
           .format(tbl, csv(keys), csv('?' for e in keys)))
    cur.execute(sql, vals)
    return cur.lastrowid

def sel(tbl:str, key:str, **kv)->any:
    """sql select a key from a table"""
    keys, vals = sepkv(kv)
    sql = 'select {0} from {1} where {2}'.format(
        key, tbl, ' and '.join('{0}=?'.format(k) for k in keys))
    cur.execute(sql, vals)
    row = cur.fetchone()
    return row[0] if row else None

## assertion helpers

def Rs(e:type, s:str, *a):
    """the 'raise' statement as an expression"""
    raise e(s.format(*a))

def T(obj, typ):
    """type check assertion as an expression"""
    if isinstance(obj,typ): return obj
    else: Rs(TypeError, '{0} is not a {1}', repr(obj), typ)


## cache to speed up string normalization

_sids = {}
def sid(s:str)->int:
    """return id for given string"""
    if not ((s in _sids) or _sids.setdefault(s, sel('string', 'id', val=s))):
        _sids[s] = ins('string', val=T(s or '',str))
    return _sids[s]


## tools to deconstruct Message objects

def tup_enum(tups:[(any,)])->[(int,)+(any,)]:
    return ((i,)+tup for (i, tup) in enumerate(tups))

def flatten(m:(Message or str))->(MimeType, str):
    """flattens both plain text and sub-messages as strings"""
    return (m['content-type'], str(m)) if isinstance(m, Message) \
        else ('text/plain', m)

def parts(m:Message)->[(MimeType, str)]:
    """return the topmost payload level with sub-messages flattened"""
    return map(flatten, m.get_payload()) if m.is_multipart()\
        else [(m['content-type'], m.get_payload())]

def headers(m:Message)->[(str,str)]:
    for k, v in m.items(): yield (k, T(v,str))

def add_email(m:Message):
    """store message in db, normalizing headers and payload"""
    payload = list(parts(m))
    msgid = ins('message', parts=len(payload), msgid=m['message-id'])
    for i, typ, val in tup_enum(payload):
        ins('payload', mid=msgid, ord=i, typ=typ, val=val)
    for i, key, val in tup_enum(headers(m)):
        ins('header', mid=msgid, ord=i, ksid=sid(key), vsid=sid(val))


## main routine

if __name__=='__main__':
    box = mbox(cfg.boxname)
    for i,msg in enumerate(box):
        if msg['message-id']: add_email(msg)
        elif i==0: pass
        else: print(msg)
