from PIL import Image
import sys
import numpy as np

# error/usage messages
def usage_error():
  print("USAGE: dodither.py INPUT [OPTIONS...]")
  print("INPUT: Path to input image, to be dithered")
  print("OPTIONS:")
  print("  -c COLORSCHEME")
  print("    Sets the colors used in the output image. Options are:")
  print("    blackandwhite, grayscale, rgbwb, blocky, finer, veryfine")
  print("    default: rgbwb")
  print("  -d DITHERSTYLE")
  print("    Sets the style of image processing. Options are:")
  print("    none, closest, floydsteinberg")
  print("  -o OUTPUT")
  print("    Sets the path to the output image, default ./out.png")
  print("  -v")
  print("    Verbose mode: prints progress")
  print("")
  print("This may take a while to run for images larger than 500 by 500.")
  exit(1)

def style_error():
  print("DITHERSTYLE must be one of:")
  print("  none, closest, floydsteinberg")
  exit(1)

def colorscheme_error():
  print("COLORSCHEME must be one of:")
  print("  blackandwhite, grayscale, rgbwb, blocky, finer, veryfine")
  print("  default: rgbwb")
  exit(1)

def file_error():
  print("Error: File", inputpath, "does not exist.")
  exit(1)

# default values
if len(sys.argv) <= 1:
  usage_error()
inputpath = sys.argv[1]
outputpath = "./out.png"
ditherstyle = "floydsteinberg"
defaultschemes = {
  # If doindendent == True, treat the RGB values as independent, matching each independently.
  # In this case, color scheme uses a list of numbers from 0 - 255 called "shades" that represent
  # the shade of each color
  # If doindependent == False, match against actual RGB colors. In this case, the color scheme is a
  # list of RGB colors
  "blackandwhite":{ # simple
    "doindependent": False,
    "colors": np.array([(0,0,0), (255,255,255)])
    },
  "grayscale":{ # three colors
    "doindependent": False,
    "colors": np.array([(0,0,0), (120,120,120), (255,255,255)]),
  },
  "rgbwb": { # just the color extremes (red, green, blue, white, black)
    "doindependent": False,
    "colors": np.array([(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,255,255)])
  },
  "blocky":{ # blocky-looking (3 colors per RGB channel)
    "doindependent": True,
    "shades": [0, 120, 255],
  },
  "finer": { # finer than blocky (4 colors per RGB channel)
    "doindependent": True,
    "shades": [0, 100, 180, 255]
  },
  "veryfine": { # finer than finer (10 colors per RGB channel)
    "doindependent": True,
    "shades": [0, 30, 60, 90, 120, 150, 180, 210, 240, 255]
  }
}
colorscheme = defaultschemes["rgbwb"]
printprogress = False

#handling args
args = sys.argv[2:]
curarg = ""
for arg in args :
  if curarg=="o":
    outputpath = arg
    curarg = ""
  elif curarg=="d":
    ditherstyle = arg
    curarg = ""
  elif curarg=="c":
    if arg in defaultschemes:
      colorscheme = defaultschemes[arg]
    else:
      colorscheme_error()
    curarg = ""
  elif arg=="-o":
    curarg = "o"
  elif arg=="-d":
    curarg = "d"
  elif arg=="-c":
    curarg="c"
  elif arg=="-v":
    printprogress = True
  else:
    usage_error()
if curarg != "":
  usage_error()

# handy functions
# returns the closest point in a given color scheme
# this function is the bottleneck of the whole program
def getclosest(color, colorscheme):
  if colorscheme["doindependent"]:
    bestcolor = np.array([0, 0, 0], dtype=np.uint8)
    for i in range(3):
      bestdist = float('inf')
      bestshade = None
      for newshade in colorscheme["shades"]:
        dist = abs(newshade- color[i])
        if(dist < bestdist):
          bestdist = dist
          bestshade = newshade
      bestcolor[i] = bestshade
    return bestcolor
  else:
    bestdist = float('inf')
    bestcolor = None
    for newcolor in colorscheme["colors"]:
      dist = np.sum(np.abs(newcolor-color))
      if(dist < bestdist):
        bestdist = dist
        bestcolor = newcolor
    return bestcolor

# actual dithering operations
try:
  with Image.open(inputpath) as im:
    bmp = np.array(im) # from PIL Image to Numpy Array, signature (width, height, 3) 
    if printprogress:
      print("shape:", bmp.shape[0], "by", bmp.shape[1])
    (width, height, _) = bmp.shape

    # just copy input image
    if ditherstyle=="none":
      Image.fromArray(bmp).save(outputpath)

    # (naively) match pixels independently
    elif ditherstyle=="closest":
      if printprogress:
        print("starting loop")
      for j in range(height):
        if printprogress:
          if j%10==0:
            print("on row", j)
        for i in range(width):
          color = bmp[i,j]
          newcolor = getclosest(color, colorscheme)
          bmp[i,j,:] = newcolor
      if printprogress:
        print("finished loop")
      Image.fromarray(bmp).save(outputpath)

    # Floyd-Steinberg dithering
    elif ditherstyle=="floydsteinberg":
      newbmp = np.empty((width, height, 3), dtype=np.uint8)
      error = np.zeros((width, height, 3))
      if printprogress:
        print("starting loop")
      for j in range(height):
        if printprogress:
          if j%10==0:
            print("on row", j)
        for i in range(width):
          color = bmp[i,j] + error[i,j]
          newcolor = getclosest(color, colorscheme)
          newbmp[i,j,:] = newcolor
          extracolor = color - newcolor
          if i+1 < width:
            error[i+1, j] += extracolor*7/16
          if i-1 >= 0 and j-1 >= 0:
            error[i-1, j-1] += extracolor*3/16
          if j-1 >= 0:
            error[i, j-1] += extracolor*5/16
          if i+1 < width and j-1 >= 0:
            error[i+1, j-1] += extracolor*1/16
      if printprogress:
        print("finished loop")
      Image.fromarray(newbmp).save(outputpath)

    # something's fishy...
    else:
      style_error()
except FileNotFoundError:
  file_error()