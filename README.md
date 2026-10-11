blackmail
=========

a console-based email client built with python and sqlite

## Status (2026 review)

Two-day spike from January 2014. No working client was ever assembled —
this repo is a SQLite mail-store schema (`blackmail.sql`: `message`,
`header`, `payload` tables with header strings interned through a `string`
table), a mailbox importer (`box2sdb.py`, which needs the never-committed
`local.py` to actually run), and two imported prototypes (`thingmail.py`, an
older Python-2.5 sketch targeting a different schema; `fo.py`, Ivan
Tikhonov's Forth-like stack language, never connected to anything).

Note: the original README also claimed Free Pascal, but there is no Pascal
anywhere in this repo — that part never happened.

The most reusable piece here is `cursor.py`: a tiny, dependency-free cursor
+ list-view abstraction with a Pine-style zoomable selection, small enough
to lift into any terminal UI.
