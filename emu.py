from tkinter import *
from time import sleep
from random import randint
import traceback

class Emulator:
    def __init__(self, size, rom_path):

        # hardware
        self.memory = [0] * 4096
        self.gpio = [0] * 16
        self.index = 0
        self.pc = 512
        self.opcode = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = []
        # a dictionary that keeps "pixels" currently diplayed on screen.
        # anything created on tkinter's canvas is an object and to remove it later on,
        # keeping track of them is necessary. This dictionary will have "pixel" coord tuple (x, y) as a key
        # to the object.
        self.displayed_values = {}
        # list that keeps currently pressed buttons. with each cycle tkinter checks if there's any key pressed and
        # checks if it's mapped. If it is (e.g. button 1 maps to 0x1) then it's put into this list. 
        self.input_read = []
        #loading the ROM
        self.load_rom(rom_path)
        #loading the fonts
        for byte in range(len(self.fonts)):
            self.memory[byte] = self.fonts[byte]


        # a small map that helps keep track at what point in memory certain font characters are stored.
        self.font_map = {
                0 : 0,
                1 : 5,
                2 : 10,
                3 : 15,
                4 : 20,
                5 : 25,
                6 : 30,
                7 : 35,
                8 : 40,
                9 : 45,
                0xa : 50,
                0xb : 55,
                0xc : 60,
                0xd : 65,
                0xe : 70,
                0xf : 75,
            }

        # creating a general event dispatcher for opcodes
        # when there's more than one opcode for the first nibble, it
        # redirects itself to own dispatchers
        self.dispatcher = {0x1000:self._1nnn,
                    0x2000:self._2nnn,
                    0x3000:self._3xkk,
                    0x4000:self._4xkk,
                    0x5000:self._5xy0,
                    0x6000:self._6xkk,
                    0x7000:self._7xkk,
                    0x8000:self._8_dispatcher,
                    0x9000:self._9xy0,
                    0xA000:self._Annn,
                    0xB000:self._Bnnn,
                    0xC000:self._Cxkk,
                    0xD000:self._Dxyn,
                    0xE000:self._E_dispatcher,
                    0xF000:self._F_dispatcher,
        }

        # used to map pressed buttons to numerical values used in programs
        self.keymap = {
            "1":1, "2":2, "3":3, "4":0xC,
            "q":4, "w":5, "e":6, "r":0xD,
            "a":7, "s":8, "d":9, "f":0xE,
            "z":0xA, "x":0, "c":0xb, "v":0xf
            }

        # tkinter widgets to display graphics
        self.master = Tk()
        self.size = size
        # 'size' is just an int that helps make the display bigger or smaller, 8 is a pretty good value
        self.canvas = Canvas(self.master, width=64*size, height=32*size, bg="white")
        self.canvas.pack()
        self.master.bind("<Key>", self.key)
        self.master.bind("<KeyRelease>", self.keyup)

        # entering cycle
        self.cycle()

    def key(self, event):
        self.input_read.append(self.keymap[event.char])
        print("Caught %s!" % event.char)

    def keyup(self, event):
        self.input_read.remove(self.keymap[event.char])
        print("Relased %s!" % event.char)

    def draw(self, x, y):
        # draws a "pixel" (rectangle) at given coordinates while compensating
        # for display size, returns rectangle object that will be put into self.displayed_values
        return self.canvas.create_rectangle(x*self.size, y*self.size,
                                     x*self.size+self.size, y*self.size+self.size,
                                     fill="black")
        

    def load_rom(self, rom_path):
        
        #loading a ROM to the memory
        file = open(rom_path, "rb")
        read = file.read()
        i = 0
        while i < len(read):
            self.memory[i+0x200] = read[i]
            i += 1
        file.close()

    # all of the fonts
    fonts = [0xf0, 0x90, 0x90, 0x90, 0xf0,
            0x20, 0x60, 0x20, 0x20, 0x70,
            0xf0, 0x10, 0xf0, 0x80, 0xf0,
            0xf0, 0x10, 0xf0, 0x10, 0xf0,
            0x90, 0x90, 0xf0, 0x10, 0x10,
            0xf0, 0x80, 0xf0, 0x10, 0xf0,
            0xf0, 0x80, 0xf0, 0x90, 0xf0,
            0xf0, 0x10, 0x20, 0x40, 0x40,
            0xf0, 0x90, 0xf0, 0x90, 0xf0,
            0xf0, 0x90, 0xf0, 0x10, 0xf0,
            0xf0, 0x90, 0xf0, 0x90, 0x90,
            0xe0, 0x90, 0xe0, 0x90, 0xe0,
            0xf0, 0x80, 0xf0, 0x80, 0xf0,
            0xe0, 0x90, 0x90, 0x90, 0xe0,
            0xf0, 0x80, 0xf0, 0x80, 0xf0,
            0xf0, 0x80, 0xf0, 0x80, 0x80]


    def cycle(self):
        while True:
            # 16-bit opcode
            self.opcode = (self.memory[self.pc] << 8 | self.memory[self.pc + 1])
            # setting PC to next instruction for next cycle
            self.pc += 2

            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                print ("**** SOUND ****")
                self.sound_timer -= 1

            # two very similar opcodes thtat are small enough  I wrote them here
            # not really elegant but I didn't want to make them their own dispatcher
            if self.opcode == 0x00e0:
                print("Clearing the screen.")
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
                self.master.update()
                self.displayed_values = {}
            elif self.opcode == 0x00ee:
                print("Sets the program counter to the address at the top of the stack, then subtracts 1 from the stack pointer.")
                self.pc = self.stack[-1]
                self.stack.pop()
            else:
                # getting first nibble
                processed = self.opcode & 0xf000
                try:
                    # running function matching the nibble
                    self.dispatcher[processed]()
                except Exception as e:
                    # in case of unknown operation, but currently doesn't occur at all
                    print("Unknown operation %s!" % processed)
                    traceback.print_exc()

            # updates whole tkinter window including the canvas
            self.master.update()


    def _1nnn(self):
        print("The interpreter sets the program counter to nnn.")
        self.pc = (self.opcode & 0x0fff)

    def _2nnn(self):
        self.stack.append(self.pc)
        self.pc = (self.opcode & 0x0fff)
        print("The interpreter increments the stack pointer, then puts the current PC on the top of the stack. The PC is then set to %s." % self.pc)

    def _3xkk(self):
        print("The interpreter compares register Vx to kk, and if they are equal, increments the program counter by 2.")
        x = ((self.opcode & 0x0f00) >> 8)
        kk = (self.opcode & 0x00ff)
        if self.gpio[x] == kk:
            self.pc += 2


    def _4xkk(self):
        print("The interpreter compares register Vx to kk, and if they are not equal, increments the program counter by 2.")
        x = ((self.opcode & 0x0f00) >> 8)
        kk = (self.opcode & 0x00ff)
        if self.gpio[x] != kk:
            self.pc += 2

    def _5xy0(self):
        print("The interpreter compares register Vx to register Vy, and if they are equal, increments the program counter by 2.")
        x = ((self.opcode & 0x0f00) >> 8)
        y = ((self.opcode & 0x00f0) >> 4)
        if self.gpio[x] == self.gpio[y]:
            self.pc += 2

    def _6xkk(self):
        kk = (self.opcode & 0x00ff)
        x = ((self.opcode & 0x0f00) >> 8)
        print("The interpreter puts the value {} into register Vx ({}).".format(kk, self.gpio[x]))
        self.gpio[x] = kk

    def _7xkk(self):
        print("Adds the value kk to the value of register Vx, then stores the result in Vx.")
        kk = (self.opcode & 0x00ff)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = (self.gpio[x] + kk) & 0xff

    def _8xy0(self):
        print("Stores the value of register Vy in register Vx.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = self.gpio[y]

    def _8xy1(self):
        print("Performs a bitwise OR on the values of Vx and Vy, then stores the result in Vx. A bitwise OR compares the corrseponding bits from two values, and if either bit is 1, then the same bit in the result is also 1. Otherwise, it is 0")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = self.gpio[x] | self.gpio[y]

    def _8xy2(self):
        print("Performs a bitwise AND on the values of Vx and Vy, then stores the result in Vx. A bitwise AND compares the corrseponding bits from two values, and if both bits are 1, then the same bit in the result is also 1. Otherwise, it is 0.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = self.gpio[x] & self.gpio[y]

    def _8xy3(self):
        print("Performs a bitwise exclusive OR on the values of Vx and Vy, then stores the result in Vx. An exclusive OR compares the corrseponding bits from two values, and if the bits are not both the same, then the corresponding bit in the result is set to 1. Otherwise, it is 0")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = self.gpio[x] ^ self.gpio[y]

    def _8xy4(self):
        print("The values of Vx and Vy are added together. If the result is greater than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0. Only the lowest 8 bits of the result are kept, and stored in Vx.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        result = self.gpio[x] + self.gpio[y]
        if result > 255:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[x] = result & 0x00ff

    def _8xy5(self):
        print("If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        if self.gpio[x] > self.gpio[y]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[x] = (self.gpio[x] - self.gpio[y]) & 0xff

    def _8xy6(self):
        print("If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        if (self.gpio[x] & 1) == 1:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        # should've made a more elegant bitwise shift right >>
        self.gpio[x] = int(self.gpio[x] >> 1) & 0xff

    def _8xy7(self):
        print("If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        if self.gpio[y] > self.gpio[x]:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        self.gpio[x] = (self.gpio[y] - self.gpio[x]) & 0xff

    def _8xyE(self):
        print("If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        if ((self.gpio[x] & 128) >> 7) == 1:
            self.gpio[0xf] = 1
        else:
            self.gpio[0xf] = 0
        # should've made a more elegant bitwise shift left <<
        self.gpio[x] = (self.gpio[x] << 1) & 0xff

    def _9xy0(self):
        print("Skip next instruction if Vx != Vy.")
        y = ((self.opcode & 0x00f0) >> 4)
        x = ((self.opcode & 0x0f00) >> 8)
        if (self.gpio[x] != self.gpio[y]):
            self.pc += 2

    def _Annn(self):
        self.index = self.opcode & 0x0fff
        print("The value of register I is set to %s." % self.index)

    def _Bnnn(self):
        print("The program counter is set to nnn plus the value of V0.")
        self.pc = (self.opcode & 0x0fff) + self.gpio[0]

    def _Cxkk(self):
        print("The interpreter generates a random number from 0 to 255, which is then ANDed with the value kk. The results are stored in Vx.")
        rnd = randint(0, 255)
        val = rnd & (self.opcode & 0x00ff)
        x = ((self.opcode & 0x0f00) >> 8)
        self.gpio[x] = val

    def _Dxyn(self):
        print("Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.")
        # coordinates X and Y
        x = self.gpio[((self.opcode & 0x0f00) >> 8)]
        y = self.gpio[((self.opcode & 0x00f0) >> 4)]
        # nibble
        n = self.opcode & 0x000f
        # in case no pixel is erased, VF will stay 0, else it will be 1
        self.gpio[0xf] = 0
        # sprite list containing all bytes of sprite about to being drawn
        sprite = []
        print("n: {}, I: {}, x: {}, y: {}".format(n, self.index, x, y))
        for i in range(n):
            sprite.append(self.memory[self.index + i])
        for i in sprite:
            x_offset = 0
            # it uses string representation of binary to draw, e.g. format(6, "08b") will give "00000110" string
            for bit in format(i, '08b'):
                if bit == "1":
                    # if exceeds the display width
                    if(x + x_offset) > 63:
                        if (((x + x_offset - 63), y)) not in self.displayed_values:
                            obj = self.draw((x + x_offset - 63), y)
                            # add the "pixel" object to self.displayed_values with coordinates as key
                            self.displayed_values[((x + x_offset - 63), y)] = obj
                        else:
                            self.canvas.delete(self.displayed_values[((x + x_offset - 63), y)])
                            # delete the "pixel" object in self.displayed_values with coordinates as key
                            self.displayed_values.pop(((x + x_offset - 63), y), None)
                            if self.gpio[0xf] == 0:
                                self.gpio[0xf] = 1
                    # if doesn't exceed display width
                    else:
                        if (x+x_offset, y) not in self.displayed_values:
                            obj = self.draw(x+x_offset, y)
                            # add the "pixel" object to self.displayed_values with coordinates as key
                            self.displayed_values[(x+x_offset, y)] = obj
                        else:
                            self.canvas.delete(self.displayed_values[(x+x_offset, y)])
                            # delete the "pixel" object in self.displayed_values with coordinates as key
                            self.displayed_values.pop((x+x_offset, y), None)
                            if self.gpio[0xf] == 0:
                                self.gpio[0xf] = 1
                # sets to the next bit in string
                x_offset += 1
            # when cycled through one byte, it draws next in line
            y += 1
        self.master.update()


    def test_draw(self, x, y, n, letter):
        # just for testing and debugging purposes, has no usage by actual programs
        print("Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.")
        x = x
        y = y
        nibble = n
        row = []
        for i in range(n):
            row.append(self.memory[self.font_map[letter] + i])
        for i in row:
            x_offset = 0
            for bit in format(i, '08b'):
                if bit == "1":
                    if(x + x_offset) > 63:
                        if (((x + x_offset - 63), y)) not in self.displayed_values:
                            obj = self.draw((x + x_offset - 63), y)
                            self.displayed_values[(x+x_offset-63, y)] = obj
                            self.gpio[0xf] = 1
                        else:
                            self.canvas.delete(self.displayed_values[((x + x_offset - 63), y)])
                            self.gpio[0xf] = 0
                    else:
                        if (x+x_offset, y) not in self.displayed_values:
                            obj = self.draw(x+x_offset, y)
                            self.displayed_values[(x+x_offset, y)] = obj
                            self.gpio[0xf] = 1
                        else:
                            self.canvas.delete(self.displayed_values[(x+x_offset, y)])
                            self.gpio[0xf] = 0
                x_offset += 1
            y += 1
        self.master.update()

    def _Ex9E(self):
        print ("Skip next instruction if key with the value of Vx is pressed.")
        pressed_key = (self.opcode & 0x0f00) >> 8
        print("Key: %s" % pressed_key)
        if pressed_key in self.input_read:
            self.pc += 2
        else:
            pass

    def _ExA1(self):
        print ("Skip next instruction if key with the value of Vx is not pressed.")
        pressed_key = (self.opcode & 0x0f00) >> 8
        print("Key: %s" % pressed_key)
        if pressed_key not in self.input_read:
            self.pc += 2
        else:
            pass

    def _Fx07(self):
        print ("The value of DT is placed into Vx.")
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.delay_timer

    def _Fx0A(self):
        print ("Wait for a key press, store the value of the key in Vx.")
        while len(self.input_read) == 0:
            self.master.update()
            if len(self.input_read) > 0:
                if (self.input_read[0] >= 0) and (self.input_read[0] <= 0xf):
                    break
                else:
                    self.input_read = []
        self.gpio[(self.opcode & 0x0f00) >> 8] = self.input_read[0]

    def _Fx15(self):
        print ("DT is set equal to the value of Vx.")
        self.delay_timer = self.gpio[(self.opcode & 0x0f00) >> 8]


    def _Fx18(self):
        print ("ST is set equal to the value of Vx.")
        self.sound_timer = self.gpio[(self.opcode & 0x0f00) >> 8]

    def _Fx1E(self):
        print ("The values of I and Vx are added, and the results are stored in I")
        self.index = self.index + self.gpio[(self.opcode & 0x0f00) >> 8]

    def _Fx29(self):
        print ("The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx")
        letter = (self.opcode & 0x0f00) >> 8
        self.index = self.font_map[letter]

    def _Fx33(self):
        # originally I made a crude attempt, this solution I found online in another emulator on GitHub, but works just like mine
        print ("Store BCD representation of Vx in memory locations I, I+1, I+2")
        self.memory[self.index] = int(self.gpio[(self.opcode & 0x0f00) >> 8] / 100)
        self.memory[self.index+1] = int((self.gpio[(self.opcode & 0x0f00) >> 8] % 100) / 10)
        self.memory[self.index+2] = int(self.gpio[(self.opcode & 0x0f00) >> 8] % 10)
        print()

    def _Fx55(self):
        print ("The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.")
        last_register = (self.opcode & 0x0f00) >> 8
        for register in range(last_register+1):
            self.memory[self.index + register] = self.gpio[register]
        

    def _Fx65(self):
        print("Read registers V0 through Vx from memory starting at location I")
        last_register = (self.opcode & 0x0f00) >> 8
        for register in range(last_register+1):
            self.gpio[register] = self.memory[self.index + register]

    # the additional dispatchers mentioned earlier
    def _8_dispatcher(self):
        op = self.opcode & 0x000f
        if op == 0:
            self._8xy0()
        if op == 1:
            self._8xy1()
        if op == 2:
            self._8xy2()
        if op == 3:
            self._8xy3()
        if op == 4:
            self._8xy4()
        if op == 5:
            self._8xy5()
        if op == 6:
            self._8xy6()
        if op == 7:
            self._8xy7()
        if op == 0xE:
            self._8xyE()

    def _E_dispatcher(self):
        op = self.opcode & 0x000f
        if op == 0xE:
            self._Ex9E()
        if op == 1:
            self._ExA1()

    def _F_dispatcher(self):
        op = self.opcode & 0x000f
        if op == 7:
            self._Fx07()
        if op == 0xA:
            self._Fx0A()
        if op == 5:
            extracted = (self.opcode & 0x00f0) >> 4
            if extracted == 1:
                self._Fx15()
            if extracted == 5:
                self._Fx55()
            if extracted == 6:
                self._Fx65()
        if op == 8:
            self._Fx18()
        if op == 0xE:
            self._Fx1E()
        if op == 9:
            self._Fx29()
        if op == 3:
            self._Fx33()




emulator = Emulator(size=8, rom_path="INVADERS")
