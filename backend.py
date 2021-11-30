import flask
from flask.json import jsonify
import uuid
import robots
from robots import Warehouse, Robot, Block
games = {}

app = flask.Flask(__name__)

@app.route("/games", methods=["POST"])
def create():
    global games
    id = str(uuid.uuid4())
    games[id] = Warehouse()
    print("id: ", id)
    return "ok", 201, {'Location': f"/games/{id}"}


@app.route("/games/<id>", methods=["GET"])
def queryState(id):
    global model
    model = games[id]
    model.step()
    listaRobots = []
    #buscar todos los agentes del modelo y si son cajas o robots incluirlos en el arreglo de diccionarios a mandar al json
    for i in range(len(model.schedule.agents)):
        agent = model.schedule.agents[i]
        print("agentes: ", model.schedule.agents)
        print("agente tipo: ",type(agent))
        if type(agent) is robots.Robot:
            listaRobots.append({"x": agent.pos[0], "y": agent.pos[1], "tipo" : "Robot", "boxesInStack": - 1, "carringBoxes": agent.cargando})
        if type(agent) is robots.Block:
            listaRobots.append({"x": agent.pos[0], "y": agent.pos[1], "tipo" : agent.type, "boxesInStack": agent.boxes, "carringBoxes": False})
        else:
            i = i - 1
    return jsonify({"Items":listaRobots})

app.run(debug = True)