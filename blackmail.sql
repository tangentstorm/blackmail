create table string (
  id integer not null primary key,
  val string unique
);
create table message (
  id integer not null primary key,
  parts integer,
  msgid string
);
create table header (
  id   integer not null primary key,
  ord  integer,
  mid  integer references message,
  ksid integer references string,
  vsid integer references string
);
create table payload (
  id integer not null primary key,	
  mid integer references message,
  ord integer,
  typ string, -- mime type
  val string
);
