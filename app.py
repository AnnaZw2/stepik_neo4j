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
@app.route("/employees", methods=["POST"])
def create_employee():
    def create_employee():
        req_data = request.get_json()

        name = req_data.get("name")
        position = req_data.get("position")
        department = req_data.get("department")

        if not all([name, position, department]):
            return "Podano niepełne dane", 400

        query = """
            CREATE (e:Employee {name: $name, position: $position, department: $department})
            RETURN e.name AS name, e.position AS position, e.department AS department
        """

        with driver.session() as session:
            result = session.run(query, name=name, position=position, department=department)
            employee = dict(result.single())

        return jsonify(employee), 201

    @app.route("/employees/<int:employee_id>", methods=["PUT"])
    def update_employee(employee_id):
        name = request.json.get("name")
        position = request.json.get("position")
        department = request.json.get("department")

        query = """
            MATCH (e:Employee)
            WHERE ID(e) = $employee_id
            SET e.name = $name, e.position = $position, e.department = $department
            RETURN e.name AS name, e.position AS position, e.department AS department
        """

        with driver.session() as session:
            result = session.run(query, employee_id=employee_id, name=name, position=position, department=department)
            employee = dict(result.single())

        return {"employee": employee}

    @app.route("/employees/<id>", methods=["DELETE"])
    def delete_employee(id):
        query = """
            MATCH (e:Employee)
            WHERE ID(e) = toInt({id})
            OPTIONAL MATCH (d:Department)<-[:MANAGES]-(e)
            SET d.manager = NULL
            DELETE e, d
        """

        with driver.session() as session:
            session.run(query, id=id)

        return {"message": "Employee deleted"}

    @app.route("/departments", methods=["GET"])
    def get_departments():
        sort_by = request.args.get("sort_by")
        sort_order = request.args.get("sort_order")
        name = request.args.get("name")
        employees = request.args.get("employees")

        sort_clause = ""
        if sort_by and sort_order:
            sort_clause = f"ORDER BY d.{sort_by} {sort_order}"

        name_clause = ""
        if name:
            name_clause = f"AND d.name CONTAINS '{name}'"

        employees_clause = ""
        if employees:
            employees_clause = f"AND size((d)<-[:WORKS_IN]-()) = {employees}"

        query = f"""
            MATCH (d:Department)
            WHERE 1=1
            {name_clause}
            {employees_clause}
            {sort_clause}
            RETURN d.name AS name, size((d)<-[:WORKS_IN]-()) AS employees
        """

        with driver.session() as session:
            result = session.run(query)
            departments = [dict(record) for record in result]

        return {"departments": departments}


    @app.route("/employees/<employee_id>/subordinates", methods=["GET"])
    def get_subordinates(employee_id):
        query = """
            MATCH (e:Employee)-[:MANAGES]->(s:Employee)
            WHERE e.id = $employee_id
            RETURN s.name AS name, s.position AS position
        """

        with driver.session() as session:
            result = session.run(query, employee_id=employee_id)
            subordinates = [dict(record) for record in result]

        return {"subordinates": subordinates}



@app.route("/employees/<id>/department", methods=["GET"])
def get_employee_department(id):
    query = """
        MATCH (e:Employee)-[:BELONGS_TO]->(d:Department)
        WHERE e.id = $id
        RETURN d.name AS department_name, d.employee_count 
    """

    with driver.session() as session:
        result = session.run(query, id=id)
        department = dict(result.single())

    return {"department": department}
if __name__ == '__main__':
    app.run(port=5121,debug = True)
