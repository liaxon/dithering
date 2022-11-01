Dithering
====

This is a short python program that will perform Floyd-Steinberg dithering.
It runs very slowly on large pictures (larger than 500 by 500). It can be run directly from
the command-line, but of course, you may modify it any way that you choose.

Usage
-----

To download dependencies, run `pip install -e .`

To run, use `python dither.py INPUT [OPTIONS...]`  
  
`INPUT`: Is a path to the input image, i.e. the one to be dithered  
`OPTIONS`:  
  * `-c COLORSCHEME`: Sets the color scheme used to generate the output image. Possible options are:
    `blackandwhite`, `grayscale`, `rgbwb`, `blocky`, `finer`, `veryfine`. More color schemes are easy to add within the code itself.  
  * `-d DITHERSTYLE`: Sets the style of image processing. Options are: `none`, `closest`, `floydsteinberg`, `notouch`. The default is `floydsteinberg`. To do realistic-looking dithering, this is the option to choose. Choose `closest` to instead naively assign the best-fitting color to each pixel of the input image. Choose `notouch` to get a neat effect, whereby no two adjacent pixels can be the same color.
  * `-o OUTPUT`: Specifies the output file, default `out.png` 
  * `-v`: Activates verbose mode; relates information about how much progress has been made on image.  

Example:
----

`python dither.py cutedog.png -o output.png -c blackandwhite`

Testing:
----

If you want to run tests on the package, it is super easy. First, make sure that you already have the primary dependencies installed
with `pip install -e .`. Also install the secondary dependencies with `pip install -e requirements-dev.txt`. All of the configuration
for mypy and unit tests is in the project configuration, in the `setup.sfg` and `myproject.toml` files.

To do type checking, run `mypy .`. This can run quite slowly.

To run unit tests, run `pytest`

This package follows the flake8 style guide. To check for consistency with this, run `flake8 .`