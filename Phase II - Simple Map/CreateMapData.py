
"""
This python script will parse the .tmx file and extract the map layers
from it.  The layers will be processed to generate the following outputs
as CSV files:

1. A list of the "rooms" in the map.  Any floor tile not in a specific
   "room" will be allocated to "HALLWAY".
2. A graph of the rooms, including the connection points between
   each room.

NOTE:
1.  The origin of the pixel position in Cocos2d-X is the BOTTOM LEFT.
2.  The origin in Tiled is the TOP LEFT.  Internally, the data is
    stored with the Tiled origin.  When it is emitted, it is converted
    to the target format.
"""

import os

from lxml import etree
from PIL import Image




class MapData(object):
    # Some constants used in the class.
    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
    FLIPPED_VERTICALLY_FLAG = 0x40000000
    FLIPPED_DIAGONALLY_FLAG = 0x20000000
    EXPECTED_LAYERS = ["Floor",
                       "Walls",
                       "Objects",
                       "Doors",
                       "Door_Activators",
                       "Use_Markers",
                       "Blocked"]
    EXPECTED_GAME_OBJECTS = [
        "ARMORY",
        "CARGO",
        "COMMON_TABLE",
        "COMPUTER_CONTROLS",
        "COMPUTER_CORE",
        "CREW_CONTROLS",
        "CRYOSLEEP",
        "DANCE_FLOOR",
        "DRONE_BAY",
        "ENGINES",
        "ENGINE_CONTROLS",
        "ENTERTAINMENT_CENTER",
        "FOOD_SERVICE",
        "HEALING_PLATFORM",
        "LOCKER",
        "MAIN_VIEWSCREEN",
        "MEDICAL_CABINET",
        "SHUTTLE",
        "SHUTTLE_GEN",
        "SPARE_PARTS",
        "TELEPORT",
        "TERMINAL",
        "WORK_BENCH",
    ]

    # Constructor
    def __init__(self):
        self.SetDefaults()

    # Default values for all the internals.
    def SetDefaults(self):
        # Set some default values for basic map data.
        self.tileWidth = 0
        self.tileHeight = 0
        self.mapWidth = 0
        self.mapHeight = 0
        self.subjectID = 0

        # ---------------------------------------------------
        # The following variables are used to
        # hold the raw data obtained from the XML file.
        # ---------------------------------------------------

        # The XML Tree used to hold the original file
        # data.  Set to None by default.
        self.tree = None
        # A dictionary with each piece of node information,
        # keyed by its node index.
        self.nodeDict = {}
        # A dictionary with each piece of room information
        # keyed by its room name
        self.roomObjectDict = {}
        # A dictionary of the tileset used for the map,
        # keyed by the tileID
        self.tileDict = {}
        # A dictionary containing a tuple of the index, cellX, and
        # cellY for each cell that in the room.
        self.roomCell = {}
        # A dictionary with all the game objects information.
        self.gameObjectDict = {}


        # ---------------------------------------------------
        # The following variables are used to
        # hold the data computed based on the raw data.
        # ---------------------------------------------------

        # For each valid cell index, there are several pieces of
        # information.  This dictionary contains ALL the information
        # for every cell.
        self.cellInfoDict = {}
        # For each room, there are several pieces of information
        # as well.  This dictionary contains all the information
        # for every room.
        self.roomInfoDict = {}
        # For each object that can be used, it has several properties,
        # some of which may depend on the object type.
        # This dictionary keeps track of all the information for each object and
        # assigns an ID to each object (incrementing integer).  This is used as a
        # reference for later.
        self.objectInfoDict = {}

    def CalcNodeData(self, index, gid):
        tileID = gid & 0x00FFFFFF
        flipX = (gid & MapData.FLIPPED_HORIZONTALLY_FLAG) > 0
        flipY = (gid & MapData.FLIPPED_VERTICALLY_FLAG) > 0
        flipD = (gid & MapData.FLIPPED_DIAGONALLY_FLAG) > 0
        cellX = index % self.mapWidth
        cellY = index / self.mapWidth
        x1 = cellX * self.tileWidth
        y1 = cellY * self.tileHeight
        x2 = x1 + self.tileWidth
        y2 = y1 + self.tileHeight

        return index,tileID, cellX, cellY, (x1, y1), (x2, y2), flipX, flipY, flipD

    def CalculateIndex(self,cellX,cellY):
        return cellY*self.mapWidth + cellX

    def CalculateAdjacentCells(self,index):
        cellX = index % self.mapWidth
        cellY = index / self.mapWidth
        north = self.CalculateIndex(cellX + 0, cellY - 1)
        south = self.CalculateIndex(cellX + 0, cellY + 1)
        east  = self.CalculateIndex(cellX + 1, cellY + 0)
        west  = self.CalculateIndex(cellX - 1, cellY + 0)

        return (north, east, south, west)

    def Overlaps(self, topLeft, botRight, sTopLeft, sBotRight):
        x1, y1 = topLeft
        x2, y2 = botRight
        sX1, sY1 = sTopLeft
        sX2, sY2 = sBotRight
        if x1 > sX2:
            return False
        if x2 < sX1:
            return False
        if y1 > sY2:
            return False
        if y2 < sY1:
            return False
        return True

    def ExtractRoomObjectsInformation(self):
        # No tree = No Work
        if not self.tree:
            print "No tree to extract data from!"
            return False
        # A dictionary of the tile IDs and the type of
        # OBJECT_TYPE they map to.
        roomObjectDict = {}
        # Bring in the tileset data.  We only
        # support ONE tileset currently.
        root = self.tree.getroot()
        objectGroups = root.findall("objectgroup")
        if len(objectGroups) < 1:
            print "objectgroup count = ", len(objectGroups)
            print "Unable to continue..."
            return False
        # Find the group with the name "Rooms"
        for group in objectGroups:
            if group.attrib['name'] != "Rooms":
                continue
            objects = group.findall("object")
            if objects is None:
                print "No objects in objectgroup."
                print "Unable to continue..."
                return False
            for obj in objects:
                x = int(obj.attrib['x'])
                y = int(obj.attrib['y'])
                width = int(obj.attrib['width'])
                height = int(obj.attrib['height'])
                # Get the ROOM for the object
                properties = obj.findall("properties")
                if len(properties) != 1:
                    continue
                property = properties[0].findall("property")
                if len(property) != 1:
                    continue
                if property[0].attrib['name'] == "ROOM":
                    roomName = property[0].attrib['value']
                    roomObjectDict[roomName] = { 'BOUNDS':((x,y),(x+width,y+height)) }
        self.roomObjectDict = roomObjectDict
        return True

    def DumpRoomObjectInfo(self):
        roomObjectDict = self.roomObjectDict
        keys = roomObjectDict.keys()
        keys.sort()
        print '----------------- ROOM INFO ------------------ '
        for key in keys:
            print "Room [%s] = %s." % (key, roomObjectDict[key])
        print '---------------------------------------------- '
        print

    def ExtractLayerInformation(self):
        # There are certain layers that are
        # specifically searched for.  If a necessary
        # layer is not found, this will fail.  Other
        # layers are ignored.
        layerDict = {}
        root = self.tree.getroot()
        layers = root.findall("layer")
        for layer in layers:
            name = layer.attrib['name']
            if name not in MapData.EXPECTED_LAYERS:
                print "Layer [%s] not used in processing."
                continue
            # Found one we care about.
            width = int(layer.attrib['width'])
            height = int(layer.attrib['height'])
            if width != self.mapWidth or height != self.mapHeight:
                print "Layer %s has incorrect dimensions; expected [%d x %d], found [%d x %d]."%(
                    name,self.mapWidth,self.mapHeight,width,height
                )
                print "Unable to continue..."
                return False
            tiles = layer[0].findall("tile")
            if len(tiles) != self.mapWidth*self.mapHeight:
                print "Layer %s tile count [%d] does not match expected [%d]."%(
                    name,len(tiles),self.mapWidth*self.mapHeight
                )
                print "Unable to continue..."
                return False
            tileData = {}
            for idx in xrange(len(tiles)):
                gid = int(tiles[idx].attrib["gid"])
                if gid > 0:
                    tileData[idx] = self.CalcNodeData(idx, gid)
            layerDict[name] = tileData
        for layerName in MapData.EXPECTED_LAYERS:
            if layerName not in layerDict:
                print "Unable to find layer %s in map data."%layerName
                print "Unable to continue..."
                return False
        self.layerDict = layerDict
        return True


    def DumpLayerInfo(self):
        layerDict = self.layerDict
        keys = layerDict.keys()
        keys.sort()
        print '----------------- LAYER INFO ------------------ '
        for key in keys:
            print "Layer [%s] = %s." % (key, layerDict[key])
        print '----------------------------------------------- '
        print


    def ExtractTilesetInformation(self):
        # No tree = No Work
        if not self.tree:
            print "No tree to extract data from!"
            return False
        # A dictionary of the tile IDs and the type of
        # OBJECT_TYPE they map to.
        tileDict = {}
        # Bring in the tileset data.
        root = self.tree.getroot()
        tilesets = root.findall("tileset")
        if len(tilesets) < 1:
            print "Tileset count = ", len(tilesets)
            print "Unable to continue..."
            return False
        for tileset in tilesets:
            firstGID = int(tileset.attrib['firstgid'])
            tiles = tileset.findall("tile")
            # Get the data associated with each tile.
            for element in tiles:
                # Get the local (in the tilset) ID for the tile.
                tileID = int(element.attrib['id'])
                tileGID = tileID + firstGID
                # Get the OBJECT_TYPE for the tile
                properties = element.findall("properties")
                if len(properties) != 1:
                    continue
                property = properties[0].findall("property")
                if len(property) != 1:
                    continue
                if property[0].attrib['name'] == "OBJECT_TYPE":
                    objectType = property[0].attrib['value']
                    tileDict[tileGID] = (objectType,tileID)
            self.tileDict = tileDict
        return True

    def DumpTilesetInfo(self):
        tileDict = self.tileDict
        keys = tileDict.keys()
        keys.sort()
        print '----------------- TILE INFO ------------------ '
        for key in keys:
            print "Tile Type [GID:%s] = %s."%(key,tileDict[key])
        print '---------------------------------------------- '
        print

    def ExtractMapInfo(self):
        # No tree = No Work
        if not self.tree:
            print "No tree to extract data from!"
            return False
        # The map information is in the "map" root.
        root = self.tree.getroot()
        # Get the basic data for the map
        if root.tag != "map":
            print 'Root tag = %s (not "map")' % root.tag
            print "Unable to continue..."
            return False
        self.tileWidth = int(root.attrib['tilewidth'])
        self.tileHeight = int(root.attrib['tileheight'])
        self.mapWidth = int(root.attrib['width'])
        self.mapHeight = int(root.attrib['height'])
        return True

    def DumpMapInfo(self):
        print '----------------- MAP INFO ------------------- '
        print "Map Dimensions: "
        print "The map is %d tiles wide X %d tiles high." % (self.mapWidth, self.mapHeight)
        print "Each tile is %d pixels wide X %d pixels high." % (self.tileWidth, self.tileHeight)
        print '---------------------------------------------- '
        print

    def CalculateCellsInRooms(self):
        # For all the cells that are in the "Floor" layer,
        # compare it against the objects found and figure
        # out which cells are in each room.  Any cells that
        # are on the floor but NOT in a room are part of the
        # "Hall" room.
        #
        # This is a BRUTE FORCE algorithm.
        roomCells = { "HALLWAY":[]}
        for room in self.roomObjectDict:
            roomCells[room] = []
        for tileIndex in self.layerDict['Floor']:
            index, tileID, cellX, cellY, topLeft, botRight, flipX, flipY, flipD = self.layerDict['Floor'][tileIndex]
            found = False
            for room in self.roomObjectDict:
                rTopLeft, rBotRight = self.roomObjectDict[room]['BOUNDS']
                if self.Overlaps(topLeft,botRight,rTopLeft,rBotRight):
                    roomCells[room].append((index,cellX,cellY))
                    found = True
                    break
            if not found:
                roomCells["HALLWAY"].append((index, cellX, cellY))
        # If there were any rooms that were NOT populated,
        # there is a problem.
        for room in roomCells:
            if len(roomCells[room]) == 0:
                print "No tiles found for room %s."%room
                print "Unable to continue..."
                return False
        self.roomCells = roomCells
        # Now update the tileInfoDict to contain the room for each
        # tile that was found.  Anything NOT in a room should throw
        # an error later on.
        for room in roomCells.keys():
            self.roomInfoDict[room] = { "Cells":[] }
            for index,cellX,cellY in roomCells[room]:
                self.cellInfoDict[index] = { "Cell":(cellX,cellY), "Room":room }
                self.roomInfoDict[room]["Cells"].append(index)
        return True

    def DumpRoomCellsInfo(self):
        roomCells = self.roomCells
        keys = roomCells.keys()
        keys.sort()
        print '----------------- ROOM CELL INFO ------------------ '
        for key in keys:
            for index,cellX,cellY in roomCells[key]:
                print "Room: %s Cell (%d,%d) Index %d."%(key,cellX,cellY,index)
            print
        print '--------------------------------------------------- '
        print

    def DumpCellInfo(self):
        cellInfoDict = self.cellInfoDict
        keys = cellInfoDict.keys()
        keys.sort()
        print '----------------- CELL INFO ------------------ '
        for key in keys:
            print "Cell %d - %s"%(key,cellInfoDict[key])
        print '--------------------------------------------------- '
        print

    def DumpRoomInfo(self):
        roomInfoDict = self.roomInfoDict
        keys = roomInfoDict.keys()
        keys.sort()
        print '----------------- ROOM INFO ------------------ '
        for key in keys:
            print "Room %s - %s" % (key, roomInfoDict[key])
        print '--------------------------------------------------- '
        print

    def ClusterObjectTypes(self,objectDict):
        cellIdxs = objectDict.keys()
        objects = {}
        while len(cellIdxs) > 0:
            queue = []
            c0 = cellIdxs[0]
            queue.append(c0)
            cellIdxs.remove(c0)
            objectType = objectDict[c0]
            self.subjectID += 1
            objects[self.subjectID] = [objectType]
            while len(queue) > 0:
                q0 = queue[0]
                queue.remove(q0)
                if objectDict[q0] != objectType:
                    # Not the type we are looking for.
                    continue
                # Must be a keeper
                objects[self.subjectID].append(q0)
                # Remove it from future consideration.
                if q0 in cellIdxs:
                    cellIdxs.remove(q0)
                for adj in self.CalculateAdjacentCells(q0):
                    if adj in cellIdxs and objectDict[adj] == objectType and adj not in queue:
                        queue.append(adj)
        return objects


    def CalculateGameObjects(self):
        # Determine all the objects in the game.  Assign the
        # user markers for all of them.
        tempDict = {}
        for cellIdx in self.layerDict["Objects"]:
            idx,tileID,cellX,cellY,topLeft,botRight,flipX,flipY,flipD = self.layerDict["Objects"][cellIdx]
            # Lookup the OBJECT_TYPE from the tile information.
            objectType,localID = self.tileDict[tileID]
            tempDict[cellIdx] = objectType
        # Now we have a dictionary indexed by cells with each of the object types as the
        # data.  What we want to do is "cluster" these by object type.
        objects = self.ClusterObjectTypes(tempDict)
        # Objects are clustered.  The key is the subjectID and the data are the
        # name of the object and the cells it is "in".
        # We need to invert this and turn this into a dictionary
        # with the object type as the key and content as a list of dictionaries, each
        # dictionary containing the information about ONE game object.
        goDict = {}
        for goType in MapData.EXPECTED_GAME_OBJECTS:
            goDict[goType] = []
        for subjectID in objects:
            goType = objects[subjectID][0]
            goCells = objects[subjectID][1:]
            goRoom = self.cellInfoDict[goCells[0]]["Room"]
            goDict[goType].append({"Room":goRoom,"Cells":goCells,"SubjectID":subjectID})
        self.gameObjectDict = goDict
        return True

    def DumpGameObjectInfo(self):
        gameObjectDict = self.gameObjectDict
        keys = gameObjectDict.keys()
        keys.sort()
        print '----------------- GAME OBJECT INFO ------------------ '
        for key in keys:
            print "Game Object %s ----------"%key
            for go in gameObjectDict[key]:
                print " - ",go
        print '----------------------------------------------------- '
        print

    # This function drives all the data extraction.
    def ParseTMXData(self, fileName):
        # Is the filename valid?
        if not os.path.exists(fileName):
            print "File %s does not exist!!!" % fileName
            return False
        # Wipe out existing information
        self.SetDefaults()
        # Get the XML data from the .tmx file.
        self.tree = etree.parse(fileName)

        # The first several operations extract the
        # data into internal structures.  This is
        # really "raw" data but in a different format.
        # No reall processing or validation, yet.
        if not self.ExtractMapInfo():
            return False
        self.DumpMapInfo()

        if not self.ExtractTilesetInformation():
            return False
        self.DumpTilesetInfo()

        if not self.ExtractRoomObjectsInformation():
            return False
        self.DumpRoomObjectInfo()

        if not self.ExtractLayerInformation():
            return False
        self.DumpLayerInfo()

        # Now that we have all the information, we
        # can process it into the various sets we
        # really want.

        # Calculate which cells are in each room.
        if not self.CalculateCellsInRooms():
            return False
        self.DumpRoomCellsInfo()


        self.DumpCellInfo()
        self.DumpRoomInfo()

        if not self.CalculateGameObjects():
            return False
        self.DumpGameObjectInfo()

        return True


mapData = MapData()
mapData.ParseTMXData("Spaceship 3.tmx")
