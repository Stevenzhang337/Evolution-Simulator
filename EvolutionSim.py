#taken from CMU 15-112: https://www.cs.cmu.edu/~112/ (lines 2-7)
from cmu_112_graphics import *
import sys
print(f'sudo "{sys.executable}" -m pip install pillow')
print(f'sudo "{sys.executable}" -m pip install requests')
from tkinter import *
from PIL import Image
import math 
import random
import copy
import string
#all images imported are published on https://stevenzh.imgur.com/all
##########################################################################################
#general Helper Functions
def distance(x1,y1,x2,y2):
    return ((x2-x1)**2 + (y2-y1)**2)**.5
def inRange(x1,y1,x2,y2,r):
    return distance(x1,y1,x2,y2) < r
def getRandomDir():
    x = random.uniform(-1,1)
    r = int(random.choice([-1,1]))
    y = r*(1 - x**2)**.5
    return (x,y)
def getBool(boolStr):
    if boolStr == 'True':
        return True
    else:
        return False

##########################################################################################
class Species(object):
    def __init__(self,x, y, speed, size, sense, eatMeat, flee, moderation,sharing,color,numID):
        #static parameters
        self.numID = numID
        self.origX = x
        self.origY = y
        #position and movement parameters
        self.x = x
        self.y = y
        self.dirx = 0
        self.diry = 0
        self.changeDir = True
        #survival parameters
        self.foodEaten = 0
        self.energy = 100
        self.inactive = False #used for moderation trait
        #inherent traits
        self.color = color
        self.speed = speed
        self.size = size
        self.sense = sense
        #mutated traits
        self.eatMeat = eatMeat #is able to eat other species
        self.flee = flee #is able to run away from larger species
        self.moderation = moderation #is able to eat only enough to reproduce then stops
        self.sharing = sharing #all food gathered are shared with another species

    def moveCreature(self):
        if self.energy > 0:
        #dx, dy are unit magnitude of direction
            dx = self.speed * self.dirx
            dy = self.speed * self.diry
            self.x += dx
            self.y += dy
            #each step costs the species some energy based on the below equation
            self.energy -= .0001*(self.size**2*self.speed**2+self.sense)

    def __eq__(self,other):
        return (isinstance(other,Species) and self.origX == other.origX and
                self.origY == other.origY) and self.numID == other.numID
    def __hash__(self):
        return(hash(self.origX,self.origY,self.numID))
    def __repr__(self):
        return f'{self.x},{self.y},{self.speed},{self.size},{self.sense},{self.eatMeat},{self.flee},{self.moderation},{self.color}'
#for invasiveSpecies
class SpeciesLite(Species):
    def __init__(self,dirx,diry,size):
        self.dirx = dirx
        self.diry = diry
        self.size = size

class Food(object):
    def __init__(self, x, y,):
        self.x = x
        self.y = y
        self.size = 5

class FoodIndicator(object):
    def __init__(self,x,y,value,timer):
        self.x = x
        self.y = y
        self.value = value
        self.timer = 5
    def countDown(self):
        self.timer -= 1
    def moveUp(self):
        self.y -= 5
        
##########################################################################################
class Simulate(Mode):
    def appStarted(mode):
        mode.margin = 30
        #simulator stats
        mode.species1 = []
        mode.species2 = []
        mode.invasiveSpecies = []
        mode.numID = 0
        mode.food = []
        mode.crackPosition = []
        #will show popups of food eaten and their values
        mode.foodEatenIndicator = []
        #shows specific species stats
        mode.speciesStats = None
        mode.generation = 0

        #stats for graphs
        mode.avgSpeed = []
        mode.avgSize = []
        mode.avgSense = []
        mode.population = []
        mode.populationSubset = {'Population': [],
                                 'Species1': [],
                                 'Species2': [],
                                 'InvasiveYellow':[],
                                 'InvasivePink':[],
                                 'InvasiveBlack':[],
                                 'InvasiveBrown':[],
                                 'InvasiveWhite':[],
                                 'eatSpeciesTrait':[],
                                 'fleeTrait':[],
                                 'eatModerationTrait':[],
                                 'sharingTrait':[],
                                 'avgSpeed1': [],
                                 'avgSpeed2': [],
                                 'avgSize1': [],
                                 'avgSize2': [],
                                 'avgSense1': [],
                                 'avgSense2': []}
        #generates starting food and species in gen 0
        for i in range(min(45,int(mode.app.setUpMode.settingInput[2]))):
            mode.generateSpecies(mode.species1)
        if getBool(mode.app.setUpMode.settingInput[10]):
            for i in range(min(45,int(mode.app.setUpMode.settingInput[11]))):
                mode.generateSpecies(mode.species2)
        mode.allSpecies = mode.species1 + mode.species2 + mode.invasiveSpecies
        for i in range(int(mode.app.setUpMode.settingInput[0])):
            mode.generateFood()
        #simulator states
        mode.extraGeneratedFood = 0
        mode.extinction = False
        mode.activateDisasterBackground = False
        mode.coolDown = 0
        mode.whiteOut = 0
        mode.allowInvasiveSpecies = False
        mode.allowMutation = getBool(mode.app.setUpMode.settingInput[19])
        #all taken from google images
        mode.foodImage = mode.app.loadImage('https://i.imgur.com/E9CZ6XH.png')
        mode.foodImage = mode.app.scaleImage(mode.foodImage, 1/15)
        mode.groundImage = mode.app.loadImage('https://i.imgur.com/pwu7Zss.jpg')
        mode.groundImage = mode.app.scaleImage(mode.groundImage,1/1.375)
        mode.crackedImage = mode.app.loadImage('https://i.imgur.com/a7rGVar.png')
        mode.crackedImage = mode.app.scaleImage(mode.crackedImage,1/15)
        mode.thunderImage = mode.app.loadImage('https://i.imgur.com/XLZdqG1.png')
        mode.thunderImage = mode.app.scaleImage(mode.thunderImage,2)
        mode.errorMessage = ''

    def keyPressed(mode, event):
        #manually starts new generation or goes back to setupMode
        if event.key == 'Space':
            if mode.extinction:
                mode.app.setUpMode.appStarted()
                mode.app.setActiveMode(mode.app.setUpMode)
            else:
                mode.food = []
                mode.newGeneration()
        #goes to data mode
        elif event.key == 'Enter':
            mode.app.setActiveMode(mode.app.dataMode)
        #creates extinction level event
        elif event.key == 'd' and not mode.activateDisasterBackground:
            mode.createNaturalDisaster()
            mode.createDisaster()
        elif event.key == 'h':
            mode.app.setActiveMode(mode.app.helpMode)
        elif event.key == 'Up':
            mode.generateFood()
            mode.extraGeneratedFood += 1
        elif event.key == 'Down':
            mode.food.pop()
            mode.extraGeneratedFood -= 1
        elif event.key == 'c':
            mode.errorMessage = ''
            mode.app.setActiveMode(mode.app.invasiveSpeciesMode)
        elif event.key == 'i':
            if mode.allowInvasiveSpecies:
                mode.createInvasiveSpecies()
            else:
                mode.errorMessage = 'Create invasive species first'
        elif event.key == 'z':
            mode.species1 = []
            mode.species2 = []
            mode.invasiveSpecies = []
            mode.extinction = True
    
    def mousePressed(mode,event):
        for species in mode.allSpecies:
            if inRange(event.x,event.y,species.x,species.y,species.size+50): #+5 for margin of error
                mode.speciesStats = species
            elif ((event.x < mode.margin) or (event.x > mode.width-mode.margin) or
                 (event.y < mode.margin) or (event.y > mode.height-mode.margin)):
                mode.speciesStats = None


    #initialize environment
    def generateFood(mode):
        #randomly places a food on the environment
        (x,y) = ((random.randint(mode.margin, mode.width-mode.margin)),
                 (random.randint(mode.margin, mode.height-mode.margin)))
        mode.food.append(Food(x,y))
    def generateSpecies(mode,speciesType):
        #randomly places a species on the margin of the environment
        randomStart = random.choice(['startHorizontal','startVertical'])
        if randomStart == 'startHorizontal':
            x = random.randint(0, mode.width)
            y = random.choice([15,mode.height-15]) #choices b/w top or bottom strip
        else: #randomStart == 'startVertical'
            x = random.choice([15,mode.width-15])  #choices b/w left or right strip
            y = random.randint(0,mode.height)
        #initialize species traits
        #comes from setUpMode
        if speciesType == mode.species1:
            speed = min(30,int(mode.app.setUpMode.settingInput[3]))
            size = min(50,int(mode.app.setUpMode.settingInput[4]))
            sense = min(500,int(mode.app.setUpMode.settingInput[5]))
            eatMeat = getBool(mode.app.setUpMode.settingInput[6])
            flee = getBool(mode.app.setUpMode.settingInput[7])
            moderation = getBool(mode.app.setUpMode.settingInput[8])
            sharing = getBool(mode.app.setUpMode.settingInput[9])
            color = 'red'
        else: #speciesType == mode.species2
            speed = min(30,int(mode.app.setUpMode.settingInput[12]))
            size = min(50,int(mode.app.setUpMode.settingInput[13]))
            sense = min(500,int(mode.app.setUpMode.settingInput[14]))
            eatMeat = getBool(mode.app.setUpMode.settingInput[15])
            flee = getBool(mode.app.setUpMode.settingInput[16])
            moderation = getBool(mode.app.setUpMode.settingInput[17])
            sharing = getBool(mode.app.setUpMode.settingInput[18])
            color = 'blue'
        speciesType.append(Species(x,y,speed,size,sense,eatMeat,flee,moderation,sharing,color,mode.numID))
        mode.numID += 1


    #initialize generation
    def checkEndGeneration(mode):
        if mode.food == []:
            return True
            
        for species in mode.allSpecies:
            if not (species.dirx == 0 and species.diry == 0):
                return False
            '''#species with moderation are done within the generation as long as they find 5 apples
            if species.moderation:
                if (species.foodEaten < 5 and species.energy > 0):
                    return False
            elif species.energy > 0:
                return False'''
        return True



    def newGeneration(mode):
        mode.getData()
        mode.errorMessage = ''
        #starts new gen
        mode.speciesDeath(mode.species1)
        mode.speciesDeath(mode.species2)
        mode.speciesDeath(mode.invasiveSpecies)
        #extinction
        if len(mode.allSpecies) == 0:
            mode.extinction = True
            return

        mode.generation += 1
        mode.reproduce(mode.species1)
        mode.reproduce(mode.species2)
        mode.reproduce(mode.invasiveSpecies)
        mode.mutate(mode.species1)
        mode.mutate(mode.species2)
        mode.allSpecies = mode.species1 + mode.species2 + mode.invasiveSpecies

        #replenishes food
        for i in range(int(mode.app.setUpMode. settingInput[0])+mode.extraGeneratedFood):
            mode.generateFood()
        #resets species stats
        for species in mode.allSpecies:
             species.foodEaten = 0
             species.x = species.origX
             species.y = species.origY
             species.energy = 100        
             species.dirx = 0
             species.diry = 0
             species.changeDir = True   
        mode.disasterCoolDown()

    def mutate(mode,speciesType):
        #contains all traits
        #mutateChance 5%
        if mode.allowMutation:
            for species in speciesType:
                #speed Trait (how fast species move)
                mutateSpeed = random.randint(0,39)
                if mutateSpeed == 0:
                    species.speed += 1
                elif mutateSpeed == 1:
                    species.speed -= 1
                #size Trait (how big species are)
                mutateSize = random.randint(0,39)
                if mutateSize == 0:
                    species.size += 2
                elif mutateSize == 1:
                    species.size -= 2
                #sense Trait (range of what they can see)
                mutateSense = random.randint(0,39)
                if mutateSense == 0:
                    species.sense += 5
                elif mutateSense == 1:
                    species.sense -= 5
                #Carnivorious (able to eat other species)
                mutateDiet = random.randint(0,19)
                if mutateDiet == 0:
                    species.eatMeat = True
                #flees from predator trait (flees if species are bigger than them)
                mutateFlee = random.randint(0,19)
                if mutateFlee == 0:
                    species.flee = True      
                #stops eating after gaining enough food to reproduce
                mutateModeration = random.randint(0,19)
                if mutateModeration == 0:
                    species.moderation = True  
                mutateSharing = random.randint(0,19)
                if mutateSharing == 0:
                    species.sharing = True
    def reproduce(mode,speciesType):
        newSpecies = speciesType
        for species in speciesType:
            #reproduce if species have eaten more than 5 foods
            if species.foodEaten > 4:
                RNG = random.randint(0,1)
                #generate horizontal
                if RNG == 0:
                    x = random.randint(0, mode.width)
                    y = random.choice([15,mode.height-15])
                #vertical
                else:
                    x = random.choice([15,mode.width-15])
                    y = random.randint(0,mode.height)
                newSpecies.append(Species(x, y, species.speed, species.size, species.sense,
                                            species.eatMeat, species.flee,species.moderation,species.sharing,species.color,mode.numID))
                mode.numID += 1
                    
        speciesType = newSpecies        
    def speciesDeath(mode,speciesType):
        notDead = speciesType
        for species in speciesType:
            if species.foodEaten < 2:
                notDead.remove(species)
        speciesType = notDead

#traits
    #uses sense Trait
    def senseFood(mode, species):
        shortest = distance(0, 0, mode.width, mode.height)
        for food in mode.food:
            if inRange(species.x, species.y, food.x, food.y, species.sense):
                d = distance(species.x, species.y, food.x, food.y)
                if d < shortest:
                    shortest = d
                    species.dirx = (food.x - species.x)/shortest
                    species.diry = (food.y - species.y)/shortest
                    species.changeDir = True
        if shortest == distance(0, 0, mode.width, mode.height):
            return False
        else:
            species.moveCreature()
            return True
    def senseSpecies(mode, species):
        if species.eatMeat:
            shortest = distance(0, 0, mode.width, mode.height)
            for species2 in mode.allSpecies:
                if (inRange(species.x, species.y, species2.x, species2.y, species.sense) and
                   (species2.size*1.2 < species.size) and
                   (species.color != species2.color)):
                    d = distance(species.x, species.y, species2.x, species2.y)
                    if d < shortest:
                        shortest = d
                        species.dirx = (species2.x - species.x)/shortest
                        species.diry = (species2.y - species.y)/shortest
            if shortest == distance(0, 0, mode.width, mode.height):
                return False
            else:
                species.moveCreature()
                return True
        return False
    #flee trait
    def flee(mode, species):
        if species.flee:
            for species2 in mode.allSpecies:
                if (inRange(species.x, species.y, species2.x, species2.y,species.sense) and
                   (species.size*1.2 < species2.size) and
                    (species.color != species2.color)):
                    d=distance(species.x, species.y, species2.x, species2.y)
                    if d == 0:
                        species.dirx = 1
                        species.diry = 0
                    else:
                        species.dirx = -(species2.x-species.x)/d
                        species.diry = -(species2.y-species.y)/d
                    species.moveCreature()
                    return True
            return False
        return False  
    def moderationTrait(mode,species):
        if species.moderation and species.foodEaten >= 5:
            species.dirx = 0
            species.diry = 0
            species.inactive = True
            return True
        return False
    #movement
    def walkRandom(mode, species):
        if species.changeDir:
            (species.dirx, species.diry) = getRandomDir()
            species.changeDir = False
        species.moveCreature()


    def collideWithWall(mode, species):
        if species.x < 0 or species.x > mode.width:
            species.dirx = -species.dirx
        if species.y < 0 or species.y > mode.height:
            species.diry = -species.diry
    #overall move function
    def move(mode,speciesType):
        #stops motion when food is all eaten
        for species in speciesType:
            if mode.food == []:
                species.dirx = 0
                species.diry = 0
            if not mode.flee(species):
                if not mode.moderationTrait(species):
                    if not mode.senseSpecies(species):
                        if not mode.senseFood(species):
                            mode.walkRandom(species)
            mode.collideWithWall(species)

    #contains sharing food trait 
    def eatFood(mode,speciesType):
        notEaten = mode.food
        for species in speciesType:
            for food in mode.food:
                if inRange(species.x, species.y, food.x, food.y, species.size+10):
                    #sharing trait
                    if species.sharing:
                        species.foodEaten += .5
                        species.energy += 20
                        species2 = random.choice(speciesType)
                        species2.foodEaten += .5
                        species2.energy += 20
                        #foodEaten indicator
                        mode.foodEatenIndicator.append(FoodIndicator(species.x,species.y,'+.5',5))
                        mode.foodEatenIndicator.append(FoodIndicator(species2.x,species2.y,'+.5',5))
                    else:
                        species.foodEaten += 1
                        species.energy += 40
                        #foodEaten indicator
                        mode.foodEatenIndicator.append(FoodIndicator(species.x,species.y,'+1',5))
                    notEaten.remove(food)
        mode.food = notEaten
    
    def moveFoodEatenIndicator(mode):
        tempIndicator = mode.foodEatenIndicator
        for indicator in mode.foodEatenIndicator:
            if indicator.timer == 0:
                tempIndicator.remove(indicator)
            else:
                indicator.countDown()
                indicator.moveUp()

    def eatSpecies(mode,speciesType):
        for species1 in speciesType:
            for species2 in mode.allSpecies:
                if ((species1.eatMeat) and
                    (species1.color != species2.color) and
                    (species1.size >= species2.size*1.2) and
                    (inRange(species1.x, species1.y,species2.x, species2.y,max(species1.size, species2.size) + 5))):
                    if species2 in mode.species1:
                        mode.species1.remove(species2)
                    elif species2 in mode.species2:
                        mode.species2.remove(species2)
                    elif species2 in mode.invasiveSpecies:
                        mode.invasiveSpecies.remove(species2)
                    if species1.sharing:
                        species1.foodEaten += 1
                        species1.energy += 30
                        species3 = random.choice(speciesType)
                        species3.foodEaten += 1
                        species3.energy += 30
                        mode.foodEatenIndicator.append(FoodIndicator(species1.x,species1.y,'+1',5))
                        mode.foodEatenIndicator.append(FoodIndicator(species3.x,species3.y,'+1',5))
                    else:
                        species1.foodEaten += 2
                        species1.energy += 60
                        mode.foodEatenIndicator.append(FoodIndicator(species1.x,species1.y,'+2',5))
                mode.allSpecies = mode.species1 + mode.species2 + mode.invasiveSpecies
#very messy (clean up)
    def getAverages(mode,speciesType):
        if len(speciesType) == 0:
            return (0,0,0)
        totalSpeed = 0
        totalSize = 0
        totalSense = 0
        for species in speciesType:
            totalSpeed += species.speed
            totalSize += species.size
            totalSense += species.sense
        avgSpeed = totalSpeed / len(speciesType)
        avgSize = totalSize / len(speciesType)
        avgSense = totalSense / len(speciesType)
        return(avgSpeed,avgSize,avgSense)

    def getCount(mode):
        countEatMeat = 0
        countFlee = 0
        countModeration = 0
        countSharing = 0
        for species in mode.allSpecies:
            if species.eatMeat:
                countEatMeat += 1
            if species.flee:
                countFlee += 1
            if species.moderation:
                countModeration += 1
            if species.sharing:
                countSharing += 1
        return (countEatMeat, countFlee, countModeration,countSharing)
    
    def countInvasive(mode):
        yellowCount = 0
        pinkCount = 0
        blackCount = 0
        brownCount = 0
        whiteCount = 0
        for species in mode.invasiveSpecies:
            if species.color == 'Yellow':
                yellowCount += 1
            elif species.color == 'Pink':
                pinkCount += 1
            elif species.color == 'Black':
                blackCount += 1
            elif species.color == 'Brown':
                brownCount += 1
            elif species.color == 'White':
                whiteCount += 1
        return (yellowCount, pinkCount,blackCount,brownCount,whiteCount)
        
    def getData(mode):
        avgSpeed1,avgSize1,avgSense1 = mode.getAverages(mode.species1)
        avgSpeed2,avgSize2,avgSense2 = mode.getAverages(mode.species2)
        countEatMeat, countFlee, countModeration,countSharing = mode.getCount()
        countYellow, countPink,countBlack,countBrown,countWhite = mode.countInvasive()
        countSpecies1 = len(mode.species1)
        countSpecies2 = len(mode.species2)
        countPopulation = len(mode.allSpecies)

        newList = mode.populationSubset.get('avgSpeed1')
        newList.append(avgSpeed1)
        mode.populationSubset['avgSpeed1'] = newList
        newList = mode.populationSubset.get('avgSpeed2')
        newList.append(avgSpeed2)
        mode.populationSubset['avgSpeed2'] = newList
        newList = mode.populationSubset.get('avgSize1')
        newList.append(avgSize1)
        mode.populationSubset['avgSize1'] = newList
        newList = mode.populationSubset.get('avgSize2')
        newList.append(avgSize2)
        mode.populationSubset['avgSize2'] = newList
        newList = mode.populationSubset.get('avgSense1')
        newList.append(avgSense1)
        mode.populationSubset['avgSense1'] = newList
        newList = mode.populationSubset.get('avgSense2')
        newList.append(avgSense2)

        newList = mode.populationSubset.get('eatSpeciesTrait')
        newList.append(countEatMeat)
        mode.populationSubset['eatSpeciesTrait'] = newList
        newList = mode.populationSubset.get('fleeTrait')
        newList.append(countFlee)
        mode.populationSubset['fleeTrait'] = newList
        newList = mode.populationSubset.get('eatModerationTrait')
        newList.append(countModeration)
        mode.populationSubset['eatModerationTrait'] = newList
        newList = mode.populationSubset.get('sharingTrait')
        newList.append(countSharing)
        mode.populationSubset['sharingTrait'] = newList

        newList = mode.populationSubset.get('Species1')
        newList.append(countSpecies1)
        mode.populationSubset['Species1'] = newList
        newList = mode.populationSubset.get('Species2')
        newList.append(countSpecies2)
        mode.populationSubset['Species2'] = newList
        newList = mode.populationSubset.get('Population')
        newList.append(countPopulation)
        mode.populationSubset['Population'] = newList

        newList = mode.populationSubset.get('InvasiveYellow')
        newList.append(countYellow)
        mode.populationSubset['InvasiveYellow'] = newList
        newList = mode.populationSubset.get('InvasivePink')
        newList.append(countPink)
        mode.populationSubset['InvasivePink'] = newList
        newList = mode.populationSubset.get('InvasiveBlack')
        newList.append(countBlack)
        mode.populationSubset['InvasiveBlack'] = newList
        newList = mode.populationSubset.get('InvasiveBrown')
        newList.append(countBrown)
        mode.populationSubset['InvasiveBrown'] = newList
        newList = mode.populationSubset.get('InvasiveWhite')
        newList.append(countWhite)
        mode.populationSubset['InvasiveWhite'] = newList
 


    def createNaturalDisaster(mode):
        #kills 50% of species (kills above the average size)
        if mode.generation > 0:
        #crashes on gen 0
            avgSize = mode.populationSubset['Population'][-1]
            for species in mode.allSpecies:
                if species.size > avgSize:
                    if species.color.lower() == 'red':
                        mode.species1.remove(species)
                    elif species.color.lower() == 'blue':
                        mode.species2.remove(species)
                    else:
                        mode.invasiveSpecies.remove(species)
            mode.allSpecies = mode.species1 + mode.species2 + mode.invasiveSpecies
            mode.activateDisasterBackground = True
            mode.whiteOut = 4

    def disasterCoolDown(mode):
        if mode.activateDisasterBackground:
            mode.coolDown += 1
        if mode.coolDown == 7:
            mode.activateDisasterBackground = False
            mode.coolDown = 0
    
    def createDisaster(mode):
        x = random.randint(mode.margin,mode.width-mode.margin)
        y = random.randint(mode.margin,mode.height-mode.margin)
        mode.crackPosition.append((x,y))

        
    def createInvasiveSpecies(mode):
        #randomly places a species on the margin of the environment
        randomStart = random.choice(['startHorizontal','startVertical'])
        if randomStart == 'startHorizontal':
            x = random.randint(0, mode.width)
            y = random.choice([15,mode.height-15]) #choices b/w top or bottom strip
        else: #randomStart == 'startVertical'
            x = random.choice([15,mode.width-15])  #choices b/w left or right strip
            y = random.randint(0,mode.height)
            
        invasiveTraits = mode.app.invasiveSpeciesMode.invasiveSpeciesInput

        speed = int(invasiveTraits[0])
        size = int(invasiveTraits[1])
        sense = int(invasiveTraits[2])
        eatSpeciesTrait = getBool(invasiveTraits[3])
        fleeTrait = getBool(invasiveTraits[4])
        moderationTrait = getBool(invasiveTraits[5])
        sharingTrait = getBool(invasiveTraits[6])
        color = invasiveTraits[7]
        mode.invasiveSpecies.append(Species(x,y,speed,size,sense,eatSpeciesTrait,fleeTrait,moderationTrait,sharingTrait,color,mode.numID))
        mode.numID += 1

    def timerFired(mode):
        mode.move(mode.species1)
        mode.move(mode.species2)
        mode.move(mode.invasiveSpecies)
        mode.eatFood(mode.species1)
        mode.eatFood(mode.species2)
        mode.eatFood(mode.invasiveSpecies)
        mode.moveFoodEatenIndicator()
        mode.eatSpecies(mode.species1)
        mode.eatSpecies(mode.species2)
        mode.eatSpecies(mode.invasiveSpecies)
        if mode.checkEndGeneration():
            mode.newGeneration()

    def drawModerationTrait(mode,canvas,species):
        size = .3*species.size
        canvas.create_oval(species.x-size,species.y-size,species.x+size,species.y+size,fill='green')
    def drawEatMeatTrait(mode,canvas,species):
        #gets the direction the species is moving
        dirx, diry = species.dirx,species.diry
        #gets angle in radians
        angle = math.atan2(diry,dirx)
        #rotates angle 30 degrees in each direction to draw the base of the triangle
        angle1 = angle + math.pi/6
        angle2 = angle - math.pi/6
        (x1,y1) = (species.size*math.cos(angle1),species.size*math.sin(angle1))
        (x2,y2) = (species.size*math.cos(angle2),species.size*math.sin(angle2))
        (x3,y3) = (species.size*3**.5*dirx,species.size*3**.5*diry)
        canvas.create_polygon(species.x+x1,species.y+y1,species.x+x2,species.y+y2,species.x+x3,species.y+y3)
    def drawFleeTrait(mode,canvas,species):
        size = species.size
        dirx,diry = species.dirx,species.diry
        #gets each point of a square
        angle = math.atan2(diry,dirx)
        angle1 = angle + math.atan(1/2)
        angle2 = angle - math.atan(1/2)
        angle3 = angle - math.atan(2/5)
        angle4 = angle + math.atan(2/5)
        (x1,y1) = ((size*(5**.5)/2)*math.cos(angle1),(size*(5**.5)/2)*math.sin(angle1))
        (x2,y2) = ((size*(5**.5)/2)*math.cos(angle2),(size*(5**.5)/2)*math.sin(angle2))
        (x3,y3) = ((size*(29**.5)/4)*math.cos(angle3),(size*(29**.5)/4)*math.sin(angle3))
        (x4,y4) = ((size*(29**.5)/4)*math.cos(angle4),(size*(29**.5)/4)*math.sin(angle4))
        canvas.create_polygon(species.x+x1,species.y+y1,species.x+x2,species.y+y2,
                              species.x+x3,species.y+y3,species.x+x4,species.y+y4)
    def drawSharingTrait(mode,canvas,species):
        dirx,diry = species.dirx,species.diry
        size = species.size
        angle = math.atan2(diry,dirx)
        angle1 = angle + math.pi/2
        angle2 = angle - math.pi/2
        (x1,y1) = (size*math.cos(angle1),size*math.sin(angle1))
        (x2,y2) = (size*math.cos(angle2),size*math.sin(angle2))
        (x3,y3) = (size*(17**.5)/4*math.cos(angle1)+size*(5**.5)/2*dirx,size*(17**.5)/4*math.sin(angle1)+size*(5**.5)/2*diry)
        (x4,y4) = (size*(17**.5)/4*math.cos(angle2)+size*(5**.5)/2*dirx,size*(17**.5)/4*math.sin(angle2)+size*(5**.5)/2*diry)
        canvas.create_line(species.x+x1,species.y+y1,species.x+x3,species.y+y3)
        canvas.create_line(species.x+x2,species.y+y2,species.x+x4,species.y+y4)
        


    def redrawAll(mode, canvas):
        #environment field
        if mode.activateDisasterBackground:
            colorlist = ['dimgrey','gray','darkgray','silver','lightgray','gainsboro','whitesmoke']
            color  = colorlist[mode.coolDown]
        else:
            color = 'saddlebrown'
        canvas.create_rectangle(0, 0,mode.width, mode.height,fill = color)
        canvas.create_image(mode.width//2,mode.height//2, image=ImageTk.PhotoImage(mode.groundImage))
        for (x,y) in mode.crackPosition:
            canvas.create_image(x,y,image=ImageTk.PhotoImage(mode.crackedImage))
        #texts
        canvas.create_text(mode.width//2, mode.height-mode.margin//2,text = 'Press h for Controls',
                         font = 'Ariel 30')
        canvas.create_text(mode.width//2, 20,
                    text = f'Generation: {mode.generation}', font = 'Ariel 20')
        #food         
        for food in mode.food:
            canvas.create_image(food.x,food.y,image=ImageTk.PhotoImage(mode.foodImage))
        for indicator in mode.foodEatenIndicator:
            canvas.create_text(indicator.x,indicator.y,text = indicator.value)
        for species in mode.species1:
            if species.energy <= 0:
                color = 'grey'
            else:
                color = species.color
            canvas.create_oval(species.x-species.size,species.y-species.size,
                               species.x+species.size,species.y+species.size,
                                fill = color)
        for species in mode.species2:
            if species.energy <= 0:
                color = 'grey'
            else:
                color = species.color
            canvas.create_oval(species.x-species.size,species.y-species.size,
                               species.x+species.size,species.y+species.size,
                               fill = color)
        for species in mode.invasiveSpecies:
            if species.energy <= 0:
                color = 'grey'
            else:
                color = species.color
            canvas.create_oval(species.x-species.size,species.y-species.size,
                               species.x+species.size,species.y+species.size,
                               fill = color)
        for species in mode.allSpecies:
            if species.eatMeat:
                mode.drawEatMeatTrait(canvas,species)
            if species.flee:
                mode.drawFleeTrait(canvas,species)
            if species.moderation:
                mode.drawModerationTrait(canvas,species)
            if species.sharing:
                mode.drawSharingTrait(canvas,species)
            
        #display specific stats
        if mode.speciesStats != None:
            species = mode.speciesStats
            canvas.create_text(mode.speciesStats.x+10,mode.speciesStats.y-36,text=f'numID:{mode.speciesStats.numID}',anchor = 'w')
            canvas.create_text(mode.speciesStats.x+10,mode.speciesStats.y-24,text=f'Food Eaten:{mode.speciesStats.foodEaten}',anchor = 'w')
            canvas.create_text(mode.speciesStats.x+10,mode.speciesStats.y-12,text=f'Energy:%0.1f' % mode.speciesStats.energy,anchor = 'w')
            canvas.create_text(mode.speciesStats.x-10,mode.speciesStats.y-36,text=f'Speed:{mode.speciesStats.speed}',anchor = 'e')
            canvas.create_text(mode.speciesStats.x-10,mode.speciesStats.y-24,text=f'Size:{mode.speciesStats.size}',anchor = 'e')
            canvas.create_text(mode.speciesStats.x-10,mode.speciesStats.y-12,text=f'Sense:{mode.speciesStats.sense}',anchor = 'e')
            #mutated Traits
            mutatedTraits = ['Eat Species Trait','Flee Trait','Eat Moderation Trait','Sharing Trait' ]
            mutatedList = [mode.speciesStats.eatMeat,mode.speciesStats.flee,mode.speciesStats.moderation,mode.speciesStats.sharing]
            line = 0
            for i in range(len(mutatedList)):
                if mutatedList[i]:
                    line += 1
                    canvas.create_text(mode.speciesStats.x,mode.speciesStats.y+15*line,text=mutatedTraits[i])
            canvas.create_oval(mode.speciesStats.x-mode.speciesStats.sense,mode.speciesStats.y-mode.speciesStats.sense,
                            mode.speciesStats.x+mode.speciesStats.sense,mode.speciesStats.y+mode.speciesStats.sense)
        #whiteOut from natural Disaster
        if mode.whiteOut > 0:
            canvas.create_image(mode.width//2,mode.height//2,image=ImageTk.PhotoImage(mode.thunderImage))
            mode.whiteOut -= 1


        if mode.extinction:
            canvas.create_text(mode.width//2,mode.height//2, text='Extinction has Occured', font = 'Ariel 50')
            canvas.create_text(mode.width//2,mode.height//2+50, text='Press Space to Restart', font = 'Ariel 50')
        canvas.create_text(mode.width//2,mode.height//2,text=mode.errorMessage,font='Ariel 50')

##########################################################################################
class setUpMode(Mode):
    def appStarted(mode):
        mode.inputNum = None
        mode.currentSetting = 0 #indexes the list 'setting'
        mode.margin = 30
        mode.spacing = 30
        mode.settingLines = ['Food generated per Generation', #0
                             'Species 1 (red):',              #1
                             'Initial Species 1 Population',  #2
                             '      Initial Speed',           #3    
                             '      Initial Size',            #4
                             '      Initial Sense',           #5
                             '      Eat Species Trait',       #6
                             '      Flee Trait',              #7
                             '      Moderation Trait',        #8
                             '      Sharing Trait',           #9
                             'Species 2 (blue):',             #10
                             'Initial Species 2 Population',  #11
                             '      Initial Speed',           #12
                             '      Initial Size',            #13
                             '      Initial Sense',           #14
                             '      Eat Species Trait',       #15
                             '      Flee Trait',              #16
                             '      Moderation Trait',        #17
                             '      Sharing Trait',           #18
                             'Allow Mutations']               #19
        mode.controlMessages = ['Press Left or Right Arrow to Scroll Options', 'Input Number']
        mode.infoMessages = ['Determines how many food in each generation (species need to eat 2 food to survive,5 to reproduce)',
                             'Always True; Customize the traits below',
                             'Determines how many of species 1 are generated at generation 0',
                             'Initial Speed species 1 begins with; may mutate later',
                             'Initial Size species 1 begins with; may mutate later',
                             'Initial Sense (used to track food/other species) species 1 begins with; may mutate later',
                             'Ability to eat other species if they are at least 1.2x bigger',
                             'Ability to run from predators big enough to eat them',
                             'Creature stops eating once it finds enough food to reproduce(stops at 5 food)',
                             'Creatures will share food with another of the same species and gain half the energy',
                             'Toggle whether you want a second species with different traits in the environment',
                             'Determines how many of species 2 are generated at generation 0',
                             'Initial Speed species 2 begins with; may mutate later',
                             'Initial Size species 2 begins with; may mutate later',
                             'Initial Sense (used to track food/other species) species 2 begins with; may mutate later',
                             'Ability to eat other species if they are at least 1.2x bigger',
                             'Ability to run from predators big enough to eat them',
                             'Creature stops eating once it finds enough food to reproduce(stops at 5 food)',
                             'Creatures will share food with another of the same species and gain half the energy',
                             'Creatures will not mutate traits from generation to generation']
        mode.settingInputLines = ['______']*len(mode.settingLines)
        #indicies (0,2,3,4,5,10,11,12,13) require numerical inputs
        #indicies (1,6,7,8,9,14,15,16) require boolean input
        mode.numInputIndex = [0,2,3,4,5,11,12,13,14]
        mode.boolInputIndex = [1,6,7,8,9,10,15,16,17,18,19]
        mode.settingInput = ['',
                             'True',
                             '',
                             '10',
                             '10',
                             '100',
                             'False',
                             'False',
                             'False',
                             'False',
                             'False',
                             '',
                             '',
                             '',
                             '',
                             '',
                             '',
                             '',
                             '',
                             'True']
        mode.currSetting = 0
        mode.initFood = ''
        mode.initSpecies = ''
        mode.errorMessage = ''


    def keyPressed(mode, event):
        mode.errorMessage = ''
        #starts simulation
        if event.key == 'Space':
            #crashes when species2 is true and its traits are unfilled
            if mode.settingInput[0] == '' or mode.settingInput[2] == '':
                mode.errorMessage = 'Please Fill In The Parameters'
            else:
                mode.app.setActiveMode(mode.app.simulateMode)
                mode.app.simulateMode.appStarted()

        #goes down the setting
        elif event.key == 'Enter':
            mode.currSetting = (mode.currSetting + 1) % len(mode.settingLines)
        #alternative
        elif event.key == 'Up':
            mode.currSetting = (mode.currSetting - 1) % len(mode.settingLines)
        elif event.key == 'Down':
            mode.currSetting = (mode.currSetting + 1) % len(mode.settingLines)
        
        #numerical input for settings
        elif ((mode.currSetting in mode.numInputIndex) and event.key.isdigit()):
            #invalidates species 2 settings
            if mode.settingInput[10] == 'False' and mode.currSetting > 10:
                return
            result = mode.settingInput[mode.currSetting]
            #only allows input up to 3 digits for sense traits
            if (mode.currSetting == 5 or mode.currSetting == 14) and len(result) < 3:
                result += str(event.key)
            #other traits can have up to 2 digit
            elif len(result) < 2:
                result += str(event.key)
            mode.settingInput[mode.currSetting] = result
        #delete numerical input for settings
        elif ((mode.currSetting in mode.numInputIndex) and event.key == 'Delete'):
            #invalid settings
            if mode.settingInput[10] == 'False' and mode.currSetting > 10:
                return
            result = mode.settingInput[mode.currSetting]
            result = result[:-1]
            mode.settingInput[mode.currSetting] = result

        #boolean input for settings
        elif ((mode.currSetting in mode.boolInputIndex) and (event.key == 'Right' or event.key == 'Left')):
            #invalid Settings
            if mode.currSetting == 1:
                return
            elif mode.settingInput[10] == 'False' and 10 < mode.currSetting < 18:
                return
            result = mode.settingInput[mode.currSetting]
            if result == 'True':
                result = 'False'
            else: #result == 'False' or result = ''
                result = 'True'
            mode.settingInput[mode.currSetting] = result
            
    def redrawAll(mode, canvas):
        #green background
        canvas.create_rectangle(0,0, mode.width,mode.height, fill = 'green')
        #title
        canvas.create_text(mode.width//2, 30, text = 'Initialize Environment',
                           font = 'Ariel 30', fill = 'Beige')
        canvas.create_text(mode.width//2, 60, text = 'Press space when done',
                           font = 'Ariel 30', fill = 'Beige')
        canvas.create_text(mode.width//2,mode.height-3*mode.margin,
                           text='*Each species starts with 100 energy and expends them based on the equation: .0001*size^2*speed^2+sense)',
                           font='Ariel 15',fill='beige')
        for line in range(len(mode.settingLines)):
            if mode.currSetting == line:
                #highlight line
                lineColor = 'yellow'
                #messages for currSetting
                if mode.errorMessage == '':
                    canvas.create_text(mode.width//2,mode.height-2*mode.margin, text = mode.infoMessages[line], font = 'Ariel 15',fill='beige')
                    if mode.currSetting in mode.numInputIndex:
                        canvas.create_text(mode.width//2,mode.height-mode.margin, text = mode.controlMessages[1], font = 'Ariel 20',fill='beige')
                    else: # in boolInputIndex
                        canvas.create_text(mode.width//2,mode.height-mode.margin, text = mode.controlMessages[0], font = 'Ariel 20',fill='beige')
                else:
                    canvas.create_text(mode.width//2,mode.height-2*mode.margin, text = mode.errorMessage, font = 'Ariel 20',fill='beige')
            #gray out invalid settings
            elif mode.settingInput[10] == 'False' and 10 < line < 19:
                lineColor = 'gray'
            else:
                lineColor = 'black'

            canvas.create_text(mode.margin,mode.spacing*(line+3), text = mode.settingLines[line],
                                font = 'Ariel 25',anchor='w',fill=lineColor)
            canvas.create_text(mode.width-mode.margin,mode.spacing*(line+3),text = mode.settingInputLines[line],
                                 font = 'Ariel 25',anchor = 'e',fill=lineColor)
            canvas.create_text(mode.width-mode.margin,mode.spacing*(line+3),text = mode.settingInput[line],
                                font = 'Ariel 25',anchor='e', fill=lineColor)
            
            
##########################################################################################
class HelpMode(Mode):
    def appStarted(mode):
        mode.spacing = 60
        mode.margin = 80
        mode.helpScreenLines = ['HelpScreen',
                                'Press "d" for Natural Disaster(kills any species above the average size)',
                                'Press "Space" to manually go to the next generation',
                                'Press "Enter" to go to Data Screen',
                                'Press "Up" to add more apples',
                                'Press "Down" to delete apples',
                                'Press "c" to create invasive Species',
                                'Press "i" to summon invasive Species',
                                'Click on species to see stats',
                                'Click outside the environment to close stats',
                                'press "z" to end simulation',
                                'Press "h" to go back']
        mode.foodImage = mode.app.loadImage('https://i.imgur.com/E9CZ6XH.png')
        mode.foodImage = mode.app.scaleImage(mode.foodImage,1/3)
    def keyPressed(mode,event):
        if event.key == 'h':
            mode.app.setActiveMode(mode.app.simulateMode)
    def redrawAll(mode,canvas):
        canvas.create_rectangle(0,0,mode.width,mode.height,fill='green')
        for i in range(len(mode.helpScreenLines)):
            if i == 0:
                color = 'white'
            else:color = 'black'
            canvas.create_text(mode.width//2,mode.spacing*(i+1), text = mode.helpScreenLines[i], font = 'Ariel 25',fill=color)
        canvas.create_image(mode.width-mode.margin,mode.height-mode.margin,image=ImageTk.PhotoImage(mode.foodImage))
##########################################################################################    
class invasiveSpeciesMode(Mode):
    def appStarted(mode):
        mode.spacing = 45
        mode.margin = 50
        mode.currTrait = 0
        mode.invasiveSpeciesTrait = ['Speed',
                                     'Size',
                                     'Sense',
                                     'Eat Species Trait',
                                     'Flee Trait',
                                     'Eat Moderation Trait',
                                     'Sharing Trait',
                                     'Color']
        mode.invasiveSpeciesLines = ['______']*len(mode.invasiveSpeciesTrait)
        mode.numInput = [0,1,2]
        mode.boolInput = [3,4,5,6]
        mode.colorInput = [7]
        mode.possibleColors = ['Yellow','Pink','Black','Brown','White']
        mode.currColor = 0
        mode.invasiveSpeciesInput = ['10',
                                     '10',
                                     '100',
                                     'False',
                                     'False',
                                     'False',
                                     'False',
                                     'Yellow']
        mode.app.simulateMode.allowInvasiveSpecies = True
        mode.posx = mode.width//2
        mode.foodImage = mode.app.loadImage('https://i.imgur.com/E9CZ6XH.png')
        mode.foodImage = mode.app.scaleImage(mode.foodImage, 1/15)
        mode.foodx = mode.margin
        mode.dirx = 1

    
    def getRandomPosition(mode):
        x = random.randint(mode.margin,mode.width-mode.margin)
        return x
    
    def eatFood(mode):
        if mode.invasiveSpeciesInput[1] == '':
            r = 0
        else:
            r = int(mode.invasiveSpeciesInput[1])+5
        if inRange(mode.foodx,0,mode.posx,0,r):
            mode.foodx = mode.getRandomPosition()

    #can probably get rid of this by modifying the functions in simulate
    def drawModerationTrait(mode,canvas):
        size = .3*min(50,int(mode.invasiveSpeciesInput[1]))
        canvas.create_oval(mode.posx-size,mode.height-2.5*mode.margin-size,
                           mode.posx+size,mode.height-2.5*mode.margin+size,fill='green')
    def drawEatMeatTrait(mode,canvas):
        size = min(50,int(mode.invasiveSpeciesInput[1]))
        #gets the direction the species is moving
        dirx= mode.dirx
        #gets angle in radians
        angle = math.atan2(0,dirx)
        #rotates angle 30 degrees in each direction to draw the base of the triangle
        angle1 = angle + math.pi/6
        angle2 = angle - math.pi/6
        (x1,y1) = (size*math.cos(angle1),size*math.sin(angle1))
        (x2,y2) = (size*math.cos(angle2),size*math.sin(angle2))
        (x3,y3) = (size*3**.5*dirx,0)
        canvas.create_polygon(mode.posx+x1,mode.height-2.5*mode.margin+y1,
                              mode.posx+x2,mode.height-2.5*mode.margin+y2,
                              mode.posx+x3,mode.height-2.5*mode.margin+y3)
    def drawFleeTrait(mode,canvas):
        size = min(50,int(mode.invasiveSpeciesInput[1]))
        dirx = mode.dirx
        #gets each point of a square
        angle = math.atan2(0,dirx)
        angle1 = angle + math.atan(1/2)
        angle2 = angle - math.atan(1/2)
        angle3 = angle - math.atan(2/5)
        angle4 = angle + math.atan(2/5)
        (x1,y1) = ((size*(5**.5)/2)*math.cos(angle1),(size*(5**.5)/2)*math.sin(angle1))
        (x2,y2) = ((size*(5**.5)/2)*math.cos(angle2),(size*(5**.5)/2)*math.sin(angle2))
        (x3,y3) = ((size*(29**.5)/4)*math.cos(angle3),(size*(29**.5)/4)*math.sin(angle3))
        (x4,y4) = ((size*(29**.5)/4)*math.cos(angle4),(size*(29**.5)/4)*math.sin(angle4))
        canvas.create_polygon(mode.posx+x1,mode.height-2.5*mode.margin+y1,
                              mode.posx+x2,mode.height-2.5*mode.margin+y2,
                              mode.posx+x3,mode.height-2.5*mode.margin+y3,
                              mode.posx+x4,mode.height-2.5*mode.margin+y4)
    def drawSharingTrait(mode,canvas):
        dirx = mode.dirx
        size = min(50,int(mode.invasiveSpeciesInput[1]))
        angle = math.atan2(0,dirx)
        angle1 = angle + math.pi/2
        angle2 = angle - math.pi/2
        (x1,y1) = (size*math.cos(angle1),size*math.sin(angle1))
        (x2,y2) = (size*math.cos(angle2),size*math.sin(angle2))
        (x3,y3) = (size*(17**.5)/4*math.cos(angle1)+size*(5**.5)/2*dirx,size*(17**.5)/4*math.sin(angle1))
        (x4,y4) = (size*(17**.5)/4*math.cos(angle2)+size*(5**.5)/2*dirx,size*(17**.5)/4*math.sin(angle2))
        canvas.create_line(mode.posx+x1,mode.height-2.5*mode.margin+y1,mode.posx+x3,mode.height-2.5*mode.margin+y3)
        canvas.create_line(mode.posx+x2,mode.height-2.5*mode.margin+y2,mode.posx+x4,mode.height-2.5*mode.margin+y4)

    def timerFired(mode):
        mode.eatFood()

    def keyPressed(mode,event):
        #goes down the setting
        if event.key == 'Enter':
            mode.currTrait = (mode.currTrait + 1) % len(mode.invasiveSpeciesTrait)
        #alternative
        elif event.key == 'Up':
            mode.currTrait = (mode.currTrait - 1) % len(mode.invasiveSpeciesTrait)
        elif event.key == 'Down':
             mode.currTrait = (mode.currTrait + 1) % len(mode.invasiveSpeciesTrait)
        #numInput
        elif ((mode.currTrait in mode.numInput) and event.key.isdigit()):
            result = mode.invasiveSpeciesInput[mode.currTrait]
            #only allows input up to 3 digits for sense trait
            if mode.currTrait == 2  and len(result) < 3:
                result += str(event.key)
            elif len(result) < 2:
                result += str(event.key)
            mode.invasiveSpeciesInput[mode.currTrait] = result
        #delete button
        elif ((mode.currTrait in mode.numInput) and event.key == 'Delete'):
            result = mode.invasiveSpeciesInput[mode.currTrait]
            result = result[:-1]
            mode.invasiveSpeciesInput[mode.currTrait] = result
        #ColorInput
        elif ((mode.currTrait in mode.colorInput) and (event.key == 'Right' or event.key == 'Left')):
            if event.key == 'Right':
                mode.currColor = (mode.currColor + 1) % len(mode.possibleColors)
            else: #event.key == 'Left':
                mode.currColor = (mode.currColor - 1) % len(mode.possibleColors)
            mode.invasiveSpeciesInput[mode.currTrait] = mode.possibleColors[mode.currColor]
        
        #boolean input for settings
        elif ((mode.currTrait in mode.boolInput) and (event.key == 'Right' or event.key == 'Left')):
            result = mode.invasiveSpeciesInput[mode.currTrait]
            if result == 'True':
                result = 'False'
            else: #result == 'False' or result = ''
                result = 'True'
            mode.invasiveSpeciesInput[mode.currTrait] = result

        elif event.key == 'c':
            mode.app.setActiveMode(mode.app.simulateMode)
        #interactive invasive species display
        elif event.key == 'Right':
            mode.posx = (mode.posx + 20)%mode.width
            mode.dirx = 1
        elif event.key == 'Left':
            mode.posx = (mode.posx - 20)%mode.width
            mode.dirx = -1
    def redrawAll(mode,canvas):
        canvas.create_rectangle(0,0,mode.width,mode.height,fill='green')
        canvas.create_text(mode.width//2, mode.margin, text='Create traits to summon invasive species',font = 'Ariel 30')
        canvas.create_text(mode.width//2, mode.height - 7*mode.margin,text='*Invasive Species cannot mutate', font = 'Ariel 25')
        canvas.create_text(mode.width//2, mode.height - 6*mode.margin,text='Try moving around',font = 'Ariel 25')
        canvas.create_text(mode.width//2, mode.height - 5*mode.margin,text='Press c to return', font = 'Ariel 25')
        for i in range(len(mode.invasiveSpeciesTrait)):
            if mode.currTrait == i:
                color = 'yellow'
            else: color = 'black'
            canvas.create_text(mode.margin, 2*mode.margin+mode.spacing*i, text = mode.invasiveSpeciesTrait[i],font = 'Ariel 30', anchor = 'w',fill=color)
            canvas.create_text(mode.width-mode.margin, 2*mode.margin+mode.spacing*i, text = mode.invasiveSpeciesLines[i], font = 'Ariel 30', anchor='s',fill=color)
            canvas.create_text(mode.width-mode.margin, 2*mode.margin+mode.spacing*i, text = mode.invasiveSpeciesInput[i], font = 'Ariel 30', anchor='s',fill=color)
        #species representation
        #size
        if mode.invasiveSpeciesInput[1]== '':
            size = 0
        else: size = min(50,int(mode.invasiveSpeciesInput[1]))
        #sense
        if mode.invasiveSpeciesInput[2]== '':
            sense = 0
        else: sense = min(500,int(mode.invasiveSpeciesInput[2]))
        color = mode.invasiveSpeciesInput[7]


        canvas.create_oval(mode.posx-size,mode.height-2.5*mode.margin-size,mode.posx+size,mode.height-2.5*mode.margin+size,fill=color)
        canvas.create_oval(mode.posx-sense,mode.height-2.5*mode.margin-sense,mode.posx+sense,mode.height-2.5*mode.margin+sense,)
        canvas.create_image(mode.foodx,mode.height-2.5*mode.margin,image=ImageTk.PhotoImage(mode.foodImage))
        if mode.invasiveSpeciesInput[1] != '':
            if getBool(mode.invasiveSpeciesInput[3]):
                mode.drawEatMeatTrait(canvas)
            if getBool(mode.invasiveSpeciesInput[4]):
                mode.drawFleeTrait(canvas)
            if getBool(mode.invasiveSpeciesInput[5]):
                mode.drawModerationTrait(canvas)
            if getBool(mode.invasiveSpeciesInput[6]):
                mode.drawSharingTrait(canvas)

##########################################################################################         
class dataMode(Mode):
    #add descriptions for each graph
    def appStarted(mode):
        mode.margin = 80
        mode.graph = 0
        mode.subPopulation = 0
        mode.button1Color = 'cyan'
        mode.button2Color = 'cyan'
        mode.button3Color = 'cyan'
        mode.button4Color = 'cyan'
        mode.button5Color = 'cyan'
        
    def keyPressed(mode, event):
        if event.key == 'Enter':
            mode.app.setActiveMode(mode.app.simulateMode)
        elif event.key == 'Right':
            mode.graph = (mode.graph + 1)%4
        elif event.key == 'Left':
            mode.graph = (mode.graph - 1)%4
        elif event.key == 'Space' and mode.graph == 3:
            mode.subPopulation = (mode.subPopulation + 1)%3

    
    def mousePressed(mode,event):
        if (event.x in range(mode.width-mode.margin,mode.width) and
           event.y in range(mode.margin,2*mode.margin)):
           mode.button1Color = 'yellow'
        else:mode.button1Color = 'cyan'
        if (event.x in range(mode.width-mode.margin,mode.width) and
            event.y in range(int(2.5*mode.margin),int(3.5*mode.margin))):
           mode.button2Color = 'yellow'
        else:mode.button2Color = 'cyan'
        if (event.x in range(mode.width-mode.margin,mode.width) and
           event.y in range(4*mode.margin,5*mode.margin)):
           mode.button3Color = 'yellow'
        else:mode.button3Color = 'cyan'
        if (event.x in range(mode.width-mode.margin,mode.width) and
           event.y in range(int(5.5*mode.margin),int(6.5*mode.margin))):
           mode.button4Color = 'yellow'
        else:mode.button4Color = 'cyan'
        if (event.x in range(mode.width-mode.margin,mode.width) and
           event.y in range(7*mode.margin,8*mode.margin)):
           mode.button5Color = 'yellow'
        else:mode.button5Color = 'cyan'
    
    def labelAxis(mode,canvas,maxYValue):
        #x-axis (generations)
        generation = mode.app.simulateMode.generation
        #length of x-axis segmented by number of generations
        intervalx=(mode.width-2*mode.margin)//generation
        #spaces out the x-axis labels
        for x in range(generation):
            if generation <= 30:
                canvas.create_text(mode.margin+x*intervalx, mode.height-mode.margin+15, text = x)
            elif generation <= 100:
                if x % 5 == 0:
                    canvas.create_text(mode.margin+x*intervalx, mode.height-mode.margin+10, text = x)
            elif generation <= 250:
                if x % 10 == 0:
                    canvas.create_text(mode.margin+x*intervalx, mode.height-mode.margin+10, text = x)

        #y-axis
        totalPoints = 20
        intervaly=(mode.height-2*mode.margin)//totalPoints
        for y in range(totalPoints):
            yValue = y*maxYValue//20
            canvas.create_text(mode.margin-10,mode.height-mode.margin-y*intervaly, text = yValue)
    
    def drawGraph(mode,canvas,name,dataList,maxYValue,fill=None,shade=None):
        #creates title on top of graph
        canvas.create_text(mode.width//2, mode.margin, text=name, font = 'Ariel 30')
        #divides the x and y axis
        intervalx = (mode.width-2*mode.margin)//mode.app.simulateMode.generation
        intervaly = (mode.height-2*mode.margin)//maxYValue
        for i in range(mode.app.simulateMode.generation):
            data1 = dataList[i]
            data2 = dataList[i-1]

            #data lines
            if i > 0:
                if shade != None:
                    canvas.create_polygon(mode.margin+(i)*intervalx, mode.height-mode.margin,
                                            mode.margin+(i)*intervalx,mode.height-mode.margin-data1*intervaly,
                                            mode.margin+(i-1)*intervalx,mode.height-mode.margin-data2*intervaly,
                                            mode.margin+(i-1)*intervalx, mode.height-mode.margin,fill=fill)
                else:
                   canvas.create_line(mode.margin+(i)*intervalx,mode.height-mode.margin-data1*intervaly,
                            mode.margin+(i-1)*intervalx,mode.height-mode.margin-data2*intervaly, fill = fill)
            #data points
            #dataPoint Size
            r = 3
            canvas.create_oval(mode.margin+(i)*intervalx-r,mode.height-mode.margin-data1*intervaly-r,
                    mode.margin+(i)*intervalx+r,mode.height-mode.margin-data1*intervaly+r,fill = fill)
    def redrawAll(mode, canvas):
        #background
        canvas.create_rectangle(0,0,mode.width,mode.height, fill = 'green')
        canvas.create_text(mode.width//2,mode.margin//2,text='Press "Enter" to go back',font = 'Ariel 30',fill='White')
        #axis lines
        canvas.create_line(mode.margin,mode.margin,mode.margin,mode.height-mode.margin, width=2)
        canvas.create_line(mode.margin,mode.height-mode.margin,mode.width-mode.margin,mode.height-mode.margin,width=2)
        if mode.app.simulateMode.generation > 0:
            #average Speed Graph
            if mode.graph == 0:
                maxY = max(20, max(mode.app.simulateMode.populationSubset['avgSpeed1']),max(mode.app.simulateMode.populationSubset['avgSpeed2']))
                mode.drawGraph(canvas,'Average Speed', mode.app.simulateMode.populationSubset['avgSpeed1'],maxY,fill = 'red')
                mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['avgSpeed2'],maxY,fill='blue')
                mode.labelAxis(canvas,maxY)
            #average Size Graph
            if mode.graph == 1:
                maxY = max(20, max(mode.app.simulateMode.populationSubset['avgSize1']),max(mode.app.simulateMode.populationSubset['avgSize2']))
                mode.drawGraph(canvas,'Average Size', mode.app.simulateMode.populationSubset['avgSize1'],maxY,fill = 'red')
                mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['avgSize2'],maxY,fill='blue')
                mode.labelAxis(canvas,maxY)
            #average Sense Graph
            if mode.graph == 2:
                maxY = max(160, max(mode.app.simulateMode.populationSubset['avgSense1']),max(mode.app.simulateMode.populationSubset['avgSense2']))
                mode.drawGraph(canvas,'Average Sense', mode.app.simulateMode.populationSubset['avgSense1'],maxY, fill = 'red')
                mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['avgSense2'],maxY, fill = 'blue')
                mode.labelAxis(canvas,maxY)
            #Population Graph
            if mode.graph == 3:
                maxY = max(30, max(mode.app.simulateMode.populationSubset['Population']))
                mode.drawGraph(canvas,'Population Size',mode.app.simulateMode.populationSubset['Population'],maxY,'Purple')
                mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['Species1'],maxY,'Red')
                mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['Species2'],maxY, 'Blue')


                mode.labelAxis(canvas,maxY)
                #settings to see the graph of subpopulation

                #eatspecies button
                canvas.create_rectangle(mode.width,mode.margin,mode.width-mode.margin,2*mode.margin,
                fill=mode.button1Color)
                canvas.create_text(mode.width-.5*mode.margin,1.5*mode.margin,text='Eat Species',anchor='s')
                canvas.create_text(mode.width-.5*mode.margin,1.5*mode.margin,text='Trait',anchor='n')
                #flee trait button
                canvas.create_rectangle(mode.width,2.5*mode.margin,mode.width-mode.margin,3.5*mode.margin,
                fill=mode.button2Color)
                canvas.create_text(mode.width-.5*mode.margin,3*mode.margin,text='Flee Trait')
                #moderation trait
                canvas.create_rectangle(mode.width,4*mode.margin,mode.width-mode.margin,5*mode.margin,
                fill=mode.button3Color)
                canvas.create_text(mode.width-.5*mode.margin,4.5*mode.margin,text='Moderation',anchor='s')
                canvas.create_text(mode.width-.5*mode.margin,4.5*mode.margin,text='Trait',anchor='n')
                #sharing trait
                canvas.create_rectangle(mode.width,5.5*mode.margin,mode.width-mode.margin,6.5*mode.margin,
                fill=mode.button4Color)
                canvas.create_text(mode.width-.5*mode.margin,6*mode.margin,text='Sharing',anchor='n')
                canvas.create_text(mode.width-.5*mode.margin,6*mode.margin,text='Trait',anchor='s')
                #invasion species Trait
                canvas.create_rectangle(mode.width,7*mode.margin,mode.width-mode.margin,8*mode.margin,
                fill=mode.button5Color)
                canvas.create_text(mode.width-.5*mode.margin,7.5*mode.margin,text='Invasive',anchor='n')
                canvas.create_text(mode.width-.5*mode.margin,7.5*mode.margin,text='Species',anchor='s')

                #activate graph
                if mode.button1Color == 'yellow':
                    mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['eatSpeciesTrait'],maxY,'Gray')
                elif mode.button2Color == 'yellow':
                    mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['fleeTrait'],maxY,'Gray')
                elif mode.button3Color == 'yellow':
                    mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['eatModerationTrait'],maxY,'Gray')
                elif mode.button4Color == 'yellow':
                    mode.drawGraph(canvas,'', mode.app.simulateMode.populationSubset['sharingTrait'],maxY,'Gray')
                elif mode.button5Color == 'yellow':
                    mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['InvasiveYellow'],maxY,'Yellow')
                    mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['InvasivePink'],maxY,'Pink')
                    mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['InvasiveBlack'],maxY,'Black')
                    mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['InvasiveBrown'],maxY,'Brown')
                    mode.drawGraph(canvas,'',mode.app.simulateMode.populationSubset['InvasiveWhite'],maxY,'White')
        else:
            canvas.create_text(mode.width//2,mode.height//2, text='No Available Data',font = 'Ariel 50')
##########################################################################################
class splashScreenMode(Mode):
    def appStarted(mode):
        mode.margin = 220
        #created and drawn by friend:Kevin Kim
        mode.splashScreen = mode.app.loadImage('https://i.imgur.com/Dwo1kFd.jpg')
        mode.splashScreen = mode.app.scaleImage(mode.splashScreen,1/2.115)
    def keyPressed(mode,event):
        mode.app.setActiveMode(mode.app.setUpMode)
    def redrawAll(mode,canvas):
        canvas.create_image(mode.width//2,mode.height//2+30,image=ImageTk.PhotoImage(mode.splashScreen))
        canvas.create_text(mode.width-mode.margin,mode.height-20,text='Press anywhere to start',font='ariel 20',anchor = 'w')
##########################################################################################
class Evolution(ModalApp):
    def appStarted(app):
        app.simulateMode = Simulate()
        app.setUpMode = setUpMode()
        app.dataMode = dataMode()
        app.helpMode = HelpMode()
        app.invasiveSpeciesMode = invasiveSpeciesMode()
        app.splashScreenMode = splashScreenMode()
        app.setActiveMode(app.splashScreenMode)
Evolution(width=800, height=800)
    
