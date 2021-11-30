#Realizado por:
#David Zárate López A01329785


from random import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.space import MultiGrid
from mesa.visualization.UserParam import UserSettableParameter
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid as PathGrid
from pathfinding.finder.a_star import AStarFinder

#Agente robot
class Robot(Agent):
  def __init__(self, model, pos, stackIndex):
    super().__init__(model.next_id(), model)
    self.pos = pos
    #se asigna el tipo robot a la clase
    self.type = "robot"
    #movimientos realizados por el robot
    self.movements = 0
    #numero de casillas limpiadas por el robot
    self.limpiadas = 0
    #se encuentra cargando una caja
    self.cargando = False
    self.travelingCoordinate = False
    self.path = []
    self.indexPath = 0
    self.endCoordinate = ()
    self.stackIndex = stackIndex

  def getAgent(self, agents, type):
    for agent in agents:
      if agent.type == type:
        return agent
    return ""

  def step(self):
    if self.cargando == False:
        self.indexPath = 0
        self.travelingCoordinate = False
        self.path = []
        #se elige al azar una posicion para que el robot avance
        next_moves = self.model.grid.get_neighborhood(self.pos, moore=True)
        next_move = self.random.choice(next_moves)
        while self.getAgent(self.model.grid[next_move[0]][next_move[1]], "robot") or self.getAgent(self.model.grid[next_move[0]][next_move[1]], "StackBlock"): 
          next_move = self.random.choice(next_moves)
        #el robot revisa si el bloque en el que esta se encuentra limpio, si no se encuentra limpio significa que tiene que cargar una caja
        clean = self.checkIfClean()
        if clean == False:
            self.cargando = True
            self.limpiadas += 1
        #si el robot todavia puede hacer movimientos y la casilla esta limpia significa que puede moverse
        if self.movements >= self.model.time:
            print("Se ha acabado el tiempo de ejecucion , teniendo un total de",  self.movements * self.model.robots,"movimientos")
        if(self.movements < self.model.time and clean and self.model.dirtyBlocks > 0):
            self.movements += 1
            self.model.grid.move_agent(self, next_move)
    else:
        if self.movements >= self.model.time:
            print("Se ha acabado el tiempo de ejecucion , teniendo un total de",  self.movements * self.model.robots,"movimientos")
        # si no existe un stack para apilar las cajas se debe crear uno
        if self.travelingCoordinate == False:
          #se obtiene la ruta del recorrido que realizara el robot, siendo el inicio su posicion y el final la casilla con el stack
          #si ya no hay casillas disponibles para poner cajas se despliega el siguiente mensaje, de lo contrario se elije un nuevo destino
          if len(self.model.cleanBlocksPositions) == 0:
            print("No se encuentran casillas para apilar las cajas")
          else:
            #se obtiene la coordenada final y el stack en esa posicion
            self.endCoordinate = self.model.cleanBlocksPositions[self.stackIndex]
            print(self.endCoordinate)
            stack = self.getAgent(self.model.grid[self.endCoordinate[0]][self.endCoordinate[1]], "CleanBlock")
            #si es la primera vez que se convierte la casilla a stack
            if stack != "":
              stack.changeToStack()
            else:
              # si ya existia un stack se busca el objeto con tipo stack
              stack = self.getAgent(self.model.grid[self.endCoordinate[0]][self.endCoordinate[1]], "StackBlock")
              # si ya no puede cargar cajas se tiene que generar un stack nuevo
              if stack.boxes >= 5:
                #se cambia a un indice que no colisione con los stacks de otros robots
                self.stackIndex += self.model.robots
                #si el indice esta fuera de rango del arreglo de posiciones limpias
                if self.stackIndex >= len(self.model.cleanBlocksPositions):
                  print("Todos los stacks ya estan siendo utilizados por otros robots")
                else:
                  self.endCoordinate = self.model.cleanBlocksPositions[self.stackIndex]
                  stack = self.getAgent(self.model.grid[self.endCoordinate[0]][self.endCoordinate[1]], "CleanBlock")
                  stack.changeToStack()
          
            self.path = self.getPath(self.pos, self.endCoordinate)
            self.travelingCoordinate = True
        else:
          stack = self.getAgent(self.model.grid[self.endCoordinate[0]][self.endCoordinate[1]], "StackBlock")
          if self.indexPath == len(self.path) - 1:
            self.cargando = False
            stack.boxes += 1
            if self.model.dirtyBlocks == 0:
              print("Se han limpiado todas las casillas sucias en un tiempo de ejecucion de ", self.movements,"movimientos, teniendo un total de", self.movements * self.model.robots)
          else:
            #si no se genero algun camino es porque el robot esta encerrado en cajas, por lo cual, cargara esa caja y otra mas para poder salir
            if len(self.path) == 0:
              self.cargando = False
              stack.boxes += 1
            else: 
              self.model.grid.move_agent(self, self.path[self.indexPath])
              self.indexPath += 1
              self.movements += 1
            
        
        
  
  #funcion auxiliar que revisa si la casilla donde se encuentra el robot esta limpia
  def checkIfClean(self):
    cellmates = self.model.grid.get_cell_list_contents([self.pos])
    for block in cellmates:
      if(block.type == "DirtyBlock"):
        block.changeToClean()
        block.limpio = True
        self.limpiadas += 1
        self.model.dirtyBlocks -= 1
        self.model.cleanBlocksPositions.append((self.pos[0],self.pos[1]))
        self.model.matrix[self.pos[0]][self.pos[1]] = 0
        if self.model.dirtyBlocks == 0:
          print("Se han limpiado todas las casillas sucias en un tiempo de ejecucion de ", self.movements,"movimientos, teniendo un total de", self.movements * self.model.robots)
        return False
      else:
        return True
  
  def getPath(self, startCoordinate, endCoordinate):
    grid = PathGrid(matrix=self.model.matrix)
    grid.cleanup()
    start = grid.node(startCoordinate[0], startCoordinate[1])
    end = grid.node(endCoordinate[0], endCoordinate[1])
    finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
    path, runs = finder.find_path(start, end, grid)
    return path

      


  

class Block(Agent):
  def __init__(self, model, pos,type, limpio):
    super().__init__(model.next_id(), model)
    self.pos = pos
    self.type = type
    self.limpio = limpio
    self.boxes = 0
    self.stack = 0

  def changeToClean(self):
    self.type = "CleanBlock"

  def changeToStack(self):
    self.type = "StackBlock"
    self.stack = True

#TENGO QUE CREAR UNA LISTA CON LAS POSICIONES DE LAS CASILLAS QUE SE ENCUENTRAN LIMPIAS
class Warehouse(Model):
  #se asignan las variables modificables por el usuario siendo filas, columnas, robots, tiempo de ejecucion y el numero de bloques sucios
  def __init__(self, rows = 10,columns = 10, robots = 5, time = 400, dirtyBlocks = 35):
    super().__init__()
    self.schedule = RandomActivation(self)
    self.rows = rows
    self.columns = columns
    self.robots = robots
    self.time = time
    self.dirtyBlocks = dirtyBlocks
    self.grid = MultiGrid(self.columns, self.rows, torus=False)
    self.matrix = []
    self.stackPositions = []
    self.stackNumber = -1
    self.cleanBlocksPositions = []
    #se crea una matriz de ceros para identificar las casillas sucias y limpias
    self.createMatrix()
    #se crean los robots y bloques tanto limpios como sucios para colocarse en el tablero
    self.placeRobots()
    self.placeDirtyBlocks()
    self.placeCleanBlocks()

  def step(self):
    self.schedule.step()
  

  #se crean los bloques sucios de manera aleatoria
  def placeDirtyBlocks(self):
    blocks = self.dirtyBlocks
    while blocks > 0:
      randomX = self.random.randint(0, self.rows-1)
      randomY = self.random.randint(0, self.columns-1)
      while self.matrix[randomX][randomY] == 0:
        randomX = self.random.randint(0, self.rows-1)
        randomY = self.random.randint(0, self.columns-1)
      block = Block(self,(randomY,randomX),"DirtyBlock", False)
      self.grid.place_agent(block, block.pos)
      self.schedule.add(block)
      self.matrix[randomX][randomY] = 0
      blocks -= 1

  #se crean los bloques limpios
  def placeCleanBlocks(self):
     for _,x,y in self.grid.coord_iter():
      if self.matrix[y][x] == 1:
        block = Block(self,(x,y), "CleanBlock", True)
        self.grid.place_agent(block, block.pos)
        self.cleanBlocksPositions.append((x,y))
        self.schedule.add(block)

  #se crea la matriz que contendra las casillas limpias y sucias
  def createMatrix(self):
    for _ in range(0,self.rows):
      zeros = []
      for j in range(0,self.columns):
        zeros.append(1)
      self.matrix.append(zeros)
  
  #se colocan los robots
  def placeRobots(self):
    stackIndex = 0
    for _ in range(0,self.robots):
      randomX = self.random.randint(0, self.rows-1)
      randomY = self.random.randint(0, self.columns-1)
      robot = Robot(self, (randomX, randomY), stackIndex)
      self.grid.place_agent(robot, robot.pos)
      self.schedule.add(robot)
      stackIndex += 1

#Agent portrayal permite rea
def agent_portrayal(agent):
  if(agent.type == "robot"):
    return {"Shape": "robot.png", "Layer": 0}
  elif(agent.type == "DirtyBlock"):
    return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "#495057", "Layer": 1}
  elif(agent.type == "CleanBlock"):
    return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "#ced4da", "Layer": 1}
  elif(agent.type == "StackBlock"):
    return {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Color": "black", "Layer": 1}

grid = CanvasGrid(agent_portrayal, 10, 10, 400, 400)
# server = ModularServer(Warehouse, [grid], "Warehouse", {})

# server.port = 8522
# server.launch()