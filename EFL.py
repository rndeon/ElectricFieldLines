import math
import sys
import numpy
import pygame
from functools import reduce
import operator

from collections import namedtuple

pygame.init()

display_width = 800
display_height = 800
Hudsize=100
k=1
angleresolution=60
spaceresolution=1
screen = pygame.display.set_mode((display_width,display_height))
screen.fill((255, 245, 210))
EFLsurface = pygame.Surface((display_width, display_height - Hudsize))
EFLsurface = EFLsurface.convert()
EFLsurface.fill((255, 245, 210))
EFLsurface.set_colorkey((255, 245, 210))
HUD = pygame.Surface((display_width,Hudsize))
HUD.fill((200, 245, 210))

class Position(tuple): #probably poorly named, it really functions as 2D vector convenience methods
    def __add__(self, other):
        return Position(x1 + x2 for x1, x2 in zip(self, other))
    def __sub__(self, other):
        return Position(x1 - x2 for x1, x2 in zip(self, other))
    def __rmul__(self, other):
        return Position(other * x for x in self)
    def __mul__(self, other):
        return Position(other * x for x in self)
    def __floordiv__(self, other):
        return Position(x // other for x in self)
    def __truediv__(self, other):
        return Position(x / other for x in self)
    def isBetween(self, point1,point2):
        betweens= Position(x1 <= s <= x2 or x2 <= s <= x1 for x1,s , x2 in zip(point1, self, point2))
        return all(betweens)
    def mag(self):
        return math.sqrt(self[0]*self[0] + self[1]*self[1])
    def magsquared(self):
        return self[0] * self[0] + self[1] * self[1]
    def isCloseEnoughTo(self,other,precision):
        return self.isBetween(other + Position((precision,precision)), other - Position((precision,precision)))

class PointCharge(object):

    def __init__(self, position, charge=1 ):
        self.position = position
        self.charge=charge
        self.size =  Position((20,20))
        self.surface = pygame.Surface(self.size)
        self.surface.fill(black)
        self.surface.set_colorkey(black)
        pygame.draw.circle(self.surface, red if self.charge > 0 else blue, self.size //2, 10, 0)

        smallText = pygame.font.SysFont("comicsansms", 15)
        textSurf, textRect = text_objects(str(self.charge), smallText, white)
        textRect.center = (10, 10)
        self.surface.blit(textSurf, textRect)

    def draw(self):
        screen.blit(self.surface,self.position-Position((10,10)))

    def isClickedOn(self,position):
        return position.isBetween(self.position - (self.size /2), self.position + (self.size /2))

class DielectricRegion(object):
    def __init__(self, rect, permittivity=1):
        self.rect=rect #just rectangle regions for now, might get more ambitious later
        self.set_perm(permittivity)

    def isInsideRegion(self,point):
        return self.rect.collidepoint(point[0], point[1])

    def set_perm(self,permittivity):
        if permittivity > 0:
            self.permittivity = permittivity
            self.k = 1 / self.permittivity


def degreesToRadians(deg):
    return deg/180.0 * math.pi

def isInsideSurface(surf, position):  # this function doesn't behave the way I think it should, so I don't know about surfaces enough yet
    temp=Position(surf.get_abs_offset())
    return Position(surf.get_abs_offset()) < position < Position(surf.get_abs_offset() + surf.get_size())

def text_objects(text, font, colour):
    textSurface = font.render(text, True, colour)
    return textSurface, textSurface.get_rect()

def display_at_mouse(msg):
    smallText = pygame.font.SysFont("couriernew", 15)
    # textSurf = smallText.render(str(curr_int.newCharge), True, black)
    textSurf, textRect = text_objects(msg, smallText, black)
    # textRect = textSurf.get_rect()
    textRect.bottomleft = curr_int.mousePoint
    screen.blit(textSurf, textRect)
#maybe useful later -
def message_display(text,position):
    largeText = pygame.font.Font('freesansbold.ttf',25)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = position
    screen.blit(TextSurf, TextRect)

    pygame.display.update()

#Just used to indicator the electric field at the mouse pointer
def drawArrow(surf,colour, start_pos, end_pos, width=1,arrowheadsize=8):
    pygame.draw.line(surf,colour, start_pos, end_pos, width)
    arrow = pygame.Surface((arrowheadsize, arrowheadsize))
    arrow.fill(white)
    pygame.draw.polygon(arrow, colour, [(0, 0), (arrowheadsize/2, arrowheadsize/2), (0,arrowheadsize), (0,0)], 0)
    arrow.set_colorkey(white)

    angle = math.atan2(-(end_pos[1] - start_pos[1]), end_pos[0] - start_pos[0])
    ##Note that in pygame y=0 represents the top of the screen
    ##So it is necessary to invert the y coordinate when using math
    angle = math.degrees(angle)

    def drawAng(angle, pos):
        nar = pygame.transform.rotate(arrow, angle)
        nrect = nar.get_rect(center=pos)
        screen.blit(nar, nrect)

    drawAng(angle, end_pos)

#probably not useful when you can calculate the field directly, but here anyway
def getPotentialAtPoint(pointcharges, testpoint):
    Potential = 0
    for pointCharge in pointcharges:
        rdiff = (testpoint - pointCharge.position).mag()
        Potential += k * pointCharge.charge / (rdiff if rdiff != 0 else 0.0001)
    return Potential

# these next two functions use a method of testing the potential in the region around the current point to find the gradient. pretty silly when the field can be calculated directly.
def getNextPointAlongEFL(pointcharges, testpoint):
    V = getPotentialAtPoint(pointcharges, testpoint)
    # find the gradient
    lowestV = V
    nextPoint = testpoint + (0, 1)
    # get total Electric Potential at all points nearby
    for angle in numpy.arange(0, 360, angleresolution):
        newPoint = testpoint + spaceresolution * Position((  math.cos(degreesToRadians(angle)), math.sin(degreesToRadians(angle))  ))
        Vnew = getPotentialAtPoint(pointcharges, newPoint)
        if Vnew < lowestV:
            lowestV = Vnew
            nextPoint = newPoint
    return Position(nextPoint)

def getUphillPointAlongEFL(pointcharges, testpoint):
    V = getPotentialAtPoint(pointcharges, testpoint)
    # find the gradient
    highestV = V
    nextPoint = testpoint + (0, 1)
    # get total Electric Potential at all points nearby
    for angle in range(0, 360,angleresolution):
        newPoint = testpoint + spaceresolution * Position((  math.cos(degreesToRadians(angle)), math.sin(degreesToRadians(angle))  ))
        Vnew = getPotentialAtPoint(pointcharges, newPoint)
        if Vnew > highestV:
            highestV = Vnew
            nextPoint = newPoint
    return Position(nextPoint)

#these next few functions deal in the field,
def getEFieldAtPoint(pointcharges, testpoint):
    field = Position((0,0))
    for pointCharge in pointcharges:
        rdiff = (testpoint - pointCharge.position)
        mag = math.pow((testpoint - pointCharge.position).magsquared(), 3/2)
        field += (k * pointCharge.charge * rdiff) / (mag if mag != 0 else 0.0001)
    return field
#Finds the next point along a field line
def getNextPointAlongEFLUsingField(pointcharges, testpoint):
    E = getEFieldAtPoint(pointcharges, testpoint)
    mag =E.mag()
    nextPoint = testpoint + spaceresolution * (E / (mag if mag != 0 else 0.0001) )
    return Position(nextPoint)

def getUphillPointAlongEFLUsingField(pointcharges, testpoint):
    E = getEFieldAtPoint(pointcharges, testpoint)
    mag = E.mag()
    nextPoint = testpoint - spaceresolution * (E / (mag if mag != 0 else 0.0001) )
    return Position(nextPoint)
#this function gets the whole EFL in one shot, which can be annoyingly slow in a interactive program
def traceEFL(elf):
    while elf[-1].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(elf[-1],
                                                                                                            pointCharges):
        elf.append(getNextPointAlongEFLUsingField(pointCharges, elf[-1]))
        # print("next point is: %s" % (elf[-1],) )
    ##follow ELF backwards until it hits a charge or leaves the screen
    while elf[0].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(elf[0],
                                                                                                           pointCharges):
        elf.insert(0, getUphillPointAlongEFLUsingField(pointCharges, elf[0]))
        # print("next point is: %s" % (elf[0],))
#so this function just adds one point on either end of an existing field line, so it can be called intermittently
def nextEFLPoints(efl):
    newpoints = [False, False]
    if efl[-1].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(efl[-1],
                                                                                                         pointCharges):
        efl.append(getNextPointAlongEFLUsingField(pointCharges, efl[-1]))
        if len(efl)>2 and (efl[-1].isCloseEnoughTo(efl[-2], spaceresolution / 10) or efl[-1].isCloseEnoughTo(efl[-3], spaceresolution / 10)):
            efl.append(Position((display_width + 1, display_height + 1))) # hack in a way to stop the calculations if the field is really zero at a point. this appends a position outside the screen, so no more will be added.
            #print("hacked!")
        else:
            newpoints[1] = True

    if efl[0].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(efl[0],
                                                                                                        pointCharges):
        efl.insert(0, getUphillPointAlongEFLUsingField(pointCharges, efl[0]))
        #print(" %s" % (elf[0], ))
        if len(efl)>2 and (efl[0].isCloseEnoughTo(efl[1], spaceresolution/10) or efl[0].isCloseEnoughTo(efl[2], spaceresolution/10)):
            efl.insert(0, Position((display_width + 1, display_height + 1)))
            #print("hacked!")
        else:
            newpoints[0] = True
    return newpoints

def isOnAnyPointCharges(point, pointcharges):
    for pointCharge in pointcharges:
        if point.isCloseEnoughTo(pointCharge.position, spaceresolution):
            return True

def isInAnyRegion(point,regions, action=lambda region: print("region: %s" % region.permittivity)):
    for region in regions:
        if region.isInsideRegion(point):
            action(region)
            break

def autoStartEFLs():
    global efls
    global pointCharges
    clearEFLs()
    for pointCharge in pointCharges:
        for angle in numpy.arange(0, 360, angleresolution):
            efls.append([pointCharge.position + 2 * spaceresolution * Position((math.cos(degreesToRadians(angle)), math.sin(degreesToRadians(angle))))])

class Button:
    def __init__(self, msg, x, y, w, h, maincolour, clickcolour, action=None):
        self.msg = msg
        self.position = Position((x,y))
        self.size = Position((w,h))
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.maincolour = maincolour
        self.clickcolour = clickcolour
        self.surface = pygame.Surface((w,h))

        pygame.draw.rect(self.surface, self.maincolour, (0, 0, self.w, self.h))
        pygame.draw.rect(self.surface, black, (0, 0, self.w, self.h), 1)
        smallText = pygame.font.SysFont("comicsansms", 20)
        self.textSurf, self.textRect = text_objects(self.msg, smallText, black)
        self.textRect.center = (self.w / 2, self.h / 2)
        self.surface.blit(self.textSurf, self.textRect)
        self.action=action
        self.wasclicked = False # so the button can change colour briefly
        self.clickcountdown=0

    #def mouseOver(self, mouse_pos):
        #nothing
    def click(self,mouseclick):
        self.wasclicked = mouseclick.isBetween(self.position, self.position + self.size)
        if self.wasclicked and self.action != None:
            self.action()
        return self.wasclicked

    def draw(self):
        if self.wasclicked:
            pygame.draw.rect(self.surface, self.clickcolour, (0, 0, self.w, self.h))
            self.surface.blit(self.textSurf, self.textRect)
            self.wasclicked = False
            self.clickcountdown = 10
        if self.clickcountdown == 1:
            pygame.draw.rect(self.surface, self.maincolour, (0, 0, self.w, self.h))
            self.surface.blit(self.textSurf, self.textRect)
            self.clickcountdown -= 1
        else:
            self.clickcountdown -= 1
        pygame.draw.rect(self.surface, black, (0, 0, self.w, self.h), 1)
        screen.blit(self.surface, self.position)

def clearEFLs():
    global efls
    global EFLsurface
    efls = []
    EFLsurface.fill((255, 245, 210))
    return True

def clearCharges():
    global pointCharges
    pointCharges = []
    return True

class MouseInteractor:
    def __init__(self):
        self.currentMode= ClickModes.addCharge
        self.mousePoint = Position((0, 0))
        self.prevMousePoint = Position((0, 0))
        self.mouseUp = Position((0, 0))
        self.prevMouseUp = Position((0, 0))
        self.mouseDown = Position((0, 0))
        self.prevMouseDown = Position((0, 0))

        self.newCharge = 0
        self.newDielectric = 1
    def set_charge(self,value):
        self.newCharge = value

    def set_mode(self,mode):
        self.currentMode = mode


# #testing my between function
# print("%s" % (pointCharges[0].position.isBetween((100,300),(400,300) ),))
# print("%s" % (pointCharges[0].position.isBetween((100,100),(400,400) ),))
# print("%s" % (pointCharges[0].position.isBetween((400,400),(0,0) ),))
# print("%s" % (pointCharges[0].position.isBetween((100,400),(300,200) ),))
# print("%s" % (pointCharges[0].position.isBetween((00,00),(8000,800) ),))
# print("%s" % (pointCharges[0].position.isBetween((100,500),(400,500) ),))
# print("%s" % (pointCharges[0].position.isBetween((400,100),(400,300) ),))
# print("%s" % (pointCharges[0].position.isBetween((0,100),(200,300) ),))
# print("%s" % (pointCharges[0].position.isBetween((0,100),(200,30) ),))
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((100,100)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((100.5,100.5)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((101,100.5)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((101,99)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((99.5,99.5)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((99,98.9)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((100.99,98.9)),1), )  )
# print("%s" % (Position((100,100)).isCloseEnoughTo(Position((101,101.1)),1), )  )

#globals and such
black = (0,0,0)
white = (255,255,255)
dullgrey = (100,100,100)
grey = (200,200,200)
red = (255,0,0)
green = (0,255,0)
dullgreen= (0,175,0)
blue = (0,0,255)
lightblue=(200,200,255)
darkblue=(0,0,100)
lightred=(255,200,200)
darkred=(100,0,0)
yellow=(200,100,0)
dullyellow=(100,50,0)

pointCharges = [PointCharge(Position((300,300))), PointCharge(Position((300, 400)), -2)] #default to a mild starting configuration
dielectricRegions = [DielectricRegion(screen.get_rect())] # this one is a little tricky.
# mousePoint=Position((0,0))
# prevMousePoint=Position((0,0))
# mouseClick=Position((0,0))
# prevMouseClick=Position((0,0))
class ClickModes:
    addCharge, fieldline, dielectric = range(3)


#currentMode=ClickModes.addCharge
# def set_mode(mode):
#     global currentMode
#     currentMode = mode
#
# NewCharge=0
# def set_charge(value):
#     global NewCharge
#     NewCharge = value

curr_int = MouseInteractor()
efls=[]
buttonsize=250
buttons=[Button("Find Field Line",0,display_height-100,buttonsize,50,green,dullgreen, action=lambda: curr_int.set_mode(ClickModes.fieldline) ),
         Button("Edit Point Charges",0,display_height-50,buttonsize,50,grey,dullgrey, action=lambda: curr_int.set_mode(ClickModes.addCharge)),
         Button("Autostart Lines", display_width - buttonsize, display_height - 100, buttonsize, 50, lightblue, darkblue, action=autoStartEFLs),
         Button("Edit Dielectric Regions", buttonsize, display_height - 50, buttonsize, 50, lightred, darkred, action=lambda: curr_int.set_mode(ClickModes.dielectric)),
         Button("Clear Screen", display_width - buttonsize, display_height - 50, buttonsize, 50, yellow, dullyellow,
                action=lambda: clearEFLs() and clearCharges())]


while True:
    #pin background colour to the value of its permittivity
    screen.fill(100 * Position((255, 245, 210)) / (100 + dielectricRegions[-1].permittivity) )
    # Calculate ELFs
    for elf in efls:
        drawnew = nextEFLPoints(elf)
        # Draw ELFs
        if drawnew[0]:
            pygame.draw.line(EFLsurface, black, elf[0], elf[0], 1)
        if drawnew[1]:
            pygame.draw.line(EFLsurface, black, elf[-1], elf[-1], 1)

    screen.blit(HUD, (0, display_height - Hudsize))
    screen.blit(EFLsurface, (0, 0))  # screen.fill((255, 245, 210))

    #event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.MOUSEBUTTONUP:
            curr_int.mouseUp = Position(pygame.mouse.get_pos())
            if event.button == 1:
                buttonclick=False
                for button in buttons:
                    if button.click(curr_int.mouseUp):
                        buttonclick = True
                if not buttonclick: #here's where we interact with most of the screen. the `simulation'.
                    if curr_int.currentMode == ClickModes.fieldline and curr_int.mouseUp != curr_int.prevMouseUp: # start up a field line calc
                        efls.append([curr_int.mouseUp])
                    if curr_int.currentMode == ClickModes.addCharge and curr_int.newCharge != 0: # add a new charge
                        pointCharges.append(PointCharge(curr_int.mouseUp, curr_int.newCharge))
                        clearEFLs()
                curr_int.prevMouseUp = curr_int.mouseUp
            elif event.button == 3:
                if curr_int.currentMode == ClickModes.addCharge: #remove a charge with right click
                    pointCharges = [x for x in pointCharges if not x.isClickedOn(curr_int.mouseUp)]
                    clearEFLs()
            elif event.button ==4:
                if curr_int.currentMode == ClickModes.addCharge:
                    curr_int.set_charge(curr_int.newCharge +1)
                elif curr_int.currentMode == ClickModes.dielectric:
                    isInAnyRegion(curr_int.mouseUp, dielectricRegions,action=lambda region: region.set_perm(region.permittivity +1))
            elif event.button == 5:
                if curr_int.currentMode == ClickModes.addCharge:
                    curr_int.set_charge(curr_int.newCharge - 1)
                elif curr_int.currentMode == ClickModes.dielectric:
                    isInAnyRegion(curr_int.mouseUp, dielectricRegions,
                              action=lambda region: region.set_perm(region.permittivity - 1))
        #elif event.type == pygame.MOUSEBUTTONDOWN:

            #nothing

    curr_int.mousePoint = Position(pygame.mouse.get_pos())
    if curr_int.currentMode == ClickModes.addCharge: # displays the charge value that will be placed on click, just above the mouse cursor
        display_at_mouse("q = %s" % str(curr_int.newCharge))
    elif curr_int.currentMode == ClickModes.fieldline: # continuously displays the field right at the mouse cursor
        # draw gradient indicator arrow
        nextPoint = getNextPointAlongEFLUsingField(pointCharges, curr_int.mousePoint)
        gradientarrowPoint = curr_int.mousePoint + (nextPoint - curr_int.mousePoint) * (
        20 / spaceresolution)  # Position([z * 10 for z in (nextPoint - mousePoint)])
        drawArrow(screen, green, curr_int.mousePoint, gradientarrowPoint, 3)
    elif curr_int.currentMode == ClickModes.dielectric: # displays the permittivity right at the mouse cursor
        isInAnyRegion(curr_int.mousePoint,dielectricRegions ,action=lambda region: display_at_mouse("ϵ = %s" % region.permittivity))

    # Draw charges
    for pointCharge in pointCharges:
        pointCharge.draw()
        #pygame.draw.circle(screen, red if pointCharge.charge > 0 else blue, pointCharge.position, 10, 0)

    # Draw HUD
    for button in buttons:
        button.draw()

    #message_display("%.3g" % V, mousePoint + (0, -10))
    #screen.blit(background, (0, 0))
    pygame.display.update()

    #pygame.quit(); sys.exit()
    