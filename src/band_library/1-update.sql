begin;

create table library_country (
    id serial primary key,
    name text not null,
    isocode varchar(3) not null);

alter table library_author add column bornyear integer null;
alter table library_author add column diedyear integer null; 
alter table library_author add column country_id integer null references library_country(id); 
alter table library_author add column comments text null;

commit;



