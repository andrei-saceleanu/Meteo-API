"""Tema 2 SPRC"""
import re
import json
from datetime import datetime
from os import getenv
from flask import Flask, Response, request
import psycopg2

app = Flask(__name__)

COUNTRY_COLS = ["id", "nume", "lat", "lon"]
CITY_COLS = ["id",  "idTara", "nume", "lat", "lon"]
TEMP_COLS = ["id", "valoare", "timestamp"]


db = psycopg2.connect(
    host="tema2_db",
    database=getenv("DB"),
    user=getenv("DB_USER"),
    password=getenv("DB_PASSWORD"),
    port=int(getenv("DB_PORT"))
)
cursor = db.cursor()

def check_types(vals, types):
    """
    Check appropriate datatype for payload content
    (e.g. city/country names should be strings)

    Parameters
    ----------
    vals: List[Any]
        values for which type is checked

    types: List[type]
        expected types for input values

    Returns
    -------
        res: bool
            True = expected type matches actual type
            *** if expected type is float, also accept integers
    """

    for i, elem in enumerate(vals):

        if types[i] == float and isinstance(elem, int):
            continue
        if not isinstance(elem, types[i]):
            return False

    return True

def check_date(date_string):
    """Check date format and validity"""
    if not date_string:
        return 0

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_string):
        return 1

    year, month, day = list(map(int, date_string.split("-")))
    status = 0
    try:
        _ = datetime(year=year, month=month, day=day)
    except ValueError:
        status = 2

    return status


@app.route("/api/countries", methods=["GET"])
def get_countries():
    """handle GET request for countries"""

    cursor.execute("SELECT * from Tari;")
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(COUNTRY_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )


@app.route("/api/countries", methods=["POST"])
def post_countries():
    """handle POST request for countries"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    # check all necessary fields were passed and no extra one was included
    target_cols = ["lat", "lon", "nume"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly lat, lon and country name"
        )

    if (not check_types(
            [
                data["lat"],
                data["lon"],
                data["nume"]
            ],
            [float, float, str]
        )):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    vals = ("("
            + ",".join(
                [
                    repr(data["nume"]),
                    str(data["lat"]),
                    str(data["lon"])
                ]
            )
            + ")")

    # check country name doesn't already exist (preserve unique constraint)
    cursor.execute(f"SELECT nume FROM Tari where nume={repr(data['nume'])};")
    if cursor.fetchone():
        return Response(
            status=409,
            response="Error: country name unique constraint violated"
        )

    table = "Tari(nume,lat,lon)"
    cursor.execute(f"INSERT INTO {table} VALUES {vals} RETURNING id;")
    last_id = cursor.fetchone()[0]
    db.commit()

    return Response(
        status=201,
        response=json.dumps({"id":last_id}),
        mimetype="application/json"
    )

@app.route("/api/countries/<int:req_id>", methods=["PUT"])
def put_countries(req_id):
    """handle PUT request for countries"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    # check all necessary fields were passed and no extra one was included
    target_cols = ["id", "lat", "lon", "nume"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly id, lat, lon and name"
        )

    if (not check_types(
            [
                data["id"],
                data["lat"],
                data["lon"],
                data["nume"]
            ],
            [int, float, float, str]
        )):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    if req_id != data["id"]:
        return Response(
            status=400,
            response="body and URL id don't match"
        )

    # check country id exists in corresponding DB relation
    cursor.execute(f"SELECT id FROM Tari where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for country not found"
        )

    # check country name to be updated doesn't already exist
    cursor.execute(f"SELECT nume FROM Tari where nume={repr(data['nume'])};")
    if cursor.fetchone():
        return Response(
            status=409,
            response="Error: country name unique constraint violated"
        )

    vals = ",".join(
                [
                    "nume=" + repr(data["nume"]),
                    "lat=" + str(data["lat"]),
                    "lon=" + str(data["lon"])
                ]
            )
    cursor.execute(f"UPDATE Tari SET {vals} WHERE id={req_id};")
    db.commit()

    return Response(
        status=200,
        response="DB updated with new country info"
    )

@app.route("/api/countries/<int:req_id>", methods=["DELETE"])
def delete_countries(req_id):
    """handle DELETE request for countries"""

    cursor.execute(f"SELECT id from Tari where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for country not found"
        )

    cursor.execute(f"DELETE FROM Tari WHERE id={req_id};")
    db.commit()

    return Response(
        status=200,
        response="DB updated with country of given id deleted"
    )

@app.route("/api/cities", methods=["GET"])
def get_cities():
    """handle GET request for cities"""

    cursor.execute("SELECT * from Orase;")
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(CITY_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )

@app.route("/api/cities/country/<int:req_id>", methods=["GET"])
def get_cities_by_country(req_id):
    """handle GET request for cities from a certain country"""

    cursor.execute(f"SELECT * from Orase WHERE idTara={req_id};")
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(CITY_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )

@app.route("/api/cities", methods=["POST"])
def post_cities():
    """handle POST request for cities"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    target_cols = ["lat", "lon", "nume", "idTara"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly lat, lon, name and id"
        )

    if (not check_types(
            [
                data["lat"],
                data["lon"],
                data["nume"],
                data["idTara"]
            ],
            [float, float, str, int]
        )):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    id_cond = f"idTara={data['idTara']}"
    name_cond = f"nume={repr(data['nume'])}"
    base_query = "SELECT idTara, nume FROM Orase"

    cursor.execute(f"{base_query} where {id_cond} AND {name_cond};")
    if cursor.fetchone():
        return Response(
            status=409,
            response="Error: (id, name) unique constraint violated"
        )

    cursor.execute("SELECT id from Tari;")
    country_ids = list(map(lambda elem:elem[0], cursor.fetchall()))

    if data["idTara"] not in country_ids:
        return Response(
            status=409,
            response="Error: FOREIGN KEY violation - unknown country id"
        )


    vals = ("("
            + ",".join(
                [
                    str(data["idTara"]),
                    repr(data["nume"]),
                    str(data["lat"]),
                    str(data["lon"])
                ]
            )
            + ")")

    table = "Orase(idTara,nume,lat,lon)"
    cursor.execute(f"INSERT INTO {table} VALUES {vals} RETURNING id;")

    last_id = cursor.fetchone()[0]
    db.commit()

    return Response(
        status=201,
        response=json.dumps({"id":last_id}),
        mimetype="application/json"
    )


@app.route("/api/cities/<int:req_id>", methods=["PUT"])
def put_cities(req_id):
    """handle PUT request for cities"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    target_cols = ["id", "lat", "lon", "nume", "idTara"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly appropriate fields"
        )

    if (not check_types(
            [
                data["id"],
                data["lat"],
                data["lon"],
                data["nume"],
                data["idTara"]
            ],
            [int, float, float, str, int]
        )):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    if req_id != data["id"]:
        return Response(
            status=400,
            response="body and URL id don't match"
        )

    cursor.execute(f"SELECT id FROM Orase where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for city not found"
        )


    id_cond = f"idTara={data['idTara']}"
    name_cond = f"nume={repr(data['nume'])}"
    base_query = "SELECT idTara, nume FROM Orase"

    cursor.execute(f"{base_query} where {id_cond} AND {name_cond};")
    if cursor.fetchone():
        return Response(
            status=409,
            response="Error: (id, name) unique constraint violated"
        )

    cursor.execute("SELECT id from Tari;")
    country_ids = list(map(lambda elem:elem[0], cursor.fetchall()))

    if data["idTara"] not in country_ids:
        return Response(
            status=409,
            response="Error: FOREIGN KEY violation - unknown country id"
        )

    vals = ",".join(
                [
                    "idTara=" + str(data["idTara"]),
                    "nume=" + repr(data["nume"]),
                    "lat=" + str(data["lat"]),
                    "lon=" + str(data["lon"])
                ]
            )
    cursor.execute(f"UPDATE Orase SET {vals} WHERE id={req_id};")
    db.commit()

    return Response(
        status=200,
        response="DB updated with new city info"
    )

@app.route("/api/cities/<int:req_id>", methods=["DELETE"])
def delete_cities(req_id):
    """handle DELETE request for cities"""

    cursor.execute(f"SELECT id from Orase where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for city not found"
        )

    cursor.execute(f"DELETE FROM Orase WHERE id={req_id};")
    db.commit()

    return Response(status=200,response="DB updated with city deleted")


@app.route("/api/temperatures", methods=["POST"])
def post_temperatures():
    """handle POST request for temperatures"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    target_cols = ["idOras", "valoare"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly city id and temp value"
        )

    if not check_types([data["idOras"], data["valoare"]], [int, float]):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    vals = ("("
            + ",".join(
                [
                    str(data["idOras"]),
                    str(data["valoare"])
                ]
            )
            + ")")

    cursor.execute("SELECT id from Orase;")
    city_ids = list(map(lambda elem:elem[0], cursor.fetchall()))
    if data["idOras"] not in city_ids:
        return Response(
            status=409,
            response="Error: FOREIGN KEY violation - unknown city id"
        )

    table = "Temperaturi(idOras, valoare)"
    cursor.execute(f"INSERT INTO {table} VALUES {vals} RETURNING id;")

    last_id = cursor.fetchone()[0]
    db.commit()

    return Response(
        status=201,
        response=json.dumps({"id":last_id}),
        mimetype="application/json"
    )

@app.route("/api/temperatures", methods=["GET"])
def get_temperatures():
    """handle GET request for temperatures"""

    # extract URL params (if not passed, defaults to None)
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    from_date = request.args.get("from", type=str)
    to_date = request.args.get("until", type=str)

    if check_date(from_date) == 1 or check_date(to_date) == 1:
        return Response(
            status=400,
            response="invalid date format, please use YYYY-MM-DD"
        )

    if check_date(from_date) == 2 or check_date(to_date) == 2:
        return Response(
            status=400,
            response="invalid date, please pass a correct day"
        )

    geo_conds = []  # geographic conditions(latitude and/or longitude)
    time_conds = [] # time conditions (entry date interval)

    # don't compare directly equality because of REAL type
    if lat:
        geo_conds.append(f"ABS(lat-{lat})<=0.001")
    if lon:
        geo_conds.append(f"ABS(lon-{lon})<=0.001")

    if from_date:
        time_conds.append(f"timestamp>={repr(from_date)}")
    if to_date:
        time_conds.append(f"timestamp<={repr(to_date)}")

    # merge conditions with AND
    time_conds = " AND ".join(time_conds)
    geo_conds = " AND ".join(geo_conds)

    # geographic conditions are used in a subquery in order to produce
    # a new variable city condition
    city_cond = ""
    if geo_conds:
        city_cond = f"idOras in (SELECT id FROM Orase WHERE {geo_conds})"

    # prepare appropriate query given the URL params
    table_cols = "id, valoare, TO_CHAR(timestamp, 'YYYY-MM-DD') timestamp"
    query = f"SELECT {table_cols} FROM Temperaturi"

    if geo_conds and time_conds:
        query += f" WHERE {city_cond} AND {time_conds};"
    elif geo_conds or time_conds:
        query += f" WHERE {city_cond}{time_conds};"
    else:
        query += ";"

    cursor.execute(query)
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(TEMP_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )


@app.route("/api/temperatures/cities/<int:req_id>", methods=["GET"])
def get_city_temperatures(req_id):
    """handle GET request for city temperatures"""

    from_date = request.args.get("from", type=str)
    to_date = request.args.get("until", type=str)

    if check_date(from_date) == 1 or check_date(to_date) == 1:
        return Response(
            status=400,
            response="invalid date format, please use YYYY-MM-DD"
        )

    if check_date(from_date) == 2 or check_date(to_date) == 2:
        return Response(
            status=400,
            response="invalid date, please pass a correct day"
        )

    time_conds = []

    if from_date:
        time_conds.append(f"timestamp>={repr(from_date)}")
    if to_date:
        time_conds.append(f"timestamp<={repr(to_date)}")

    time_conds = " AND ".join(time_conds)

    table_cols = "id, valoare, TO_CHAR(timestamp, 'YYYY-MM-DD') timestamp"
    query = f"SELECT {table_cols} FROM Temperaturi"

    if time_conds:
        query += f" WHERE idOras={req_id} AND {time_conds};"
    else:
        query += f" WHERE idOras={req_id}"

    cursor.execute(query)
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(TEMP_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )

@app.route("/api/temperatures/countries/<int:req_id>", methods=["GET"])
def get_country_temperatures(req_id):
    """handle GET request for country temperatures"""
    from_date = request.args.get("from", type=str)
    to_date = request.args.get("until", type=str)

    if check_date(from_date) == 1 or check_date(to_date) == 1:
        return Response(
            status=400,
            response="invalid date format, please use YYYY-MM-DD"
        )

    if check_date(from_date) == 2 or check_date(to_date) == 2:
        return Response(
            status=400,
            response="invalid date, please pass a correct day"
        )

    time_conds = []

    if from_date:
        time_conds.append(f"timestamp>={repr(from_date)}")
    if to_date:
        time_conds.append(f"timestamp<={repr(to_date)}")

    time_conds = " AND ".join(time_conds)
    city_cond = f"idOras in (SELECT id from Orase WHERE idTara = {req_id})"

    table_cols = "id, valoare, TO_CHAR(timestamp, 'YYYY-MM-DD') timestamp"
    query = f"SELECT {table_cols} FROM Temperaturi"

    if time_conds:
        query += f" WHERE {time_conds} AND {city_cond};"
    else:
        query += f" WHERE {city_cond};"

    cursor.execute(query)
    res = cursor.fetchall()

    records = []
    for elem in res:
        records.append({k:v for k, v in zip(TEMP_COLS, elem)})

    return Response(
        status=200,
        response=json.dumps(records),
        mimetype="application/json"
    )

@app.route("/api/temperatures/<int:req_id>", methods=["PUT"])
def put_temperatures(req_id):
    """handle PUT request for temperatures"""

    data = request.get_json()
    if not data:
        return Response(status=400, response="Error: No JSON format detected")

    target_cols = ["id", "idOras", "valoare"]
    all_fields_passed = all([key in data for key in target_cols])
    wrong_fields = any([key not in target_cols for key in data])

    if not all_fields_passed or wrong_fields:
        return Response(
            status=400,
            response="Error: please provide exactly id, city id and value"
        )

    if (not check_types(
            [
                data["id"],
                data["idOras"],
                data["valoare"]
            ],
            [int, int, float]
        )):
        return Response(
            status=400,
            response="Invalid data type detected for field"
        )

    if req_id != data["id"]:
        return Response(
            status=400,
            response="body and URL id don't match"
        )

    cursor.execute(f"SELECT id FROM Temperaturi where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for temperature not found"
        )


    vals = ",".join(
                [
                    "idOras=" + str(data["idOras"]),
                    "valoare=" + str(data["valoare"])
                ]
            )
    cursor.execute(f"UPDATE Temperaturi SET {vals} WHERE id={req_id};")
    db.commit()

    return Response(
        status=200,
        response="DB updated with new temp info"
    )

@app.route("/api/temperatures/<int:req_id>", methods=["DELETE"])
def delete_temperatures(req_id):
    """handle DELETE request for temperatures"""

    cursor.execute(f"SELECT id from Temperaturi where id={req_id}")
    if not cursor.fetchone():
        return Response(
            status=404,
            response="Requested id for city not found"
        )

    cursor.execute(f"DELETE FROM Temperaturi WHERE id={req_id};")
    db.commit()

    return Response(status=200,response="DB updated with temp deleted")

if __name__=="__main__":
    app.run("0.0.0.0",debug=True)
