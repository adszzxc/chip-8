# CHIP-8 emulator

This is my attempt at making a CHIP-8 emulator in Python.
It's actually my first time ever making something like this, so intially I was learning from this [tutorial](http://omokute.blogspot.com/2012/06/emulation-basics-write-your-own-chip-8.html).
But as soon as I grasped the basics, I decided to move on and try to do as much as I can by myself.
During making of this emulator I used the briliant [Cowgod's CHIP-8 reference](http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#0.0) that provided me with many details.

## Usage
Just import the `Emulator` class or just write a line and create an object while passing ROM path and pixel size to the constructor.
It will automatically do the rest.

Unfortunately it's still work in progress: there are some notable issues (e.g. in PONG) where input read fails for some reason but big part of games play nicely. I have not recorded any cases of visual glitches anymore.
