"""
Uses dithering to process a file.
"""

import os
import sys
from typing import Any, Callable
import numpy as np
import numpy.typing as npt
from PIL import Image


# error/usage messages
def on_usage_error() -> None:
    """
    Output general usage message and quit.
    """

    message = """Transform an input image with dithering
    USAGE: dither.py INPUT [OPTIONS...]
    OPTIONS:
    INPUT: Path to input image, to be dithered
    -c COLORSCHEME
        Sets the colors used in the output image. Options are:
        blackandwhite, grayscale, rgbwb, blocky, finer, veryfine
        default: rgbwb
    -d DITHERSTYLE
        Sets the style of image processing. Options are:
        none, closest, floydsteinberg, notouch, default is floydsteinberg
    -o OUTPUT
        Sets the path to the output image, default ./out.png
    -v
        Verbose mode: prints progress

    This may take a while to run for images larger than 500 by 500."""
    print(message)
    exit(1)


def on_style_error() -> None:
    """
    Handle error for incorrect DITHERSTYLE
    """

    message = """DITHERSTYLE must be one of:
    none, closest, floydsteinberg, notouch"""
    print(message)
    exit(1)


def on_colorscheme_error() -> None:
    """
    Handle error for incorrect COLORSCHEME
    """

    message = """COLORSCHEME must be one of:
      blackandwhite, grayscale, rgbwb, blocky, finer, veryfine
      default: rgbwb"""
    print(message)
    exit(1)


def on_file_error(inputpath: str) -> None:
    """
    Handle error for file that does not exist
    """

    message = f"""Error: File {inputpath} does not exist.\""""
    print(message)
    exit(1)


ColorLike = npt.NDArray[np.int32]


class ColorScheme:
    colors: npt.NDArray[np.int32]  # shape (_, 3)

    def __init__(self, *colors: tuple[int, int, int]):
        # self.colors has the wrong dimension if the colors parameter
        # is empty. numpy has no trivial function to fix this, but I'll
        # just assume that colors is non-empty.
        if len(colors) == 0:
            raise RuntimeError("Must have at least one color.")
        self.colors = np.array(colors)

    def getClosest(self, othercolor: ColorLike) -> ColorLike:
        bestdist = float("inf")
        newcolor: ColorLike
        for newcolor in self.colors:
            dist = np.sum(np.square(newcolor-othercolor))
            if dist < bestdist:
                bestdist = dist
                bestcolor = newcolor
        return bestcolor  # type: ignore

    def getClosestWithExclusion(self, othercolor: ColorLike, notcolors: list[ColorLike]) -> ColorLike:
        bestdist = float("inf")
        newcolor: ColorLike
        bestcolor = None
        for newcolor in self.colors:
            if isin(newcolor, notcolors):
                continue
            dist = np.sum(np.square(newcolor-othercolor))
            if dist < bestdist:
                bestdist = dist
                bestcolor = newcolor
        if bestcolor is None:
            raise RuntimeError("Tried to get closest with exclusion, but all available colors were used.")
        return bestcolor


class UniformColorScheme(ColorScheme):
    shades: npt.NDArray[np.int32]  # shape (_)

    def __init__(self, *shades: int):
        # self.shades has the wrong dimension if the shades parameter
        # is empty. numpy has no trivial function to fix this, but I'll
        # just assume that shades is non-empty.
        if len(shades) == 0:
            raise RuntimeError("Must have at least one shade.")
        self.shades = np.array(shades)
        shadeR: int
        shadeG: int
        shadeB: int
        colorlist = []
        for shadeR in shades:
            for shadeG in shades:
                for shadeB in shades:
                    newcolor = np.array((shadeR, shadeG, shadeB))
                    colorlist.append(newcolor)
        self.colors = np.array(colorlist)

    def getClosest(self, othercolor: ColorLike) -> ColorLike:
        bestcolor = np.zeros(3, dtype=np.int32)
        for i in range(3):
            bestdist = float("inf")
            bestshade = None
            for newshade in self.shades:
                dist = abs(newshade - othercolor[i])
                if dist < bestdist:
                    bestdist = dist
                    bestshade = newshade
                bestcolor[i] = bestshade
        return bestcolor


# List of available color schemes
defaultschemes: dict[str, ColorScheme] = {
    # simple
    "blackandwhite": ColorScheme((0, 0, 0), (255, 255, 255)),
    # three colors
    "grayscale": ColorScheme((0, 0, 0), (120, 120, 120), (255, 255, 255)),
    # just the color extremes (red, green, blue, white, black)
    "rgbwb": ColorScheme((0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)),
    # blocky-looking (3 colors per RGB channel)
    "blocky": UniformColorScheme(0, 120, 255),
    # finer than blocky (4 colors per RGB channel)
    "finer": UniformColorScheme(0, 100, 180, 255),
    # finer than fine
    "veryfine": UniformColorScheme(0, 30, 60, 90, 120, 150, 180, 210, 240, 255)
}


def isin(item: Any, list: list[Any]) -> bool:
    """
    Returns whether an item is in a list (because the "in" keyword was giving me difficulty).
    This works specifically for a list of numpy objects, including numpy lists.
    """
    for listitem in list:
        if np.array_equal(item, listitem):
            return True
    return False


def dither_do_nothing(image: ColorLike, colorscheme: ColorScheme, verbose: bool) -> ColorLike:
    """
    Does not modify the original image at all
    """
    return image


def dither_closest(image: ColorLike, colorscheme: ColorScheme, verbose: bool) -> ColorLike:
    """
    Replaces each pixel with its closes valid color
    """
    width, height, _ = image.shape
    for j in range(height):
        if verbose and j % 10 == 0:
            print("on row", j, "of", height)
        for i in range(width):
            color = image[i, j]
            image[i, j] = colorscheme.getClosest(color)
    return image


def dither_floyd_steinberg(image: ColorLike, colorscheme: ColorScheme, verbose: bool) -> ColorLike:
    """
    Applies floyd-steinberg dithering to an image
    """
    width, height, _ = image.shape
    newimage = np.empty((width, height, 3), dtype=np.int32)
    error = np.zeros((width, height, 3))
    for j in range(height):
        if verbose and j % 10 == 0:
            print("on row", j, "of", height)
        for i in range(width):
            color = image[i, j] + error[i, j]
            # notouch rule for horizontally or vertically adjacent squares
            excludedcolors = []
            if i >= 1:
                excludedcolors.append(newimage[i-1, j])
            if j >= 1:
                excludedcolors.append(newimage[i, j-1])
            newcolor = colorscheme.getClosestWithExclusion(color, excludedcolors)
            newimage[i, j] = newcolor
            extracolor = color - newcolor
            if i+1 < width:
                error[i+1, j] += extracolor*7/16
            if i-1 >= 0 and j-1 >= 0:
                error[i-1, j-1] += extracolor*3/16
            if j-1 >= 0:
                error[i, j-1] += extracolor*5/16
            if i+1 < width and j-1 >= 0:
                error[i+1, j-1] += extracolor*1/16
    return newimage


def dither_no_touch(image: ColorLike, colorscheme: ColorScheme, verbose: bool) -> ColorLike:
    """
    Applies Floyd-Steinberg dithering, but no two tiles can touch.
    """
    width, height, _ = image.shape
    newimage = np.empty((width, height, 3), dtype=np.int32)
    error = np.zeros((width, height, 3))
    for j in range(height):
        if verbose and j % 10 == 0:
            print("on row", j, "of", height)
        for i in range(width):
            color = image[i, j] + error[i, j]
            # notouch rule for horizontally or vertically adjacent squares
            excludedcolors = []
            if i >= 1:
                excludedcolors.append(newimage[i-1, j])
            if j >= 1:
                excludedcolors.append(newimage[i, j-1])
            newcolor = colorscheme.getClosestWithExclusion(color, excludedcolors)
            newimage[i, j] = newcolor
            extracolor = color - newcolor
            if i+1 < width:
                error[i+1, j] += extracolor*7/16
            if i-1 >= 0 and j-1 >= 0:
                error[i-1, j-1] += extracolor*3/16
            if j-1 >= 0:
                error[i, j-1] += extracolor*5/16
            if i+1 < width and j-1 >= 0:
                error[i+1, j-1] += extracolor*1/16
    return newimage


if __name__ == "__main__":
    # default values
    if len(sys.argv) <= 1:
        on_usage_error()
    inputpath = sys.argv[1]
    outputpath = os.path.join(".", "out.png")
    ditherstyle = "floydsteinberg"
    colorscheme = defaultschemes["rgbwb"]
    verbose = False

    print(sys.argv, "!")

    # handling command line args
    args = sys.argv[2:]
    curarg = ""
    for arg in args:
        if curarg == "o":
            outputpath = arg
            curarg = ""
        elif curarg == "d":
            ditherstyle = arg
            curarg = ""
        elif curarg == "c":
            if arg in defaultschemes:
                colorscheme = defaultschemes[arg]
            else:
                on_colorscheme_error()
            curarg = ""
        elif arg == "-o":
            curarg = "o"
        elif arg == "-d":
            curarg = "d"
        elif arg == "-c":
            curarg = "c"
        elif arg == "-v":
            verbose = True
        else:
            on_usage_error()
    if curarg != "":
        on_usage_error()

    # Get the image manipulation strategy
    image_action: Callable[[ColorLike, ColorScheme, bool], ColorLike]
    image_action = None  # type: ignore
    if ditherstyle == "none":
        image_action = dither_do_nothing
    elif ditherstyle == "closest":
        image_action = dither_closest
    elif ditherstyle == "floydsteinberg":
        image_action = dither_floyd_steinberg
    elif ditherstyle == "notouch":
        image_action = dither_no_touch
    else:
        on_style_error()

    # actual dithering begins here
    try:
        with Image.open(inputpath) as im:
            bmp = np.array(im, dtype=np.int32)  # shape (width, height, 3)
            if verbose:
                print(f"shape: {bmp.shape[0]} by {bmp.shape[1]}")
            width, height, _ = bmp.shape

            if verbose:
                print("starting image processing")
            newbmp = image_action(bmp, colorscheme, verbose)
            if verbose:
                print("finished processing image")

            output = Image.fromarray(newbmp.astype(np.uint8))
            output.save(outputpath)
            if verbose:
                print(f"Image saved to {outputpath}")
    except FileNotFoundError:
        # input file does not exists
        on_file_error(inputpath)
