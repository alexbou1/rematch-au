drop table if exists gnaf.suburb_lookup;
create table gnaf.suburb_lookup as
with postcode_lookup as (
    select distinct locality_pid, postcode
    from australian_full_addresses
), suburbs as (
    select distinct l.locality_pid as primary_loc_pid,
        l.locality_name as primary_loc_name,
        l.locality_pid as associated_loc_pid,
        l.locality_name as associated_loc_name,
        s.state_abbreviation,
        pl.postcode,
        'PRIMARY' as row_type,
        concat_ws(' ', l.locality_name, s.state_abbreviation, pl.postcode) as suburb
    from locality l
    join state s on s.state_pid = l.state_pid
    join postcode_lookup pl on pl.locality_pid = l.locality_pid

), neighbours as (
    select distinct l.locality_pid as primary_loc_pid,
        l.locality_name as primary_loc_name,
        l2.locality_pid as associated_loc_pid,
        l2.locality_name as associated_loc_name,
        s.state_abbreviation,
        pl.postcode,
        'NEIGHBOUR' as row_type,
        concat_ws(' ', l2.locality_name, s.state_abbreviation, pl.postcode) as suburb
    from locality l
    join locality_neighbour ln on ln.locality_pid = l.locality_pid
    join locality l2 on ln.neighbour_locality_pid = l2.locality_pid
    join state s on s.state_pid = l2.state_pid
    join postcode_lookup pl on pl.locality_pid = l2.locality_pid
)
select * from suburbs
union all
select * from neighbours;

insert into gnaf.suburb_lookup
select distinct l.primary_loc_pid as primary_loc_pid,
    l.primary_loc_name as primary_loc_name,
    la.locality_pid as associated_loc_pid,
    la.name as associated_loc_name,
    l.state_abbreviation,
    l.postcode,
    'ALIAS' as row_type,
    concat_ws(' ', la.name, l.state_abbreviation, l.postcode) as suburb
from gnaf.suburb_lookup l
join locality_alias la on la.locality_pid = l.primary_loc_pid;
create index idx_suburb_lookup_primary_loc_pid on gnaf.suburb_lookup (primary_loc_pid);
-- Created 'gnaf.suburb_lookup' table;

drop table if exists gnaf.street_lookup;
create table gnaf.street_lookup as
with postcode_lookup as (
    select distinct primary_loc_pid as locality_pid, associated_loc_name as locality_name, state_abbreviation, postcode, row_type
    from gnaf.suburb_lookup
    where row_type in ('PRIMARY', 'ALIAS')
)
select distinct sc.street_locality_pid,
       sc.street_name,
       sc.street_type_code,
       sc.street_type,
       sc.street_suffix_code,
       sc.street_suffix,
       sc.locality_pid,
       sc.variant,
       pl.locality_name,
       pl.state_abbreviation,
       pl.postcode,
       pl.row_type as suburb_type,
       sc.street_full_name,
       sc.gnaf_street_pid,
       concat_ws(' ', sc.street_full_name, pl.locality_name, pl.state_abbreviation, pl.postcode) as address_suffix
from (
    select sl.*,
           sl.street_type_code as street_type,
           sl.street_suffix_code AS street_suffix,
           'V1' as variant,
           sl.gnaf_street_pid,
           concat_ws(' ', sl.street_name, sl.street_type_code, sl.street_suffix_code) as street_full_name
    from street_locality sl
    union
    select sl.*,
           sl.street_type_code as street_type,
           ss.name AS street_suffix,
           'V2' as variant,
           sl.gnaf_street_pid,
           concat_ws(' ', sl.street_name, sl.street_type_code, ss.name) as street_full_name
    from street_locality sl
    left join street_suffix_aut ss ON sl.street_suffix_code = ss.code
    where ss.name is not null
    union
    select sl.*,
           st.name as street_type,
           sl.street_suffix_code AS street_suffix,
           'V3' as variant,
           sl.gnaf_street_pid,
           concat_ws(' ', sl.street_name, st.name, sl.street_suffix_code) as street_full_name
    from street_locality sl
    join street_type_aut st ON sl.street_type_code = st.code
    where st.name is not null
    union
    select sl.*,
           st.name as street_type,
           ss.name AS street_suffix,
           'V4' as variant,
           sl.gnaf_street_pid,
           concat_ws(' ', sl.street_name, st.name, ss.name) as street_full_name
    from street_locality sl
    join street_type_aut st ON sl.street_type_code = st.code
    left join street_suffix_aut ss ON sl.street_suffix_code = ss.code
    where ss.name is not null and st.name is not null
) sc
join postcode_lookup pl on pl.locality_pid = sc.locality_pid;
create index idx_street_lookup_locality_pid on gnaf.street_lookup (locality_pid);
-- Created 'gnaf.street_lookup' table;

drop table if exists gnaf.suburb_lookup_vic;
create table gnaf.suburb_lookup_vic as select * from gnaf.suburb_lookup where state_abbreviation = 'VIC' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_vic_primary_loc_pid on gnaf.suburb_lookup_vic (primary_loc_pid);
create index idx_suburb_lookup_vic_postcode on gnaf.suburb_lookup_vic (postcode);
-- Created 'gnaf.suburb_lookup_vic' table;

drop table if exists gnaf.suburb_lookup_nsw;
create table gnaf.suburb_lookup_nsw as select * from gnaf.suburb_lookup where state_abbreviation = 'NSW' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_nsw_primary_loc_pid on gnaf.suburb_lookup_nsw (primary_loc_pid);
create index idx_suburb_lookup_nsw_postcode on gnaf.suburb_lookup_nsw (postcode);
-- Created 'gnaf.suburb_lookup_nsw' table;

drop table if exists gnaf.suburb_lookup_act;
create table gnaf.suburb_lookup_act as select * from gnaf.suburb_lookup where state_abbreviation = 'ACT' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_act_primary_loc_pid on gnaf.suburb_lookup_act (primary_loc_pid);
create index idx_suburb_lookup_act_postcode on gnaf.suburb_lookup_act (postcode);
-- Created 'gnaf.suburb_lookup_act' table;

drop table if exists gnaf.suburb_lookup_qld;
create table gnaf.suburb_lookup_qld as select * from gnaf.suburb_lookup where state_abbreviation = 'QLD' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_qld_primary_loc_pid on gnaf.suburb_lookup_qld (primary_loc_pid);
create index idx_suburb_lookup_qld_postcode on gnaf.suburb_lookup_qld (postcode);
-- Created 'gnaf.suburb_lookup_qld' table;

drop table if exists gnaf.suburb_lookup_sa;
create table gnaf.suburb_lookup_sa as select * from gnaf.suburb_lookup where state_abbreviation = 'SA' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_sa_primary_loc_pid on gnaf.suburb_lookup_sa (primary_loc_pid);
create index idx_suburb_lookup_sa_postcode on gnaf.suburb_lookup_sa (postcode);
-- Created 'gnaf.suburb_lookup_sa' table;

drop table if exists gnaf.suburb_lookup_tas;
create table gnaf.suburb_lookup_tas as select * from gnaf.suburb_lookup where state_abbreviation = 'TAS' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_tas_primary_loc_pid on gnaf.suburb_lookup_tas (primary_loc_pid);
create index idx_suburb_lookup_tas_postcode on gnaf.suburb_lookup_tas (postcode);
-- Created 'gnaf.suburb_lookup_tas' table;

drop table if exists gnaf.suburb_lookup_wa;
create table gnaf.suburb_lookup_wa as select * from gnaf.suburb_lookup where state_abbreviation = 'WA' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_wa_primary_loc_pid on gnaf.suburb_lookup_wa (primary_loc_pid);
create index idx_suburb_lookup_wa_postcode on gnaf.suburb_lookup_wa (postcode);
-- Created 'gnaf.suburb_lookup_wa' table;

drop table if exists gnaf.suburb_lookup_nt;
create table gnaf.suburb_lookup_nt as select * from gnaf.suburb_lookup where state_abbreviation = 'NT' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_nt_primary_loc_pid on gnaf.suburb_lookup_nt (primary_loc_pid);
create index idx_suburb_lookup_nt_postcode on gnaf.suburb_lookup_nt (postcode);
-- Created 'gnaf.suburb_lookup_nt' table;

drop table if exists gnaf.suburb_lookup_ot;
create table gnaf.suburb_lookup_ot as select * from gnaf.suburb_lookup where state_abbreviation = 'OT' order by postcode, primary_loc_pid;
create index idx_suburb_lookup_ot_primary_loc_pid on gnaf.suburb_lookup_ot (primary_loc_pid);
create index idx_suburb_lookup_ot_postcode on gnaf.suburb_lookup_ot (postcode);
-- Created 'gnaf.suburb_lookup_ot' table;

drop table if exists gnaf.street_lookup_vic;
create table gnaf.street_lookup_vic as select * from gnaf.street_lookup where state_abbreviation = 'VIC' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_vic_locality_pid on gnaf.street_lookup_vic (locality_pid);
create index idx_street_lookup_vic_street_name on gnaf.street_lookup_vic (street_name);
create index idx_street_lookup_vic_street_locality_pid on gnaf.street_lookup_vic (street_locality_pid);
-- Created 'gnaf.street_lookup_vic' table;

drop table if exists gnaf.street_lookup_nsw;
create table gnaf.street_lookup_nsw as select * from gnaf.street_lookup where state_abbreviation = 'NSW' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_nsw_locality_pid on gnaf.street_lookup_nsw (locality_pid);
create index idx_street_lookup_nsw_street_name on gnaf.street_lookup_nsw (street_name);
create index idx_street_lookup_nsw_street_locality_pid on gnaf.street_lookup_nsw (street_locality_pid);
-- Created 'gnaf.street_lookup_nsw' table;

drop table if exists gnaf.street_lookup_act;
create table gnaf.street_lookup_act as select * from gnaf.street_lookup where state_abbreviation = 'ACT' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_act_locality_pid on gnaf.street_lookup_act (locality_pid);
create index idx_street_lookup_act_street_name on gnaf.street_lookup_act (street_name);
create index idx_street_lookup_act_street_locality_pid on gnaf.street_lookup_act (street_locality_pid);
-- Created 'gnaf.street_lookup_act' table;

drop table if exists gnaf.street_lookup_qld;
create table gnaf.street_lookup_qld as select * from gnaf.street_lookup where state_abbreviation = 'QLD' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_qld_locality_pid on gnaf.street_lookup_qld (locality_pid);
create index idx_street_lookup_qld_street_name on gnaf.street_lookup_qld (street_name);
create index idx_street_lookup_qld_street_locality_pid on gnaf.street_lookup_qld (street_locality_pid);
-- Created 'gnaf.street_lookup_qld' table;

drop table if exists gnaf.street_lookup_sa;
create table gnaf.street_lookup_sa as select * from gnaf.street_lookup where state_abbreviation = 'SA' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_sa_locality_pid on gnaf.street_lookup_sa (locality_pid);
create index idx_street_lookup_sa_street_name on gnaf.street_lookup_sa (street_name);
create index idx_street_lookup_sa_street_locality_pid on gnaf.street_lookup_sa (street_locality_pid);
-- Created 'gnaf.street_lookup_sa' table;

drop table if exists gnaf.street_lookup_tas;
create table gnaf.street_lookup_tas as select * from gnaf.street_lookup where state_abbreviation = 'TAS' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_tas_locality_pid on gnaf.street_lookup_tas (locality_pid);
create index idx_street_lookup_tas_street_name on gnaf.street_lookup_tas (street_name);
create index idx_street_lookup_tas_street_locality_pid on gnaf.street_lookup_tas (street_locality_pid);
-- Created 'gnaf.street_lookup_tas' table;

drop table if exists gnaf.street_lookup_wa;
create table gnaf.street_lookup_wa as select * from gnaf.street_lookup where state_abbreviation = 'WA' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_wa_locality_pid on gnaf.street_lookup_wa (locality_pid);
create index idx_street_lookup_wa_street_name on gnaf.street_lookup_wa (street_name);
create index idx_street_lookup_wa_street_locality_pid on gnaf.street_lookup_wa (street_locality_pid);
-- Created 'gnaf.street_lookup_wa' table;

drop table if exists gnaf.street_lookup_nt;
create table gnaf.street_lookup_nt as select * from gnaf.street_lookup where state_abbreviation = 'NT' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_nt_locality_pid on gnaf.street_lookup_nt (locality_pid);
create index idx_street_lookup_nt_street_name on gnaf.street_lookup_nt (street_name);
create index idx_street_lookup_nt_street_locality_pid on gnaf.street_lookup_nt (street_locality_pid);
-- Created 'gnaf.street_lookup_nt' table;

drop table if exists gnaf.street_lookup_ot;
create table gnaf.street_lookup_ot as select * from gnaf.street_lookup where state_abbreviation = 'OT' order by locality_pid, street_name, street_locality_pid;
create index idx_street_lookup_ot_locality_pid on gnaf.street_lookup_ot (locality_pid);
create index idx_street_lookup_ot_street_name on gnaf.street_lookup_ot (street_name);
create index idx_street_lookup_ot_street_locality_pid on gnaf.street_lookup_ot (street_locality_pid);
-- Created 'gnaf.street_lookup_ot' table;

drop table if exists gnaf.australian_full_addresses_vic;
create table gnaf.australian_full_addresses_vic as select * from australian_full_addresses where state_abbreviation = 'VIC' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_vic add primary key (address_detail_pid);
create index idx_australian_full_addresses_vic_street_locality_pid on gnaf.australian_full_addresses_vic (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_vic' table;

drop table if exists gnaf.australian_full_addresses_nsw;
create table gnaf.australian_full_addresses_nsw as select * from australian_full_addresses where state_abbreviation = 'NSW' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_nsw add primary key (address_detail_pid);
create index idx_australian_full_addresses_nsw_street_locality_pid on gnaf.australian_full_addresses_nsw (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_nsw' table;

drop table if exists gnaf.australian_full_addresses_act;
create table gnaf.australian_full_addresses_act as select * from australian_full_addresses where state_abbreviation = 'ACT' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_act add primary key (address_detail_pid);
create index idx_australian_full_addresses_act_street_locality_pid on gnaf.australian_full_addresses_act (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_act' table;

drop table if exists gnaf.australian_full_addresses_qld;
create table gnaf.australian_full_addresses_qld as select * from australian_full_addresses where state_abbreviation = 'QLD' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_qld add primary key (address_detail_pid);
create index idx_australian_full_addresses_qld_street_locality_pid on gnaf.australian_full_addresses_qld (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_qld' table;

drop table if exists gnaf.australian_full_addresses_sa;
create table gnaf.australian_full_addresses_sa as select * from australian_full_addresses where state_abbreviation = 'SA' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_sa add primary key (address_detail_pid);
create index idx_australian_full_addresses_sa_street_locality_pid on gnaf.australian_full_addresses_sa (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_sa' table;

drop table if exists gnaf.australian_full_addresses_tas;
create table gnaf.australian_full_addresses_tas as select * from australian_full_addresses where state_abbreviation = 'TAS' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_tas add primary key (address_detail_pid);
create index idx_australian_full_addresses_tas_street_locality_pid on gnaf.australian_full_addresses_tas (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_tas' table;

drop table if exists gnaf.australian_full_addresses_wa;
create table gnaf.australian_full_addresses_wa as select * from australian_full_addresses where state_abbreviation = 'WA' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_wa add primary key (address_detail_pid);
create index idx_australian_full_addresses_wa_street_locality_pid on gnaf.australian_full_addresses_wa (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_wa' table;

drop table if exists gnaf.australian_full_addresses_nt;
create table gnaf.australian_full_addresses_nt as select * from australian_full_addresses where state_abbreviation = 'NT' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_nt add primary key (address_detail_pid);
create index idx_australian_full_addresses_nt_street_locality_pid on gnaf.australian_full_addresses_nt (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_nt' table;

drop table if exists gnaf.australian_full_addresses_ot;
create table gnaf.australian_full_addresses_ot as select * from australian_full_addresses where state_abbreviation = 'OT' order by street_locality_pid, locality_pid, number_first;
alter table gnaf.australian_full_addresses_ot add primary key (address_detail_pid);
create index idx_australian_full_addresses_ot_street_locality_pid on gnaf.australian_full_addresses_ot (street_locality_pid);
-- Created 'gnaf.australian_full_addresses_ot' table;
