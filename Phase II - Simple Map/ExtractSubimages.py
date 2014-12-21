from PIL import Image
import glob, os, math

OFFSET_X = 0
OFFSET_Y = 0
GAP_X  = 4
GAP_Y  = 4
SIZE_X = 64
SIZE_Y = 64
IMAGE_FORMAT = "PNG"
FORMAT = r"TILE_%03d.png"
GLOB_FORMAT = "TILE_*.png"
FILE_NAME = r"RPG_ICONS_TOP_64x64.png"
FILE_NAME_OUT = r"OUTPUT_FILE.png"
IMAGE_OUT_DIR = r"Images"

def NextPowerOfTwo(value):
    return int(math.pow(2,math.ceil(math.log(value,2))))

def ExtractTiles(fileName,offsetX,offsetY,gapX,gapY,sizeX,sizeY):
    im = Image.open(fileName)
    result = []
    xSize,ySize = im.size
    xPixel = offsetX
    yPixel = offsetY
    while (yPixel < ySize):
        xPixel = offsetX
        while(xPixel < xSize):
            cropTuple = (xPixel,yPixel,xPixel+SIZE_X,yPixel+SIZE_Y)
            part = im.crop(cropTuple)
            result.append(part)
            xPixel = xPixel + (GAP_X + SIZE_X)
        yPixel = yPixel + (GAP_Y + SIZE_Y)
    return result

def CreateTileFiles(imageList,format,imageFormat):
    imageIdx = 0
    if not os.path.exists(IMAGE_OUT_DIR):
        os.mkdir(IMAGE_OUT_DIR)
    for image in imageList:
        imageIdx = imageIdx + 1
        image.save(os.path.join(IMAGE_OUT_DIR,format%imageIdx),imageFormat)

def CreateImageList(format):
    result = []
    fileList = glob.glob(GLOB_FORMAT)
    for fileName in fileList:
        print "Adding file:",fileName
        result.append(Image.open(fileName))
    return result

def CreateTileSet(imageList, fileName, imageFormat):
    sizeX,sizeY = imageList[0].size
    tileCount = len(imageList)
    print "TileCount = ",tileCount
    rowSize = math.sqrt(tileCount)
    imSizeX = NextPowerOfTwo(rowSize * sizeX)
    imSizeY = NextPowerOfTwo(rowSize * sizeY)
    print "Creating new image:(%d x %d)"%(imSizeX,imSizeY)
    im = Image.new("RGBA",(imSizeX,imSizeY),None)
    imIdx = 0
    xPixel = 0
    yPixel = 0
    while (yPixel < imSizeY and imIdx < len(imageList)):
        xPixel = 0
        while (xPixel < imSizeX and imIdx < len(imageList)):
            pasteTuple = (xPixel, yPixel)
            im.paste(imageList[imIdx],pasteTuple)
            xPixel = xPixel + sizeX
            imIdx = imIdx + 1
        yPixel = yPixel + sizeY
    print "Saving image file: ",fileName
    im.save(fileName,imageFormat)

tiles = ExtractTiles(FILE_NAME,OFFSET_X,OFFSET_Y,GAP_X,GAP_Y,SIZE_X,SIZE_Y)
#CreateTileFiles(tiles,FORMAT,IMAGE_FORMAT)
#CreateTileSet(tiles,"Crunched.png",IMAGE_FORMAT)
#tiles = CreateImageList(FORMAT)
CreateTileSet(tiles,FILE_NAME_OUT,IMAGE_FORMAT)
CreateTileFiles(tiles,FORMAT,IMAGE_FORMAT)