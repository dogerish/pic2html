#! /usr/bin/python3
import sys
from PIL import Image

# return the argument if it exists (converted to the same type as the default), otherwise default
default = lambda arg, defa: type(defa)(sys.argv[arg]) if len(sys.argv) > arg and sys.argv[arg] else defa

# filename of image to evaluate, default is image.jpg
IMAGE = default(1, "image.jpg")
# output columns (width)
COLS = default(2, 200)

# colors, color name: (r, g, b)
COLORS = \
{
    "white":        (255, 255, 255),
    "#BFBFBF":      (191, 191, 191),
    "gray":         (127, 127, 127),
    "#3F3F3F":      (63, 63, 63),
    "black":        (0, 0, 0),
    "red":          (255, 0, 0),
    "orange":       (255, 127, 0),
    "yellow":       (255, 255, 0),
    "#808000":      (127, 127, 0),
    "#80FF00":      (127, 255, 0),
    "lime":         (0, 255, 0),
    "green":        (0, 127, 0),
    "#003F00":      (0, 63, 0),
    "#001F00":      (0, 31, 0),
    "#00FF80":      (0, 255, 127),
    "turquoise":    (0, 255, 255),
    "blue":         (0, 0, 255),
    "magenta":      (255, 0, 255),
    "purple":       (127, 0, 127)
}
# characters for lightness values (ascending)
CHARS = " -+:!?%#&$@"

# color class
class Color:
    def __init__(self, r=0, g=0, b=0, name=None):
        self.r, self.g, self.b = r, g, b
        self.vals = ('r', 'g', 'b')
        self.name = name

    # reduce the color to accumulator
    def reduce(self, reducer, accumulator=0):
        for v in self.vals:
            accumulator = reducer(accumulator, getattr(self, v))
        return accumulator

    # executes f for each value of this color, returns a list of results
    def for_each(self, f):
        return [f(getattr(self, v)) for v in self.vals]
    # executes f on each color value, returns list of results
    def on_each(self, other, f):
        return [f(getattr(self, v), getattr(other, v)) for v in self.vals]

    # add with another color
    def __add__(self, color2):
        if type(color2) == Color:
            return Color(*self.on_each(color2, lambda a, b: a + b))
        else:
            return Color(*self.for_each(lambda x: x + color2))
    # multiply with another color
    def __mul__(self, color2):
        if type(color2) == Color:
            return Color(*self.on_each(color2, lambda a, b: a * b))
        else:
            return Color(*self.for_each(lambda x: x * color2))
    # subtract another color
    def __sub__(self, color2):
        return self + -1*color2
    # divide by another color
    def __truediv__(self, color2):
        if type(color2) == Color:
            return Color(*self.on_each(color2, lambda a, b: a / b))
        else:
            return Color(*self.for_each(lambda x: x / color2))

    # get the difference between 2 colors (like subtraction but with no negatives)
    def diff(self, color2):
        return Color(*self.on_each(color2, lambda a, b: abs(a - b)))

    # get the sum of the rgb values
    def sum(self):
        return self.reduce(lambda a, b: a + b)
    
    # get the lightness of this color as a decimal percent
    # 1 means brightest, 0 means darkest, 0.5 means middle...
    def lightness(self):
        return self.sum() / 765

    # approximate a given color to be one of the colors listed in COLORS
    # works by adding all of the differences in rgb values. lowest wins
    def approx(self):
        # the best one so far: (score, name, diff)
        best = (None, None, None)
        for color in COLORS.keys():
            color = COLORS[color]
            diff = self.diff(color)
            # get the sum of the differences - this is the score
            score = diff.sum()
            # if this is a new best score
            if best[0] == None or score < best[0]:
                best = (score, color.name, diff)
        # return the name of the best color
        return best

    # color the string the color that the name describes
    def color_str(self, string, colorName):
        return f'<font color="{colorName}">{string}'

# convert all the colors in COLORS to Color objects (with the corresponding name)
for color in COLORS.keys():
    COLORS[color] = Color(*COLORS[color], name=color)

# where the output will be accumulated to
accumulator = '<body style="background-color: #000"><pre>'
# open the image
with Image.open(IMAGE) as img:
    # the step to increment by each time
    step = img.size[0] / COLS
    # the vertical step, to account for characters not being squares
    vstep = step * 15/7.81
    # the current color
    curcolor = None
    # each row
    for row in range(int(img.size[1]/vstep)):
        row *= vstep
        # add newline character to go to next row if this isn't the first row
        accumulator += '\n'
        # each column
        for col in range(COLS):
            col *= step
            # average the colors for this location
            avgcolor = Color()
            colorc = 0 # color count
            # within this tile/area
            for y in range(int(row), int(row + vstep)):
                for x in range(int(col), int(col + step)):
                    if x >= img.size[0]: break # break if it's out of range
                    # add this pixel's color to the average
                    avgcolor += Color(*img.getpixel((x, y)))
                    colorc += 1
                if y >= img.size[1]: break # break if it's out of range
            # turn sum into average
            avgcolor /= colorc

            # approximate the color
            score, apcolor, diff = avgcolor.approx()
            # pick the right character based on the lightness
            # pick max "brigthness" if it's 0
            char = CHARS[round((1 - diff.lightness())*(len(CHARS) - 1))]
            # if it isn't already in the right color, change it
            if apcolor != curcolor:
                # add colored string to accumulator
                accumulator += "</font>" + avgcolor.color_str(char, apcolor)
                # new color
                curcolor = apcolor
            else:
                # add character
                accumulator += char
# end the elements
accumulator += "</font></pre></body>"
# print the result
print(accumulator)
