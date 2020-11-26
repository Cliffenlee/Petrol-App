drop schema if exists petrol;
create schema petrol;
use petrol;

drop table if exists petrol;
create table `petrol` (
    `name` varchar (20) not null primary key,
    `rating` int,
    `storage` double default 0.0,
    `cost` double not null
);

insert into petrol (name, rating, cost)
values 
    ("Basic X1", 92, 2.09),
    ("Cool X2", 95, 2.13),
    ("Fantastic X3", 98, 2.59),
    ("Diesel", null, 1.76)
;

