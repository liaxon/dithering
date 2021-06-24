Dithering
====

This is a short python program that will perform Floyd-Steinberg dithering.
It runs very slowly on large pictures (larger than 500 by 500). It is designed 
to be run from the command-line, but of course, you may modify it any way that you choose.

Dependencies
-----

``numpy`` and ``PIL``

Usage
-----

``dodither.py INPUT [OPTIONS...]``  
``INPUT``: Is a path to the input image, i.e. the one to be dithered  
``OPTIONS``:  
  ``-c COLORSCHEME``:  
    Sets the color scheme used to generate the output image. Possible options are:
    ``blackandwhite``, ``grayscale``, ``rgbwb``, ``blocky``, ``finer``, ``veryfine``.  
    More color schemes are easy to add within the code itself.  
  ``-d DITHERSTYLE``:  
    Sets the style of image processing. Options are:
    ``none``, ``closest``, ``floydsteinberg``  
    The default is ``floydsteinberg``. To do realistic-looking dithering, always use the default value.
    Choose ``closest`` to instead naively assign the best-fitting color to each pixel of the input image.  
  ``-o OUTPUT``:  
    Specifies the output file.  
  ``-v``:  
    Activates verbose mode; relates information about how much progress has been made on image.  

Example:
----

``python dodither.py cutedog.png -o output.png -c blackandwhite``