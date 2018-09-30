#CHIP-8 emulator

This is my attempt at making a CHIP-8 emulator in Python.
It's actually my first time ever making something like this, so intially I was learning from this [tutorial](http://omokute.blogspot.com/2012/06/emulation-basics-write-your-own-chip-8.html).
But as soon as I grasped the basics, I decided to move on and try to do as much as I can by myself.
During making of this emulator I used the briliant [Cowgod's CHIP-8 reference](http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#0.0) that provided me with many details.

###### Usage
Just import the `Emulator` class or just write a line and create an object while passing ROM path and pixel size to the constructor.
It will automatically do the rest.

Unfortunately it's still work in progress: I had some trouble learning and debugging, but this still barely works.
Most games (other than Tic-Tac-Toe) are unplayable because of graphical or input (?) bugs. However I can't pin-point the problem.
The best working so far are `Invaders` ROM which renders the menu and the scrolling text flawleslly and Tic-Tac-Toe which actually plays.

I went through Wikipedia and above source reference for opcodes and hardware. I was unable to find the problem so I looked at other emulators to fix the issue, but without any effects. 
