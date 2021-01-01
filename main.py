#! /usr/bin/python3
import sys, re
from PIL import Image

# return the argument if it exists (converted to the same type as the default), otherwise default
default = lambda arg, defa: type(defa)(sys.argv[arg]) if len(sys.argv) > arg and sys.argv[arg] else defa

# filename of image to evaluate, default is image.jpg
IMAGE = default(1, "image.jpg")
# filename of output, default just prints it to stdout
OUTPUT = default(2, "")
# outputs in defined way based on whether or not an output file is given
if OUTPUT == "": output = print
else:
    def output(*args, **kwargs):
        with open(OUTPUT, "w+") as ofile:
            ofile.write(*args, **kwargs)

# output columns (width)
COLS = default(3, 200)

# color hues (degrees, [0-360))
COLORS = dict()
with open('colors.txt') as f:
    # each line in the file
    for line in f.readlines():
        # means comment
        if line.startswith('#'): continue
        # name: hue saturation
        # split bt name and values
        line = line.split(':')
        # split values with whitespace characters
        line = [line[0], *line[1].strip().split('\t')]
        # strip blank things from each piece
        for i, piece in enumerate(line): line[i] = piece.strip()
        # add key to COLORS
        name, hue, sat = line
        COLORS[name] = (None if hue == '*' else int(hue), None if sat == '*' else float(sat))

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
    def graylightness(self):
        return self.sum() / 765

    # returns the hsl version of this color
    def hsl(self):
        ## setup
        # normalized version of self
        nself = self / 255
        # rgb values
        vals = nself.for_each(lambda x: x)
        x, n = max(vals), min(vals) # max value
        d = x - n # difference bt max and min

        ## hue
        hue = 0;
        if d == 0: pass # max and min same
        elif x == nself.r: hue = 60*( (nself.g - nself.b) / d % 6 ) # r is max
        elif x == nself.g: hue = 60*( (nself.b - nself.r) / d + 2 ) # g is max
        else: hue = 60*( (nself.r - nself.g) / d + 4 ) # b is max

        lightness = (x + n) / 2 ## lightness
        saturation = 0 if d == 0 else d / (1 - abs(2*lightness - 1)) ## saturation

        # add 360 to hue if it's negative
        return (hue < 0)*360 + hue, saturation, lightness

    # approximate a given color to be one of the colors listed in COLORS
    # works by comparing hue values. lowest difference wins
    def approx(self, hsl=None):
        if hsl == None: hsl = self.hsl()
        hue, sat = hsl[:2]
        # the best one so far: (score, name, diff)
        best = (None, None, None)
        for name in COLORS.keys():
            chue, csat = COLORS[name]
            a, am, b, bm = 0, 2, 0, 2
            # if hue does matter
            if chue != None: a, bm = abs(hue - chue)/360, 1
            # if saturation does matter
            if csat != None: b, am = abs(sat - csat), 1
            # sum of difference in hue and saturation is the score
            score = a*am + b*bm
            # if this is a new best score
            if best[0] == None or score < best[0]:
                best = (score, name)
        # return the name of the best color
        return best[1]

    # color the string the color that the name describes
    def color_str(self, string, colorName):
        return f'<font color="{colorName}">{string}'

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

            # get the hsl version
            hsl = avgcolor.hsl()
            # approximate the color
            apcolor = avgcolor.approx(hsl)
            # pick the right character based on the lightness
            char = CHARS[round(hsl[2]*(len(CHARS) - 1))]
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
# output the result
output(accumulator)
