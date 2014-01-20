"""
  http://www.brokestream.com/fo.py.html

  Copyright (C) 2007 Ivan Tikhonov

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

  Ivan Tikhonov, kefeer@brokestream.com

"""


#############################
### types
#############################

class A(str):
    def __repr__(s):
        return s

class E(list):
    def copy(s):
        return E(s[:])

class U:
    pass
U = U()

class X:
    def __init__(s,p,n,a):
        s.p = p
        s.n = n
        s.a = a
        s.f = getattr(__import__(p,globals(),locals(),[n]),n)

    def __call__(s, st, ec, ep):
        if callable(s.f):
            if s.a == 0:
                st.append(s.f())
            else:
                a = st[-s.a:]
                del st[-s.a:]
                st.append(s.f(*a))
        else:
            st.append(s.f)

class M:
    def __init__(s,n,a):
        s.n = n
        s.a = a
    def __call__(s, st, ec, ep):
        a = st[-s.a:]
        del st[-s.a:]
        o = st.pop()
        st.append(getattr(o,s.n)(*a))

#############################
### built-ins
#############################

def fexit(st,ec,ep):
    ep[:]=[]

input_buf = ""

def finput(st,ec,ep):
    global input_buf
    from sys import stdin
    from os import O_NONBLOCK
    from fcntl import fcntl, F_SETFL

    fcntl(stdin.fileno(), F_SETFL, O_NONBLOCK)
    try:
        l = stdin.readline()
        l = input_buf + l
        if len(l) == 0:
            ec[:]=[atom2i('exit')]
        while '\n' in l:
            (c,l) = l.split('\n',1)
            ep.append(ec.copy())
            ec[:] = re(c)
        input_buf = l
    except IOError,e:
        if e.errno != 11:
            raise

def fdef(st,ec,ep):
    ':'
    i = ec.pop(0)
    code[i] = ec.copy()
    ec[:] = []

def ffrom(st,ec,ep):
    p = atoms[ec.pop(0)]
    n = atoms[ec.pop(0)]
    a = int(atoms[ec.pop(0)])
    w = ec.pop(0)
    code[w] = X(p,n,a)
    ec[:] = []

def fnumber(st,ec,ep):
    '#'
    st.append(int(atoms[ec.pop(0)]))

def fq(st,ec,ep):
    '?'
    if not st.pop(): ec[:] = []

def fdot(st,ec,ep):
    '.'
    print st

def fw(*args):
    for (x,y) in zip(atoms,code):
        if isinstance(y,E):
            print '%10s : %s' % (x,' '.join([atoms[z] for z in y]))
        elif isinstance(y,M):
            print '%10s : method %s %d' % (x,y.n,y.a)
        elif isinstance(y,X):
            print '%10s : from %s %s %d' % (x,y.p,y.n,y.a)
        elif y == U: pass
        else: print '%10s : %s' % (x,y)

def fpy(st,ec,ep):
    i = ec.pop(0)
    code[i] = eval(' '.join([atoms[x] for x in ec]))
    ec[:] = []

def fnop(*args):
    ''

def fmethod(st, ec, ep):
    n = atoms[ec.pop(0)]
    a = int(atoms[ec.pop(0)])
    w = ec.pop(0)
    code[w] = M(n,a)
    ec[:] = []

def fload(*args):
    st = []
    try: f = open('fo.source')
    except IOError,e:
        if e.errno == 2: return
        raise

    for l in f:
        ex(re(l[:-1]),st)

def fset(st,ec,ep):
    '!'
    code[ec.pop(0)] = st.pop()

def fcomma(st,ec,ep):
    ','
    v = st.pop()
    st[-1] = st[-1] + (v,)

def fdrop(st,ec,ep):
    st.pop()

def fsave(*args):
    f = open('fo.source-','w')
    for (n,c) in zip(atoms,code):
        if isinstance(c,M): s = 'method %s %d %s' % (c.n,c.a,n)
        elif isinstance(c,X): s = 'from %s %s %d %s' % (c.p,c.n,c.a,n)
        elif isinstance(c,E):
            s = ': %s %s' %(n, ' '.join([atoms[x] for x in c]))
        elif callable(c): continue # builtin
        elif c == U: continue
        else:
            try:
                r = repr(c)
                if c != eval(r): continue
                s = 'py %s %s' % (n,r)
            except:
                print 'can not store %s (%s)' % (n,repr(c))
        f.write(s+"\n")
    f.close
    from os import rename
    try: rename('fo.source','fo.source~')
    except: pass
    rename('fo.source-','fo.source')

def frstack(st,ec,ep):
    st.append(ep)

def fstack(st,ec,ep):
    st.append(st)

def fhello(*args):
    print "fo.py version unknown"
    print " (c) Ivan Tikhonov (kefeer@brokestream.com)"
    print " http://www.brokestream.com/wordpress/category/projects/fopy/"
    print " type w<enter> to see words defined, type exit<enter> to exit."

#############################

def name(x,y):
    if getattr(y,'__doc__',None) != None:
        return y.__doc__
    return x[1:]

x = [(A(name(x,y)),y) for x,y in locals().items() if x[0] == 'f']
atoms = [y[0] for y in x]
code = [y[1] for y in x]

atoms.append('|')
code.append(())

def add(n,c = U):
    atoms.append(n)
    code.append(c)
    return len(atoms) - 1

def atom2i(x):
    x = A(x)
    try: return atoms.index(x)
    except ValueError: return add(x)

def re(e):
    return E([atom2i(x) for x in e.split(' ')])

code[atom2i('init')] = re('input init')

def ex(e,st):
    ep = []
    ec = e.copy()
    while True:
        x = ec.pop(0)
        c = code[x]
        if callable(c): c(st,ec,ep)
        elif isinstance(c,E):
            if len(ec) > 0: ep.append(ec)
            ec = c.copy()
        elif c == U:
            print 'undefined:', atoms[x]
        else: st.append(c)
        if len(ec) == 0:
            try: ec = ep.pop()
            except: break

fload()
ex(re('hello init'), [])
fsave()
