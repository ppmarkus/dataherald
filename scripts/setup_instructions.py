"""

    This script is used to upload instructions to DH.

    Instructions are passed directly to the engine and can be used to steer the engine to generate SQL that is more in line with your business logic.
    
    It reads the data from the config database.
    
    The database has the following columns
    select id, DB, Instructions luser, lupdate from darwin.marvin_config_instructions;
    
    The db_alias will default to 'hkg02p'

    1. Query the database for the list of golden records
    2. Loop through the database configuration file and construct the REST API call
    3. Run the REST API call to create the database in Dataherald

  """

import json
import os
import sys

import requests
from rh_python_common import db

from MongoDB import MongoDB

# constants. TODO: move to a config file
DATAHERALD_REST_API_URL = "http://localhost"

endpoint_url: str = f"{DATAHERALD_REST_API_URL}/api/v1/instructions"


def escape_quotes(s: str) -> str:
    return s.replace("'", "''")


def add_instruction(payload: list):
    """Add a single instruction to the database

    Args:
        db_connection_id (str): the db_connection_id to apply golden record to
        instruction (str): the instruction
    """

    # print the payload
    print("payload: ")
    print(json.dumps(payload, indent=4, sort_keys=True))

    r = requests.post(endpoint_url, json=payload, headers={
                      "Content-Type": "application/json", "Accept": "application/json"}, timeout=300)
    print(r.status_code)
    print(r.text)

    print()


def run():
    # 1. Query the database for the list of Instructions
    qry = f"""
      select DB, Instruction from darwin.marvin_config_instructions;
    """
    instructions_df = db.query_hkg02p(qry)

    # 2. Loop through the database configuration file and construct the REST API call
    api_payload = []
    for index, row in instructions_df.iterrows():
        print(f"index: {index}")
        print(f"row: {row}")
        print(f"row['DB']: {row['DB']}")
        print(f"row['Instruction']: {row['Instruction']}")
        db_alias = row['DB']

        # get the db_connection_id from the mongo database /
        mongo = MongoDB()
        db_id = mongo.get_db_connection_id_for_db_alias(db_alias)
        mongo.close()

        if db_id is None:
            print(f"db_alias: {db_alias} not found in database_connections")
            continue

        Instruction = row["Instruction"]

        api_payload.append(
            {"db_connection_id": db_id, "instruction": Instruction})

    if len(api_payload) == 0:
        print("No Instructions found in database")
        return
    add_instruction(api_payload)


if __name__ == "__main__":
    # read in the database configuration file but use the default if not provided
    print("################################################################################")
    print("                            Setup Instruction")
    print("################################################################################")
    print(f"Current working directory: {os.getcwd()}")

    run()