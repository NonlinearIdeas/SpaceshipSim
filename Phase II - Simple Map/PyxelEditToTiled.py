__author__ = 'james'

import os

from lxml import etree
from PIL import Image

ROOT_FILE = "Spaceship 3"

INPUT_XML_FILE = "%s.xml"%ROOT_FILE
INPUT_TILESET_FILE = "%s.png" % ROOT_FILE
OUTPUT_XML_FILE = "%s.tmx" % ROOT_FILE

# Updates the gid for a tile based on the rotation
# and flipX flag passed in from the PyxelEdit element.
def UpdateGIDForRotation(gid, rot, flipX):
    # Constants used in Tiled to indicate flip/rotation
    FLIPPED_HORIZONTALLY_FLAG = 0x80000000
    FLIPPED_VERTICALLY_FLAG = 0x40000000
    FLIPPED_DIAGONALLY_FLAG = 0x20000000
    # There are 4 rot values and two flipX values (True,False),
    # leading to 8 combinations.  For each combination, we have
    # to add on the flags that are appropriate.
    if not flipX:
        if rot == "0":
            # Nothing to do
            pass
        elif rot == "1":
            gid += (FLIPPED_HORIZONTALLY_FLAG + FLIPPED_DIAGONALLY_FLAG)
        elif rot == "2":
            gid += (FLIPPED_HORIZONTALLY_FLAG + FLIPPED_VERTICALLY_FLAG)
        elif rot == "3":
            gid += (FLIPPED_VERTICALLY_FLAG + FLIPPED_DIAGONALLY_FLAG)
    else:   # FlipX
        if rot == "0":
            gid += (FLIPPED_HORIZONTALLY_FLAG)
        elif rot == "1":
            gid += (FLIPPED_HORIZONTALLY_FLAG + FLIPPED_VERTICALLY_FLAG + FLIPPED_DIAGONALLY_FLAG)
        elif rot == "2":
            gid += (FLIPPED_VERTICALLY_FLAG)
        elif rot == "3":
            gid += (FLIPPED_DIAGONALLY_FLAG)
    # Return the modified value.
    return gid

def PyxelEditToTiled(inFileName, tileSetName, outFileName):
    # IF THE OUTPUT FILE ALREADY EXISTS, DO NOT OVERWRITE IT!!
    if os.path.exists(outFileName):
        print "File %s already exists...NOT OVERWRITING!"%outFileName
        print "NOTHING DONE!!!"
        return
    # Read in the tileset information
    imgFile = Image.open(tileSetName)
    imgWidth, imgHeight = map(str, imgFile.size)

    inTree = etree.parse(inFileName)
    inRoot = inTree.getroot()
    tilesWide = inRoot.attrib["tileswide"]
    tilesHigh = inRoot.attrib["tileshigh"]
    tileWidth = inRoot.attrib["tilewidth"]
    tileHeight = inRoot.attrib["tileheight"]

    # Build the root node ("map")
    outRoot = etree.Element("map")
    outRoot.attrib["version"] = "1.0"
    outRoot.attrib["orientation"] = "orthogonal"
    outRoot.attrib["renderorder"] = "left-up"
    outRoot.attrib["width"] = tilesWide
    outRoot.attrib["height"] = tilesHigh
    outRoot.attrib["tilewidth"] = tileWidth
    outRoot.attrib["tileheight"] = tileHeight


    # Build the tileset
    tileset = etree.SubElement(outRoot, "tileset")
    tileset.attrib["firstgid"] = "1"
    tileset.attrib["name"] = os.path.splitext(tileSetName)[0]
    tileset.attrib["tilewidth"] = tileWidth
    tileset.attrib["tileheight"] = tileHeight
    # Add the image information for the tileset
    imgElem =etree.SubElement(tileset, "image")
    imgElem.attrib["source"] = tileSetName
    imgElem.attrib["width"] = imgWidth
    imgElem.attrib["height"] = imgHeight

    # Now iterate over the layers and pull out each one.
    for element in inRoot:
        layer = etree.SubElement(outRoot, element.tag)
        layer.attrib["name"] = element.attrib["name"]
        layer.attrib["width"] = tilesWide
        layer.attrib["height"] = tilesHigh
        data = etree.SubElement(layer, "data")
        # In each layer, there are width x height tiles.
        for tile_element in element:
            tile = etree.SubElement(data, "tile")
            gid = tile_element.attrib["tile"]
            if(gid == "-1"):
                tile.attrib["gid"] = "0"
            else:
                flipX = tile_element.attrib["flipX"] == "true"
                rot = tile_element.attrib["rot"]
                tile.attrib["gid"] = str(UpdateGIDForRotation(int(gid) + 1, rot, flipX))

    outTree = etree.ElementTree(outRoot)
    outTree.write(outFileName, encoding="UTF-8", xml_declaration=True, pretty_print=True)



PyxelEditToTiled(INPUT_XML_FILE, INPUT_TILESET_FILE, OUTPUT_XML_FILE)

