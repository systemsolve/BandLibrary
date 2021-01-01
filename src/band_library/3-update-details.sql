begin;

create table library_source (
    id serial primary key,
    label varchar(200) not null,
    description text
);


alter table library_entry add column source_id integer null references library_source(id); 
alter table library_entry add column provider_id integer null references library_author(id); 
alter table library_entry add column digitised boolean not null default false;


commit;



