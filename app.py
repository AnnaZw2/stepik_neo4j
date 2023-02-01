from flask import Flask, request,jsonify
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password),database="neo4j")

@app.route("/employees", methods=["GET"])
def get_employees():
    sort_by = request.args.get("sort_by")
    sort_order = request.args.get("sort_order")
    name = request.args.get("name")
    position = request.args.get("position")

    sort_clause = ""
    if sort_by and sort_order:
        sort_clause = f"ORDER BY e.{sort_by} {sort_order}"

    name_clause = ""
    if name:
        name_clause = f"AND e.name CONTAINS '{name}'"

    position_clause = ""
    if position:
        position_clause = f"AND e.position CONTAINS '{position}'"

    query = f"""
        MATCH (e:Employee)
        WHERE 1=1
        {name_clause}
        {position_clause}
        {sort_clause}
        RETURN e.name AS name, e.position AS position
    """

    with driver.session() as session:
        result = session.run(query)
        employees = [dict(record) for record in result]

    return {"employees": employees}

@app.route("/employees", methods=["POST"])
def create_employee():
    name = request.json["name"]
    position = request.json["position"]

    query = """
        CREATE (e:Employee {name: $name, position: $position})
        RETURN e.name AS name, e.position AS position
    """

    with driver.session() as session:
        result = session.run(query, name=name, position=position)
        employee = dict(result.single())

    return {"employee": employee}
if __name__ == '__main__':
    app.run(port=5121,debug = True)
