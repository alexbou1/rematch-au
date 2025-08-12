#!/usr/bin/env python3
"""Main file that will determine the closest address in the GNAF database."""
import logging
import os
import re
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Tuple

import duckdb
from duckdb import DuckDBPyConnection
from rich.console import Console

from rematch_au.address_scorer import AddressScorer
from rematch_au.common import setup_logging
from rematch_au.models import GNAFAddress, SearchAddress
from rematch_au.utils import fetch_gnaf_address_from_cursor

PROG = Path(__file__).stem.replace("_", "-")
LOG = setup_logging(PROG, fresh=True)
LOG.setLevel(os.getenv("LOG_LEVEL", logging.INFO))

DATABASE_TABLE = "australian_full_addresses"
DUCKDB_FILE = "test_gnaf.db"

VALID_STATES = ("act", "nsw", "nt", "ot", "qld", "sa", "tas", "vic", "wa")

FIND_CLOSE_ADDRESS_QUERY = """
    WITH closest_suburbs AS (
        SELECT DISTINCT primary_loc_pid
        FROM suburb_lookup_{state}
        WHERE postcode = $2
    ),
    locality_streets AS (
        SELECT DISTINCT
            sl.street_locality_pid,
            sl.street_name,
            sl.street_full_name
        FROM street_lookup_{state} sl
        INNER JOIN closest_suburbs cs ON cs.primary_loc_pid = sl.locality_pid
    ),
    street_similarities AS (
        SELECT
            street_locality_pid,
            street_name,
            levenshtein($1, street_full_name) AS similarity
        FROM locality_streets
    ),
    best_street AS (
        SELECT street_name
        FROM street_similarities
        ORDER BY similarity
        OFFSET $3 LIMIT 1
    ),
    search_streets AS (
        SELECT DISTINCT street_locality_pid
        FROM street_similarities ss
        WHERE street_name = (SELECT street_name FROM best_street)
    )
    SELECT
        a.address_detail_pid,
        a.lot_number_prefix,
        a.lot_number,
        a.lot_number_suffix,
        a.flat_type,
        a.flat_number_prefix,
        a.flat_number,
        a.flat_number_suffix,
        a.level_type,
        a.level_number_prefix,
        a.level_number,
        a.level_number_suffix,
        a.number_first_prefix,
        a.number_first,
        a.number_first_suffix,
        a.number_last_prefix,
        a.number_last,
        a.number_last_suffix,
        a.street_name,
        a.street_type_code,
        a.street_suffix_type,
        a.postcode,
        a.address,
        a.alias_principal
    FROM australian_full_addresses_{state} a
    INNER JOIN search_streets ss USING (street_locality_pid);
"""


# ------------------------------------------------------------------------------
def process_cli_args() -> Namespace:
    """
    Process the command line arguments.

    :return:    The args namespace.
    """
    argp = ArgumentParser(
        prog=PROG,
        description="Find the closest matching addresses in the Australian GNAF dataset.",
    )

    argp.add_argument(
        "-n",
        action="store",
        metavar="COUNT",
        dest="limit",
        type=int,
        help=(
            "Maximum number of source addresses to use. A lower number may be"
            " used if the source relation has less rows. By default, not limit"
            " is imposed beyond that imposed by the source relation.."
        ),
    )

    argp.add_argument(
        "-r",
        "--relation",
        action="store",
        metavar="RELATION",
        default=DATABASE_TABLE,
        help="Fetch data from the specified relation (table or view) in the "
        f"duckdb database. Defaults to {DATABASE_TABLE}.",
    )

    # argp.add_argument("-v", "--version", action="version", version=__version__)

    argp.add_argument(
        "db_file",
        metavar="DB-FILE",
        default=DUCKDB_FILE,
        nargs="?",
        help="Name of the duckdb database file containing G-NAF data. "
        f"Defaults to {DUCKDB_FILE}.",
    )

    # argp.add_argument(
    #     "output",
    #     metavar="OUT-FILE",
    #     nargs="?",
    #     help=(
    #         "Name of the output file. The output is JSON, one object per line,"
    #         " containing the canonical address, the mutated address and some"
    #         " address data."
    #     ),
    # )

    args = argp.parse_args()

    if not is_sql_safe_object_name(args.relation):
        argp.error(f"Bad SQL relation name: {args.relation}")

    return args


# ------------------------------------------------------------------------------
def is_sql_safe_object_name(s: str) -> bool:
    """Check that a string is a safe database object name."""
    return bool(re.match(r"^\w+$", s))


# ------------------------------------------------------------------------------
def match_address(
    conn: DuckDBPyConnection, address: SearchAddress
) -> Optional[Tuple[GNAFAddress, float, float]]:
    """Match input address with GNAF database address."""
    with conn.cursor() as cursor:
        if address.state.lower() not in VALID_STATES:
            print(f"Address state {address.state} not a valid state")
            return GNAFAddress(), 0.0, 0.0

        processed_addresses = set()
        scores = []
        iterations = 0
        attempts = 0

        highest_score = 0
        highest_address = None
        while iterations < 1:
            start_time = time.perf_counter()
            query = FIND_CLOSE_ADDRESS_QUERY.format(state=address.state.lower())
            street_name = address.likely_street_name(attempts)
            if street_name is None:
                break
            cursor.execute(
                query,
                [
                    street_name,
                    address.postcode,
                    iterations,
                    # address.search_address_numbers,
                ],
            )
            # print(
            #     [
            #         street_name,
            #         address.postcode,
            #         iterations,
            #         address.search_address_numbers,
            #     ],
            # )
            end_time = time.perf_counter()
            print(f"Query time {end_time - start_time:.3f} seconds")

            scorer = AddressScorer(address)
            for address_candidate in fetch_gnaf_address_from_cursor(cursor):
                if address_candidate.address_detail_pid in processed_addresses:
                    continue

                total_score, sub_scorers = scorer.score(address_candidate)
                scores.append((total_score, sub_scorers, address_candidate))
                processed_addresses.add(address_candidate.address_detail_pid)

            # Sort candidates by score
            for i, (total_score, sub_scorers, address_candidate) in enumerate(
                scores
            ):
                if total_score > highest_score:
                    highest_score = total_score
                    highest_address = address_candidate

            if scores:
                print(highest_address.address)
            else:
                print("No matches found")

            iterations += 1

            if iterations >= 5:
                attempts += 1
                iterations = 0

            if highest_score > 4:
                break

        print(f"Searched from {len(scores)} addresses")
        scores.sort(key=lambda x: x[0], reverse=True)
        table = scorer.score_table()
        for total_score, sub_scorers, address_candidate in scores[:10]:
            values = [f"{s.weighted_score:.2f}" for s in sub_scorers]
            table.add_row(
                f"[ {total_score:.2f} ]",
                address_candidate.address_detail_pid,
                address_candidate.address,
                *values,
            )
        console = Console()
        console.print(table)
        # print(
        #     f"[{confidence:3.2f}] {address_candidate.address_detail_pid:14s}"
        #     f": {address_candidate.address:55s}",
        #     " ".join(
        #         [
        #             f"{p}={s:.2f}"
        #             for s, p in zip(
        #                 conf_scores,
        #                 ["PF", "FF", "PC", "NA", "NS", "HN", "PS", "SS"],
        #             )
        #         ]
        #     ),
        # )

        try:
            second_highest_diff = scores[0][0] - scores[1][0]
        except IndexError:
            second_highest_diff = 10
        match_confidence = min(highest_score / 4.2, 1) - 1 / (
            max(0.01, second_highest_diff) * 400
        )

        return highest_address, highest_score, match_confidence


# ------------------------------------------------------------------------------
def main() -> int:
    """Determine the closest address in the GNAF database."""
    setup_logging(PROG)
    args = process_cli_args()
    conn = duckdb.connect(args.db_file, read_only=True)

    address = SearchAddress(
        identifier="id",
        address="SUITE 2 LEVEL 4 14 QUEENS RD MELBOURNE VIC 3004",
        suburb="MELBOURNE",
        state="VIC",
        postcode="3004",
    )
    print("Searching for", address.address)
    print("Street:", address.likely_street_name)

    start_time = time.perf_counter()
    highest_match, highest_score, match_confidence = match_address(
        conn, address
    )
    print(match_confidence, highest_match.address)
    end_time = time.perf_counter()
    print(f"Found results in {end_time - start_time:.3f} seconds")

    return 0


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # import cProfile
    #
    # cProfile.run("main()", sort="cumtime")
    exit(main())  # Uncomment for debugging
    # try:
    #     exit(main())
    # except InterruptedError:
    #     LOG.info("Keyboard interrupt. exiting...")
    # except Exception as e:
    #     LOG.info("Error occurred during runtime: %s", e)
    # finally:
    #     LOG.info("Done")
