
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
        # The XML Tree used to hold the original file
        # data.  Set to None by default.
        self.tree = None
        # A dictionary with each piece of node information,
        # keyed by its node index.
        self.nodeDict = {}
        # A dictionary with each piece of room information
        # keyed by its room name
        self.roomDict = {}
        # A dictionary of the tileset used for the map,
        # keyed by the tileID
        self.tileDict = {}

    def CalcNodeData(self,index,gid,cellsWide,cellsHigh,cellWidth,cellHeight):
        tileID = gid & 0x00FFFFFF
        flipX = (gid & MapData.FLIPPED_HORIZONTALLY_FLAG) > 0
        flipY = (gid & MapData.FLIPPED_VERTICALLY_FLAG) > 0
        flipD = (gid & MapData.FLIPPED_DIAGONALLY_FLAG) > 0
        cellX = index % cellsWide
        cellY = index / cellsWide
        x1 = cellX * cellWidth
        y1 = cellY * cellHeight
        x2 = x1 + cellWidth
        y2 = y1 - cellHeight

        return index,tileID, cellX, cellY, (x1, y1), (x2, y2), flipX, flipY, flipD


    def Overlaps(self, topLeft, botRight, sTopLeft, sBotRight):
        x1, y1 = topLeft
        x2, y2 = botRight
        sX1, sY1 = sTopLeft
        sX2, sY2 = sBotRight
        if x1 < sX1:
            return False
        if y1 > sY1:
            return False
        if x2 > sX2:
            return False
        if y2 < sY2:
            return False
        return True

    def ExtractRoomObjectsInformation(self):
        # No tree = No Work
        if not self.tree:
            print "No tree to extract data from!"
            return False
        # A dictionary of the tile IDs and the type of
        # OBJECT_TYPE they map to.
        roomDict = {}
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
                    roomDict[roomName] = { 'BOUNDS':((x,y),(x+width,y+height)) }
        self.roomDict = roomDict
        return True

    def DumpRoomInfo(self):
        roomDict = self.roomDict
        keys = roomDict.keys()
        keys.sort()
        print '----------------- ROOM INFO ------------------ '
        for key in keys:
            print "Room [%s] = %s." % (key, roomDict[key])
        print '---------------------------------------------- '
        print

    def ExtractLayerInformation(self):
        # There are certain layers that are
        # specifically searched for.  Any layers that are found
        # that are NOT on this list will cause a problem.
        layers = {}


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
        self.DumpRoomInfo()

        # Now that we have all the information, we
        # can process it into the various sets we
        # really want.

        return True


mapData = MapData()
mapData.ParseTMXData("Spaceship 3.tmx")
