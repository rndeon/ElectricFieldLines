import math
import sys
import numpy
import pygame

pygame.init()
pygame.display.set_caption("Electric Field Lines")
#globals and such
display_width = 800
display_height = 800
Hudsize=100
k=1
angleresolution=60
spaceresolution=1
screen = pygame.display.set_mode((display_width,display_height))
screen.fill((255,255, 255))
EFLsurface = pygame.Surface((display_width, display_height - Hudsize))
EFLsurface.fill((255, 245, 210))
EFLsurface.set_colorkey((255, 245, 210))
EFLsurface = EFLsurface.convert()
HUD = pygame.Surface((display_width,Hudsize))
HUD.fill((200, 245, 210))

black = (0,0,0)
white = (255,255,255)
dullgrey = (100,100,100)
grey = (200,200,200)
lightgrey= (225,225,225)
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

class Position(object): #probably poorly named, it really functions as 2D vector convenience methods
    def __init__(self, new_tuple):
        self.tuple = tuple(new_tuple)
    def __getitem__(self, index):
        return self.tuple[index]
    def __add__(self, other):
        return Position(x1 + x2 for x1, x2 in zip(self, other))
    def __sub__(self, other):
        return Position(x1 - x2 for x1, x2 in zip(self.tuple, other.get_tuple()))
    def __rmul__(self, other):
        return Position(other * x for x in self.tuple)
    def __mul__(self, other):
        return Position(other * x for x in self.tuple)
    def __floordiv__(self, other):
        return Position(x // other for x in self.tuple)
    def __truediv__(self, other):
        return Position(x / other for x in self.tuple)
    def get_tuple(self):
        return self.tuple
    def isBetween(self, point1,point2):
        betweens= Position(x1 <= s <= x2 or x2 <= s <= x1 for x1,s , x2 in zip(point1, self.tuple, point2))
        return all(betweens)
    def mag(self):
        return math.sqrt(self[0]*self[0] + self[1]*self[1])
    def magsquared(self):
        return self[0] * self[0] + self[1] * self[1]
    def isCloseEnoughTo(self,other,precision):
        return self.isBetween(other + Position((precision,precision)), other - Position((precision,precision)))
    def move(self, amount):
        self.tuple = tuple(x1 + x2 for x1, x2 in zip(self, amount))

class PointCharge(object):
    def __init__(self, position, charge=1 ):
        self.position = position
        self.charge=charge
        self.size =  Position((20,20))
        self.surface = pygame.Surface(self.size.get_tuple())
        self.surface.fill(black)
        self.surface.set_colorkey(black)
        pygame.draw.circle(self.surface, red if self.charge > 0 else blue, (self.size //2).get_tuple(), 10, 0)

        smallText = pygame.font.SysFont("comicsansms", 15)
        textSurf, textRect = text_objects(str(self.charge), smallText, white)
        textRect.center = (10, 10)
        self.surface.blit(textSurf, textRect)

    def draw(self):
        screen.blit(self.surface,(self.position-Position((10,10))).get_tuple() )

    def isClickedOn(self,position):
        return position.isBetween(self.position - (self.size /2), self.position + (self.size /2))

class DielectricRegion(object):
    def __init__(self, slope = 0, intercept=0, permittivity=1, x_intercept=0): # if the line isn't vertical, provide its slope and intercept, if it is vertical, set slope==intercept==0 and use the x_intercept value
        self.slope = slope
        self.intercept=intercept
        self.x_intercept =x_intercept
        self.set_perm(permittivity)
        #draw the region. divided by a line
        if slope==0 :
            if x_intercept==0:            
                if intercept==0: # then region is the whole screen, polygon to draw is just a square
                    polygonpoints=[(0,0), (0,EFLsurface.get_size()[1]), (EFLsurface.get_size()[0],EFLsurface.get_size()[1]), (EFLsurface.get_size()[0],0), (0,0)]
                else:
                    polygonpoints=[(0,0), (0,intercept), (EFLsurface.get_size()[0],intercept), (EFLsurface.get_size()[0],0), (0,0)] # horizontal division
            else:
                polygonpoints=[(0,0), (0,EFLsurface.get_size()[1]), (x_intercept,EFLsurface.get_size()[1]), (x_intercept,0), (0,0)] # vertical division       
        else: # need to get messy
            polygonpoints=[(0,0)]
            if intercept > EFLsurface.get_size()[1]: # need to go to the corner, then partway along the bottom screen limit
                polygonpoints.append( (0,EFLsurface.get_size()[1]) )
                polygonpoints.append( ( (EFLsurface.get_size()[1]-intercept) / slope , EFLsurface.get_size()[1]) )
            else:
                polygonpoints.append((0, intercept))
            #find the point where the line hits the top of the screen
            self.x_intercept = -intercept/slope
            if self.x_intercept > EFLsurface.get_size()[0]: # need to hit the right side of the screen, then go up to hit the corner
                polygonpoints.append( (EFLsurface.get_size()[0], slope * EFLsurface.get_size()[0] + intercept) )
                polygonpoints.append( ( EFLsurface.get_size()[0],0) )
            else:
                polygonpoints.append( ( self.x_intercept,0) )
            polygonpoints.append((0,0)) #back to start
        self.polygon = polygonpoints
        #draw this shape
        pygame.draw.polygon(screen, self.region_colour(),self.polygon,0 )


    def isInsideRegion(self,point):
        if self.slope==0 and self.intercept==0: # then region is the whole screen
            if self.x_intercept ==0:
                return isInsideSurface(EFLsurface,point)
            else:
                return point[0] <= self.x_intercept 
        else:
            # since region is defined as the area above a line (and in these coordinates, 'above' means less than),
            # we calculate what the line's y value is at the desired point's x value, and see if the point's y is less than the line's y
            return (point[1] <= self.slope * point[0] + self.intercept) 

    def set_perm(self,permittivity):
        self.permittivity = permittivity
        if not permittivity == 0: # in this 0 will indicate a conductor
            self.k = 1 / self.permittivity
        #else:
        #    self.permittivity = 1
        #    self.k = 1

    def region_colour(self): # pin region colour to the value of its permittivity, darker = higher epsilon
        if self.permittivity == 0:
            return lightgrey
        elif self.permittivity > 0:
            return (100 * Position((255, 245, 210)) / (100 + self.permittivity)).get_tuple()
        else:
            return (100 * Position((210, 245, 255)) / (100 - self.permittivity)).get_tuple()

    def permittivity_text(self):
        if self.permittivity == 0:
            return "conductor"
        else:
            return "ε = %s" % self.permittivity


    def draw(self):
        pygame.draw.polygon(screen, self.region_colour(),self.polygon,0)
        if not( self.slope==0 and self.intercept ==0 and self.x_intercept==0): #then the region doesn't fill the whole screen, so we should draw something at the interface
            firstpoint = (0,0)
            secondpoint = (0,0)
            if self.slope==0:
                if self.x_intercept==0:
                    firstpoint = (0,self.intercept)
                    secondpoint=(display_width, self.intercept)
                else:
                    firstpoint = (self.x_intercept,0)
                    secondpoint =(self.x_intercept, EFLsurface.get_height())
            else:
                if self.intercept > EFLsurface.get_size()[1]:
                    firstpoint=( (EFLsurface.get_size()[1]-self.intercept) / self.slope , EFLsurface.get_size()[1])
                else:
                    firstpoint= (0, self.intercept)
                if self.x_intercept > EFLsurface.get_size()[0]:
                    secondpoint = (EFLsurface.get_size()[0], self.slope * EFLsurface.get_size()[0] + self.intercept)
                else:
                    secondpoint = (self.x_intercept, 0)
            pygame.draw.line(screen, white, firstpoint, secondpoint, 2)

    def imagePosition(self, point):
        if self.slope==0 :
            if self.x_intercept==0:
                return Position(( point[0], point[1] + 2*(self.intercept - point[1]) ))
            else:
                return Position((point[0] + 2 * (self.x_intercept - point[0]), point[1] ))
        else: # need to get messy
            # from http://stackoverflow.com/questions/3306838/algorithm-for-reflecting-a-point-across-a-line
            #d= (x + (y - c) * a) / (1 + a ^ 2) x distance from point to the line intersection
            d=(point[0] + (point[1] - self.intercept)*self.slope)/ (1 + self.slope * self.slope)
            #x' = 2*d - x
            #y' = 2*d*a - y + 2c
            return Position((2*d - point[0],2*d*self.slope - point[1] + 2* self.intercept ))
    def imageCharge(self,other_region, point_charge):
        # the value of the image charge (located in other_region), felt from this region
        if other_region.permittivity==0: # indicates conductor here
            return - point_charge.charge
        elif other_region.permittivity== - self.permittivity: # avoid div/0
            return 0 # but this isn't really accurate, need to fix
        else:
            return -(other_region.permittivity - self.permittivity )/(self.permittivity + other_region.permittivity) * point_charge.charge
    def screenedCharge(self,other_region, point_charge):
        # the value of the point charge (located in other_region) felt from this region
        if other_region.permittivity== - self.permittivity: # avoid div/0
            return 0 # but this isn't really accurate, need to fix
        else:
            return 2 * self.permittivity  * point_charge.charge / ( self.permittivity + other_region.permittivity)


def degreesToRadians(deg):
    return deg/180.0 * math.pi

def isInsideSurface(surf, position):
    return position.isBetween(Position(surf.get_abs_offset()), Position(surf.get_abs_offset()) + Position(surf.get_size()) )

def text_objects(text, font, colour):
    textSurface = font.render(text, True, colour)
    return textSurface, textSurface.get_rect()

def display_at_mouse(msg):
    smallText = pygame.font.SysFont("couriernew", 15)
    # textSurf = smallText.render(str(curr_int.newCharge), True, black)
    textSurf, textRect = text_objects(msg, smallText, black)
    # textRect = textSurf.get_rect()
    textRect.bottomleft = curr_int.mousePoint.get_tuple()
    screen.blit(textSurf, textRect)
#maybe useful later -
def message_display(text,position):
    largeText = pygame.font.Font('freesansbold.ttf',25)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = position
    screen.blit(TextSurf, TextRect)

    pygame.display.update()

#Just used to indicate the electric field at the mouse pointer. Some of this code comes from a stackoverflow answer that I have lost now
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
def getEFieldAtPoint(pointcharges, dielectricregions, testpoint):
    field = Position((0,0))
    if len(dielectricregions) == 1:
        for pointCharge in pointcharges:
            rdiff = (testpoint - pointCharge.position)
            mag = math.pow((testpoint - pointCharge.position).magsquared(), 3/2)
            field += (dielectricregions[0].k * pointCharge.charge * rdiff) / (mag if mag != 0 else 0.0001)
        return field
    else: #only really accounts for  len(dielectricregions) == 2 so far
        for pointCharge in pointcharges:
            rdiff = (testpoint - pointCharge.position)
            mag = math.pow((testpoint - pointCharge.position).magsquared(), 3/2)
            testpoint_i=isInWhichRegion(testpoint, dielectricregions)
            pointCharge_i=isInWhichRegion(pointCharge.position,dielectricregions)
            # the rest assumes only two regions, and that the second region ( dielectricregions[1]) is the one with the interface definition)
            if testpoint_i == pointCharge_i:
                if not dielectricregions[pointCharge_i].permittivity == 0:
                    other_region_i = 1 - testpoint_i # suuuuuuper hacky
                    image=PointCharge(dielectricregions[1].imagePosition(pointCharge.position), dielectricregions[testpoint_i].imageCharge(dielectricregions[other_region_i],pointCharge) )
                    image_rdiff = (testpoint - image.position)
                    image_mag = math.pow((testpoint - image.position).magsquared(), 3 / 2)
                    field += dielectricregions[testpoint_i].k * (pointCharge.charge * rdiff) / (mag if mag != 0 else 0.0001)
                    field += dielectricregions[testpoint_i].k * (image.charge * image_rdiff) / (image_mag if image_mag != 0 else 0.0001)
            else:
                if not (dielectricregions[testpoint_i].permittivity == 0 or dielectricregions[pointCharge_i].permittivity == 0 ):
                    field += dielectricregions[testpoint_i].k * (dielectricregions[testpoint_i].screenedCharge(dielectricregions[pointCharge_i], pointCharge) * rdiff) / (mag if mag != 0 else 0.0001)
        return field

        
#Finds the next point along a field line
def getNextPointAlongEFLUsingField(pointcharges,dielectricregions, testpoint):
    E = getEFieldAtPoint(pointcharges,dielectricregions, testpoint)
    mag =E.mag()
    nextPoint = testpoint + spaceresolution * (E / (mag if mag != 0 else 0.0001) )
    return Position(nextPoint)

def getUphillPointAlongEFLUsingField(pointcharges,dielectricregions, testpoint):
    E = getEFieldAtPoint(pointcharges,dielectricregions, testpoint)
    mag = E.mag()
    nextPoint = testpoint - spaceresolution * (E / (mag if mag != 0 else 0.0001) )
    return Position(nextPoint)

#this function gets the whole EFL in one shot, which can be annoyingly slow in a interactive program
def traceEFL(elf):
    global dielectricRegions
    while elf[-1].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(elf[-1],
                                                                                                            pointCharges):
        elf.append(getNextPointAlongEFLUsingField(pointCharges,dielectricRegions, elf[-1]))
        # print("next point is: %s" % (elf[-1],) )
    ##follow ELF backwards until it hits a charge or leaves the screen
    while elf[0].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(elf[0],
                                                                                                           pointCharges):
        elf.insert(0, getUphillPointAlongEFLUsingField(pointCharges,dielectricRegions, elf[0]))
        # print("next point is: %s" % (elf[0],))

#so this function just adds one point on either end of an existing field line, so it can be called intermittently
def nextEFLPoints(efl):
    global dielectricRegions
    newpoints = [False, False]
    if efl[-1].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(efl[-1],
                                                                                                         pointCharges):
        efl.append(getNextPointAlongEFLUsingField(pointCharges,dielectricRegions, efl[-1]))
        if len(efl)>2 and ( efl[-1].isCloseEnoughTo(efl[-2], spaceresolution / 10) or efl[-1].isCloseEnoughTo(efl[-3], spaceresolution / 10) ):
            efl.append(Position((display_width + 1, display_height + 1))) # hack in a way to stop the calculations if the field is really zero at a point. this appends a position outside the screen, so no more will be added.
            #print("hacked!")
        else:
            newpoints[1] = True

    if efl[0].isBetween(EFLsurface.get_abs_offset(), EFLsurface.get_size()) and not isOnAnyPointCharges(efl[0],
                                                                                                        pointCharges):
        efl.insert(0, getUphillPointAlongEFLUsingField(pointCharges,dielectricRegions, efl[0]))
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
    for region in reversed(regions):
        if region.isInsideRegion(point):
            action(region)
            break
def isInWhichRegion(point,regions):
    for index,region in enumerate(reversed(regions)):
        if region.isInsideRegion(point):
            return len(regions)-1 - index # because index now indexes the reversed list!

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
        screen.blit(self.surface, self.position.get_tuple())

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
        self.mousedragging=False
        self.dragPosition= Position((0,0))
        self.newCharge = 0
        self.newDielectric = 1
    def set_charge(self,value):
        self.newCharge = value

    def set_mode(self,mode):
        self.currentMode = mode

class ClickModes:
    addCharge, fieldline, dielectric = range(3)

#More globals
curr_int = MouseInteractor()
efls=[]
buttonsize=250
buttons=[Button("Find Field Line",0,display_height-100,buttonsize,50,green,dullgreen, action=lambda: curr_int.set_mode(ClickModes.fieldline) ),
         Button("Edit Point Charges",0,display_height-50,buttonsize,50,grey,dullgrey, action=lambda: curr_int.set_mode(ClickModes.addCharge)),
         Button("Autostart Lines", display_width - buttonsize, display_height - 100, buttonsize, 50, lightblue, darkblue, action=autoStartEFLs),
         Button("Edit Dielectric Regions", buttonsize, display_height - 50, buttonsize, 50, lightred, darkred, action=lambda: curr_int.set_mode(ClickModes.dielectric)),
         Button("Clear Screen", display_width - buttonsize, display_height - 50, buttonsize, 50, yellow, dullyellow, action=lambda: clearEFLs() and clearCharges())
         ]

pointCharges = [PointCharge(Position((300,300))), PointCharge(Position((300, 400)), -2)] #default to a mild starting configuration
dielectricRegions = [DielectricRegion(0,0,1) , # this is the full screen, don't remove this one.
                     #   DielectricRegion( 0, 0 , 15,EFLsurface.get_size()[1]/3) # vertical region
                     #DielectricRegion( -EFLsurface.get_size()[1]/EFLsurface.get_size()[0], EFLsurface.get_size()[1]/2 , 15) # angled region
                     DielectricRegion(-EFLsurface.get_size()[1] / EFLsurface.get_size()[0] / 2, EFLsurface.get_size()[1] +50, 15) # larger angled region
                     ]
                    # first region fills screen, later regions are defined above and to the left of their interface line

###MAIN event loop
while True:
    #pin background colour to the value of its permittivity
    for region in dielectricRegions:
        region.draw()

    # Calculate ELFs
    for elf in efls:
        drawnew = nextEFLPoints(elf)
        # Draw ELFs
        if drawnew[0]:
            pygame.draw.line(EFLsurface, black, elf[0].get_tuple(), elf[0].get_tuple(), 1)
        if drawnew[1]:
            pygame.draw.line(EFLsurface, black, elf[-1].get_tuple(), elf[-1].get_tuple(), 1)

    screen.blit(HUD, (0, display_height - Hudsize))
    screen.blit(EFLsurface, (0, 0))  # screen.fill((255, 245, 210))

    #event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.MOUSEBUTTONUP:
            curr_int.mouseUp = Position(pygame.mouse.get_pos())
            if event.button == 1: # left click
                buttonclick=False
                for button in buttons:
                    if button.click(curr_int.mouseUp):
                        buttonclick = True
                if not buttonclick: #here's where we interact with most of the screen. the `simulation'.
                    if curr_int.currentMode == ClickModes.fieldline and curr_int.mouseUp != curr_int.prevMouseUp: # start up a field line calc
                        efls.append([curr_int.mouseUp])
                    elif curr_int.currentMode == ClickModes.addCharge:
                        if curr_int.mousedragging:
                            curr_int.mousedragging = False
                            curr_int.dragPosition = Position((0,0))
                        elif curr_int.newCharge != 0: # add a new charge
                            pointCharges.append(PointCharge(curr_int.mouseUp, curr_int.newCharge))
                            clearEFLs()
                    elif curr_int.currentMode == ClickModes.dielectric and len(dielectricRegions) <=1:
                        dielectricRegions.append(DielectricRegion(0,0,1,curr_int.mouseUp[0]))
                        clearEFLs()
                curr_int.prevMouseUp = curr_int.mouseUp
            elif event.button == 3: #right click
                if curr_int.currentMode == ClickModes.addCharge: #remove a charge with right click
                    pointCharges = [x for x in pointCharges if not x.isClickedOn(curr_int.mouseUp)]
                    clearEFLs()
                elif curr_int.currentMode == ClickModes.dielectric:
                    index= isInWhichRegion(curr_int.mouseUp, dielectricRegions)
                    if index != 0:
                        del dielectricRegions[index]
                        clearEFLs()
            elif event.button ==4: #scroll mouse wheel up
                if curr_int.currentMode == ClickModes.addCharge:
                    curr_int.set_charge(curr_int.newCharge +1)
                elif curr_int.currentMode == ClickModes.dielectric:
                    isInAnyRegion(curr_int.mouseUp, dielectricRegions,action=lambda region: region.set_perm(region.permittivity +1))
                    clearEFLs()
            elif event.button == 5: #scroll mouse wheel down
                if curr_int.currentMode == ClickModes.addCharge:
                    curr_int.set_charge(curr_int.newCharge - 1)
                elif curr_int.currentMode == ClickModes.dielectric:
                    isInAnyRegion(curr_int.mouseUp, dielectricRegions,
                              action=lambda region: region.set_perm(region.permittivity - 1))
                    clearEFLs()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            curr_int.mouseDown = Position(pygame.mouse.get_pos())
            if event.button == 1:  # left click
                if curr_int.currentMode == ClickModes.addCharge:
                    for pointCharge in pointCharges:
                        if pointCharge.isClickedOn(curr_int.mouseDown):
                            curr_int.mousedragging = True
                            curr_int.dragPosition = pointCharge.position
                            clearEFLs()

    curr_int.mousePoint = Position(pygame.mouse.get_pos())
    if isInsideSurface(EFLsurface, curr_int.mousePoint):
        if curr_int.currentMode == ClickModes.addCharge: # displays the charge value that will be placed on click, just above the mouse cursor
            display_at_mouse("q = %s" % str(curr_int.newCharge))
            if curr_int.mousedragging:
                curr_int.dragPosition.move(curr_int.mousePoint - curr_int.prevMousePoint)
        elif curr_int.currentMode == ClickModes.fieldline: # continuously displays the field right at the mouse cursor
            # draw gradient indicator arrow
            nextPoint = getNextPointAlongEFLUsingField(pointCharges,dielectricRegions, curr_int.mousePoint)
            gradientarrowPoint = curr_int.mousePoint + (nextPoint - curr_int.mousePoint) * (
            20 / spaceresolution)  # Position([z * 10 for z in (nextPoint - mousePoint)])
            drawArrow(screen, green, curr_int.mousePoint.get_tuple(), gradientarrowPoint.get_tuple(), 3)
        elif curr_int.currentMode == ClickModes.dielectric: # displays the permittivity right at the mouse cursor
            isInAnyRegion(curr_int.mousePoint,dielectricRegions ,action=lambda region: display_at_mouse(region.permittivity_text()))
    curr_int.prevMousePoint = curr_int.mousePoint

    # Draw charges
    for pointCharge in pointCharges:
        pointCharge.draw()
        #pygame.draw.circle(screen, red if pointCharge.charge > 0 else blue, pointCharge.position, 10, 0)

    # Draw HUD
    for button in buttons:
        button.draw()

    pygame.display.update()

    
