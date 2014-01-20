#!/usr/bin/python2.5
import handy
import sys, os
import mailbox
import sqlite3
from email.utils import parseaddr, parsedate_tz, mktime_tz, formatdate
import cmd
import pdb
from cursor import Cursor, ListView
from storage import PySQLiteStorage

BOXNAME = "INBOX" #"mail/@ONE" #+ ".BATCH"
def connect():
    dbc = sqlite3.connect('thingmail.sdb')
    sto = PySQLiteStorage(dbc)
    return dbc, sto

ADDRESS = "sender name <sender@example.com>"

DBC, STO = connect()

# table names
CONTACT  = "contact"
MESSAGE  = "message"
OPCODE   = "opcode"
TICKET   = "ticket"
UACCOUNT = "uaccount"

ESC = chr(27)
def esc(code):
    return "%s[%im" % (ESC, code)
class ANSI(object):
    def reset(self): return esc(0)
    def bold(self): return esc(1)
    def red(self):   return esc(31)
    def blue(self): return esc(34)
    def magenta(self): return esc(35)
    def yellow(self): return esc(33)
    def cyan(self): return esc(36)
    def cls(self):     return "%s[2J" % ESC

class NOANSI(object):
    def __getattr__(self, x):
        return self
    def __call__(self):
        return ''

#ANSI=ANSI()
ANSI=NOANSI()

##########################################
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/134892
class _Getch:
    """
    Gets a single character from standard input.  Does not echo to the screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

##########################################

def quote(s):
    return "'%s'" % s.replace(r"'","''")

def setcolumns(msg, **kw):
    cur = DBC.cursor()
    meta = metadata(msg)
    keys = meta.keys()
    meta.update(kw)
    vals = [quote(meta[k]) for k in keys] # repr to quote
    sql = (
        """
        REPLACE INTO message (msgid, %s)
        VALUES ('%s', %s)
        """ % (','.join(keys),
               msg["message-id"],
               ','.join(vals)))
    print sql
    cur.execute(sql)
    DBC.commit()

def metadata(msg):
    return {}
    cur = DBC.cursor()
    cur.execute("SELECT user FROM message where msgid='%s'" % msg['message-id'])
    res = {'user':''}

    row = cur.fetchone()
    if row:
        u, = row
        res["user"]=u
    return res


def printMsg(msg):
    print
    print
    sys.stdout.write(ANSI.cls() +  ANSI.red())
    for key in ["From","Date","Subject"]:
        print "%s: %s" % (key,msg[key])

##     sys.stdout.write(ANSI.reset())
##     if msg.is_multipart():
##         sys.stdout.write( ANSI.magenta())
##         print '------'
##         for i, x in enumerate(msg.get_payload()):
##             ct = x.get("Content-Type", "unknown")
##             print i, ct
##             if ct.count("text/plain"):
##                 sys.stdout.write(ANSI.reset())
##                 print x.get_payload(decode=True)
##                 sys.stdout.write( ANSI.magenta())
##         print '------'
##     else:
##         print msg.get_payload(decode=True)

##     sys.stdout.write(ANSI.blue() + ANSI.bold())
    print metadata(msg), ANSI.reset()

class ThingShell(cmd.Cmd):
    prompt = ANSI.reset() + ANSI.bold() + "thing> " + ANSI.reset()
    cursor = 0
    mode = "message" # "list"
    immediate = False

    def __init__(self, msgs, *args):
        cmd.Cmd.__init__(self, *args)
        self.msgs = msgs
        self.cursor = Cursor(ListView(self.msgs))

    def do_EOF(self, arg):
        print "exit"
        sys.exit()
    def do_quit(self, arg): # quit
        sys.exit()
    def do_shell(self, arg):
        os.system(arg)
    def preloop(self):
        #self.disp();self.do_i('')
        pass

    def this(self):
        return self.msgs[self.cursor.position]

    def disp(self):
        if self.mode == "list":
            self.do_list('')
        else:
            printMsg(self.this())

    def do_disp(self, arg):
        printMsg(self.this())

    def do_windowtest(self, arg): # curses window test
        import curses
        from curses.wrapper import wrapper
        def getHeaders(stdscr):
            heads = ["To","CC","Subject"]
            curs = Cursor(ListView(heads))

            def redraw():
                for y, item in enumerate(heads):
                    stdscr.addstr(y,0, "%10s:" % item,
                                  curses.A_REVERSE if y == curs.position
                                  else curses.A_NORMAL)
                stdscr.move(curs.position, 12)
                stdscr.refresh()

            stdscr.addstr(len(heads),0,'-' * 20)
            redraw()

            #curses.newwin()

            while True:
                ch = stdscr.getch()
                if ch==27: break
                elif ch==curses.KEY_UP: curs.moveUp()
                elif ch==curses.KEY_DOWN: curs.moveDown()
                redraw()

        wrapper(getHeaders)
        self.disp()


    def do_compose(self, arg): # compose
        import tempfile
        t = tempfile.NamedTemporaryFile()
        t.write(handy.trim(
            """
            From: {0}
            To:
            Subject: test message

            """).format(ADDRESS))
        t.write(open("/home/sei/.signature").read())
        print >> t
        t.seek(0)
        os.system("emacs %s" % t.name)
        msg = t.read()
        handy.sendmail(msg)
        open("mail/sendysend", "a").write(msg)
        t.close()

    def do_prev(self, arg): # prev
        self.cursor.moveUp()
        self.disp()

    def do_next(self, arg): # next
        self.cursor.moveDown()
        self.disp()

    def do_h(self, arg): # hourly histogram
        os.system("clear")
        os.system('~/bin/oldest.py -h')

    def do_message(self, arg): # message view
        self.mode = "message"
        msg = self.this()

        if arg:
            path = [int(x) for x in arg.split()]
            node = msg
            path.reverse()
            while path:
                next = path.pop()
                try:
                    node = node.get_payload()[next]
                except Exception, e:
                    print e
                    return
            print node.get_payload() if hasattr(node,'get_payload') else node
        else:
            printMsg(msg)


    def do_jump(self, arg): # jump to message number
        try:
            self.cursor.position = int(arg)
            if self.cursor.position < 0: self.cursor = 0
            if self.cursor.position >= len(self.msgs):
                self.cursor.position = len(self.msgs)-1
        except Exception, e:
            print e
            return
        self.disp()

    def do_list(self, arg): # list view
        print ANSI.cls()
        self.mode = "list"
        for i, msg in enumerate(self.msgs):
            if i == self.cursor.position:
                print ANSI.bold() + ANSI.yellow() + "->" + ANSI.reset(),
            else: print "  ",
            meta = metadata(msg)

            stat = msg["X-Status"]
            print ("%s%s" %(("D" if "D" in stat else " "),
                            ("A" if "A" in stat else " "))),

            print "%5i" % i, msg['From'], ANSI.red(), msg['Subject'] + ANSI.reset(),
            if meta['user']:
                print ANSI.blue() + ANSI.bold() + meta['user'] + ANSI.reset()
            else:
                print

    def do_immediate(self, arg): # immediate vs prompt
        self.immediate = not self.immediate
        while self.immediate:
            ch = getch()
            if ord(ch)==13: ch = "m"
            meth = "do_%s" % ch
            if hasattr(self, meth):
                getattr(self,meth)('')

    def do_object(self, arg): # debug/work with user object
        user = metadata(self.this())['user']
        if user:
            c = CLERK
            o = c.matchOne(User, username=user)
            print "c=CLERK"
            print "o=%s" % o
            pdb.set_trace()

    def do_goto(self, arg): # ssh to user's machine
        user = metadata(self.this())['user']
        try:
            o = CLERK.matchOne(User, username=user)
            print user, '@', o.server.name
            os.system(o.server.name)
        except Exception, e:
            print e


    def do_pdb(self, arg): # debug
        msg = self.this()
        pdb.set_trace()

    def do_user(self, arg):
        setcolumns(self.this(), user=arg)

    def do_sql(self, arg):
        os.system("sqlite3 thingmail.sdb")


    def do_prep(self, arg):
        ensure_tickets(self.msgs)


def ask_integer(msg):
    while True:
        num = raw_input(ANSI.cyan() + msg + ANSI.reset())
        try: return int(num)
        except: print ANSI.red() + "invalid number"


def ensure_msgid(msg):
    msgid = msg["message-id"]
    if msgid:
        return msgid
    else:
        raise Exception(ANSI.red() + "no message id!" + ANSI.reset())

def ensure_contact(contact):
    name, email = parseaddr(contact)
    if not email:
        raise Exception("couldn't parse address: %s" % contact)
    try: row = STO.matchOne(CONTACT, address=email)
    except LookupError:
        raise
        return STO.store(CONTACT, address=email, note=name)

    if name and not row["note"]:
        row["note"]=name
        STO.store(CONTACT, **row)
    return row


def ensure_msgobject(msg):
    msgid = ensure_msgid(msg)
    try: mobj= STO.matchOne(MESSAGE, msgid=msgid)
    except LookupError:
        contactID = ensure_contactID(msg["From"])
        #@TODO: better handling of followups
        tcount = ask_integer("count of *NEW* issues in this email (use 0 for dupe/followup):")
        return STO.store(MESSAGE, msgid=msgid, subject=msg["subject"],
                         received = receivedDate(msg),
                         contactID=contactID, ticket_count=tcount)

    # @TODO: remove "update message" stuff.
    # (this section is just to fill in data that wasn't there in
    # earlier versions while I was developing.)
    update = False
    if msg["Subject"] and not mobj["subject"]:
        mobj["subject"] = msg["Subject"]
        update = True

    if msg["Received"] and not mobj["received"]:
        mobj["received"] = receivedDate(msg)
        update = True

    if update:
        STO.store(MESSAGE, **mobj)

    return mobj

def ensure_opcode(opcode):
    try: return STO.matchOne(OPCODE, opcode=opcode)
    except:
        print "need default priority for %s" % opcode
        return STO.store(OPCODE, opcode=opcode, priority=ask_priority())

def ensure_uaccount(username):
    try: return STO.matchOne(UACCOUNT, username=username)
    except:
        #@TODO: attempt to prepopulate server
        print "guessing server:"
        os.system("whichserver %s" % username)
        print
        s = raw_input("what is server for %s?" % username)
        return STO.store(UACCOUNT, username=username, server=s)

def ask_priority():
    return ask_integer("assign priority (1=high, 2=med, 3=low):")

def ensure_uaccountID(username):
    return ensure_uaccount(username)["ID"]

def ensure_opcodeID(opcode):
    return ensure_opcode(opcode)["ID"]

def ensure_contactID(contact):
    return ensure_contact(contact)["ID"]

def ensure_tickets(msglist):
    print len(msglist), "messages"

    for msg in msglist:
        printMsg(msg)
        mobj = ensure_msgobject(msg)
        print mobj

        mID = mobj["ID"]

        tickets = STO.match(TICKET, messageID=mID)
        needed  = mobj["ticket_count"] - len(tickets)
        assert needed >= 0, "had more tickets than expected!"
        if needed > 0:
            print len(tickets), "created so far:"
            # @TODO: denormalize ticket listing
            for t in tickets: print "    ",t
            print "need to define %s more tickets" % needed

            for i in range(needed):
                t = 1 + len(tickets) + i # so they start with 1 for us humans

                #@TODO: suggest matches for the the username
                print "to which account does issue %s pertain?" % t
                username = raw_input(ANSI.cyan() + "username:" + ANSI.reset())
                uID = ensure_uaccountID(username)

                print "what is the opcode for this issue?"
                #@TODO: readline for opcodes
                opcode = raw_input(ANSI.cyan() + "opcode:" + ANSI.reset())
                o = ensure_opcode(opcode)
                oID = o['ID']
                print "assign priority for ticket. default for this opcode is %s" % o["priority"]

#                 flow = -1
#                 while not (flow in range(4)):
#                     print "what is the flow state? (0:FLOW, 1:SNAG, 2:PRIVATE, 3:PUBLIC)"
#                     try:
#                         flow = int(raw_input(">"))
#                     except:
#                         print "bad value."

                STO.store(TICKET, messageID=mID, uaccountID=uID, opcodeID=oID,
                          status='open', priority=ask_priority()) #, flow=flow)

def receivedDate(msg):
    """
    extracts the date from the received header and converts to UTC
    """
    ds = msg["Received"].split(";")[-1].strip()
    return formatdate(mktime_tz(parsedate_tz(ds)))


if __name__=="__main__":

    from imaplib import IMAP4_SSL
    import highmap
    from config import username, password, server

    imap = IMAP4_SSL(server)
    imap.login(username, password)
    msglist = [msg for uid,msg in highmap.messages(imap, BOXNAME, True)]
    imap.close()

    #msglist = [msg for msg in mailbox.mbox(BOXNAME) if not msg.get("X-IMAP")]

    ensure_tickets(msglist)
    shell = ThingShell(msglist)

    cursor = shell.cursor
    shell.cmdloop()
