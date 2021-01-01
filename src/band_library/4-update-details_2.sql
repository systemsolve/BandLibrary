begin;

create table library_publisher (
    id serial primary key,
    name varchar(128) not null,
    country_id integer null references library_country(id),
    comments text
);

create table library_genre (
    id serial primary key,
    label varchar(32) not null,
    comments text
);


alter table library_entry add column publisher_id integer null references library_publisher(id);
alter table library_entry add column publication integer null;
alter table library_entry add column genre_id integer null references library_genre(id);

create table library_program_entry (
    id serial primary key,
    entry_id integer not null references library_entry(id),
    program_id integer not null references library_program(id)
);

commit;



