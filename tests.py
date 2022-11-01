"""
Test package for dither.py
These tests run automatically with when pytest is run.
"""

import numpy as np
import numpy.typing as npt
import pytest
from dithering.dither import ColorScheme, UniformColorScheme, dither_closest, dither_do_nothing, dither_floyd_steinberg, dither_no_touch, isin


def test_isin_simple():
    testarr = [1, 2, 3, 4]
    assert isin(1, testarr)
    assert not isin(5, testarr)


def test_isin_arrays():
    testarr = [np.array([1, 2]), np.array([2, 3])]
    assert isin(np.array([1, 2]), testarr)
    assert not isin(np.array([1, 3]), testarr)


# testing color schemes
def test_get_closest_1():
    cs = ColorScheme((0, 0, 0), (255, 255, 255), (255, 0, 0))
    black = np.array((0, 0, 0))
    red = np.array((255, 0, 0))
    white = np.array((255, 255, 255))
    assert np.array_equal(cs.getClosest(black), black)
    assert np.array_equal(cs.getClosestWithExclusion(black, []), black)
    assert np.array_equal(cs.getClosestWithExclusion(black, [black]), red)
    assert np.array_equal(cs.getClosest(white), white)
    assert np.array_equal(cs.getClosestWithExclusion(white, []), white)
    assert np.array_equal(cs.getClosestWithExclusion(white, [black]), white)


def test_get_closest_2():
    cs = UniformColorScheme(0, 100, 255)
    black = np.array((0, 0, 0))
    white = np.array((255, 255, 255))
    pink = np.array((100, 0, 0))
    lime = np.array((0, 100, 0))
    sky = np.array((0, 0, 100))
    assert np.array_equal(cs.getClosest(black), black)
    assert np.array_equal(cs.getClosestWithExclusion(black, []), black)
    assert isin(cs.getClosestWithExclusion(black, [black]), [pink, lime, sky])
    assert np.array_equal(cs.getClosest(white), white)
    assert np.array_equal(cs.getClosestWithExclusion(white, []), white)
    assert np.array_equal(cs.getClosestWithExclusion(white, [pink]), white)


@pytest.fixture()
def colorscheme():
    return ColorScheme((0, 0, 0), (100, 100, 100), (255, 255, 255))


# dithering functions which rely on a colorscheme (donothing requires different tests)
IMAGE_ACTIONS = [
    dither_closest,
    dither_floyd_steinberg,
    dither_no_touch
]


@pytest.fixture(params=IMAGE_ACTIONS)
def image_action(request):
    return request.param


def test_do_nothing_trivial(colorscheme):
    sample_picture = np.zeros((0, 0, 3), np.int32)
    result = dither_do_nothing(np.copy(sample_picture), colorscheme, False)
    assert np.array_equal(result, sample_picture)


def test_do_nothing(colorscheme):
    sample_picture = np.array([
        [(0, 0, 0), (100, 100, 100)],
        [(0, 0, 0), (100, 200, 100)]
    ])
    result = dither_do_nothing(np.copy(sample_picture), colorscheme, False)
    assert np.array_equal(result, sample_picture)


def test_dither_trivial(image_action, colorscheme):
    sample_picture = np.zeros(shape=(0, 0, 3), dtype=np.int32)
    result = image_action(sample_picture, colorscheme, False)
    assert np.array_equal(result, sample_picture)


def test_dither_simple(image_action, colorscheme):
    sample_picture = np.array(
        [[[100, 100, 0]]]
    )
    expected_picture = np.array(
        [[[100, 100, 100]]]
    )
    result = image_action(sample_picture, colorscheme, False)
    assert np.array_equal(result, expected_picture)


def test_dither_succeeds(image_action, colorscheme):
    """
    Only tests for that a call to dithering does not give an error, and that it uses the color scheme
    """
    sample_picture = np.array([
        [[100, 100, 100], [100, 200, 0], [0, 20, 0]],
        [[100, 200, 10], [10, 5, 30], [20, 20, 20]]
    ])
    result: npt.NDArray[np.int32] = image_action(sample_picture, colorscheme, False)
    assert result.shape == sample_picture.shape
    width, height, _ = sample_picture.shape
    for i in range(width):
        for j in range(height):
            assert isin(result[i, j], colorscheme.colors)
