create table australian_full_addresses as
select
    address_detail_pid,
    street_locality_pid,
    locality_pid,
    building_name,
    lot_number_prefix,
    lot_number,
    lot_number_suffix,
    flat_type,
    flat_number_prefix,
    flat_number,
    flat_number_suffix,
    level_type,
    level_number_prefix,
    level_number,
    level_number_suffix,
    number_first_prefix,
    number_first,
    number_first_suffix,
    number_last_prefix,
    number_last,
    number_last_suffix,
    street_name,
    street_class_code,
    street_class_type,
    street_type_code,
    street_suffix_code,
    street_suffix_type,
    locality_name,
    state_abbreviation,
    postcode,
    latitude,
    longitude,
    confidence,
    alias_principal,
    primary_secondary,
    regexp_replace(trim(concat_ws(
        ' ',
        --building_name,
        case when flat_number is null
            then concat(lot_number_prefix, lot_number, lot_number_suffix)
        end,
        concat(flat_type, ' ', flat_number_prefix, flat_number, flat_number_suffix),
        concat(level_type, ' ', level_number_prefix, level_number, level_number_suffix),
        case when number_last is null
            then concat(number_first_prefix, number_first, number_first_suffix)
            else concat(
                    number_first_prefix, number_first, number_first_suffix, '-',
                    number_last_prefix, number_last, number_last_suffix
                 )
        end,
        concat_ws(' ', street_name, street_type_code, street_suffix_type),
        locality_name,
        state_abbreviation,
        postcode
    )), '\s{2,}', ' ', 'g') as address
from australian_addresses
order by state_abbreviation;
