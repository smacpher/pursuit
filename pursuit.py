#using vectors for accel, vel, and pos
### EVENT BASED ANIMATION DESIGN TAKEN FROM CLASS NOTES ###
from tkinter import *
import random
import math
import cmath

#http://wp.stolaf.edu/it/installing-pil-pillow-cimage-on-windows-and-mac/ to install PIL
from PIL import ImageTk
from PIL import Image

#from rohan's socket demo
import socket
from _thread import * #allows us to launch another thread
from queue import Queue


class Game(object):

    #keeps track of number of games played
    #read and write files taken from course notes
    leaderBoardPath = "leaderBoard.txt"

    def readFile(self, path):
        with open(path, "rt") as f:
            return f.read()

    def writeFile(self, path, contents):
        with open(path, "wt") as f:
            f.write(contents)

    def getName(self):
        self.name = self.nameEntry.get()
        self.scoreRoot.quit()
        self.scoreRoot.destroy()

    def addScore(self):
        self.scoreRoot = Tk()
        self.nameEntry = Entry(self.scoreRoot)
        self.nameEntry.pack()
        self.nameEntry.focus_set()
        self.nameButton = Button(self.scoreRoot, text="Enter a name", command = self.getName)
        self.nameButton.pack()
        self.scoreRoot.mainloop()

        score = self.score
        path = self.leaderBoardPath
        prevContents = self.readFile(path)

        if self.name != None:
            self.writeFile(path, prevContents + self.name + "-" + str(score) + "*") #add space for easy access to splitting
        else: #didn't enter a name
            self.writeFile(path, prevContents + "anonymous" + "-" + str(score) + "*")

    def getLeaderBoard(self):
        path = self.leaderBoardPath
        contents = self.readFile(path)
        contents = contents.split("*")
        if '' in contents:
            contents.remove('')
        contents = set(contents) #get rid of duplicates
        contents = list(contents)
        if contents != []:
            for i in range(len(contents)):
                nameScore = contents[i].split("-")
                score = int(nameScore[1])
                contents[i] = (nameScore[0], score) #name, then score tuple
        contents = sorted(contents, key = lambda content: content[1]) #sorts by 
        return reversed(contents[-5:])

    def drawLeaderBoard(self, canvas):
        canvas.create_text(self.width/20, self.height/20, text="High Scores",
            fill="black", font="Helvetica 15 bold", anchor=W)
        i = 2
        for score in self.getLeaderBoard():
            canvas.create_text(self.width/20, i*self.height/20, 
                text="%d." % (i-1), fill="black", font="Helvetica 15", anchor=W)
            canvas.create_text(self.width/20 + 20, i*self.height/20, 
                text= "%s: %d" % (score[0], int(score[1])), fill="red", font="Helvetica 15", anchor=W)
            i+=1

    wallColors = ["black"]
    views = ["title", "play", "gameOver", "help", "settings", "multiplayer", "multiplayer prePlay"]
    settings = {"Wall Frequency": 5, "Start Level": 1, "Police Marker": False} #update for the settings page

    #wall Frequency range from 0 to 10
    def __init__(self):
        #2-d side scrolling 
        self.scrollX = 0
        self.scrollY = 0
        self.scrollMargin = 100
        self.totalSize = 2000

        self.scaling = 40
        #referring to window width and height
        self.windowFactor = 4
        self.width = self.totalSize/self.windowFactor
        self.height = self.totalSize/self.windowFactor

        #buttons
        self.buttonFill = "blue"
        self.titleButtonSize = self.width/10

        #settings
        self.settingsButtons = [Button1(40, 40, self.titleButtonSize, "Back",
                                      self),
                                IncrementButton(self.width/8, self.height/2, self.titleButtonSize/2, 
                                       "-", "Wall Frequency", self),
                                IncrementButton(2*self.width/8, self.height/2, self.titleButtonSize/2, 
                                       "+", "Wall Frequency", self),
                                IncrementButton(3*self.width/8, self.height/2, self.titleButtonSize/2, 
                                       "-", "Start Level", self),
                                IncrementButton(4*self.width/8, self.height/2, self.titleButtonSize/2, 
                                       "+", "Start Level", self),
                                Button1(6*self.width/8, self.height/2, self.titleButtonSize,
                                       "Police\nMarker", self)]

        self.policeMarker = self.settings["Police Marker"]
        #game play
        self.player = Player(self.width/2, self.height/2, self)
        self.policeCars = [PoliceAI2(0-20,self.height/2, 10, self)] #10 refers to max speed
        self.spawnPoints = [(0,0), (self.width/2, self.height/2), (self.width, self.height),
                      (self.width, 0), (0, self.height)] #spawn points at the center and the four corners
        self.level = self.settings["Start Level"]
        self.isPause = False
        #walls
        self.wallFrequency = 210 - 20*self.settings["Wall Frequency"] #grab from the settings dictionary; algorithm to make scale range form 1 to 10
        self.rows = 50
        self.cols = 50
        self.wallSize = 20
        self.wallGrid = self.make2dList()
        self.generateWalls()

        #key pressed/released
        self.pressedKeys = []
        self.score = 0
        self.counter = 0
        #mode dispatcher
        self.view = "title"
        #title stuff
        self.titleCounter = 0
        self.titlePlayer = Player(self.width/4, self.height/4, self)
        self.titlePlayer.AIInit()
        self.titlePolice = [PoliceAI2(3*self.width/4, self.height/4, 10, self)]
        self.titleButtons = [Button1(self.width/4, 3*self.height/5, self.titleButtonSize,
                                    "play", self),
                             Button1(2*self.width/4, 3*self.height/5, self.titleButtonSize,
                                    "settings", self),
                             Button1(3*self.width/4, 3*self.height/5, self.titleButtonSize,
                                    "help", self),
                             Button1(2*self.width/4, 4*self.height/5, 5*self.titleButtonSize/4,
                                    "multiplayer", self)]
        #help stuff
        self.helpButtons = [Button1(40, 40, self.titleButtonSize, "Back",
                                      self)]
        self.helpPlayer = Player(self.width/2+80, self.height/2+70, self)
        self.helpPressedKeys = []
        #spawn behind stuff
        self.advantage = 100
        self.advantageX = self.advantage
        self.advantageY = self.advantage

        #ui stuff
        self.titleColor = (100,223,105) #nice little green accent color lol
        self.playColor = (0,0,0)
        self.settingsColor = (0,128,255)
        self.helpColor = (0,128,255)
        self.multiplayerColor = (0,128,255)
        self.multiplayerPrePlayColor = (0,128,255)
        self.multiplayerPlayColor = (0,0,0)
        self.gameOverColor = self.playColor
        self.wallFile = "building.png"
        self.wallImage = None

        #multiplayer
        self.multiplayerButtons = [Button1(40, 40, self.titleButtonSize, "Back",
                                      self),
                                   Button1(1*self.width/4, self.height/2, 2*self.titleButtonSize,
                                    "Find Game", self),
                                   Button1(3*self.width/4, self.height/2, 2*self.titleButtonSize,
                                    "Create Game", self)]

        self.ip = socket.gethostbyname(socket.gethostname())#set the ip to return to the user
        self.host = None
        self.server = None
        self.backlog = 3 #max number of connections
        self.port = None
        self.timeout = 50 #set the time to look for a connection
        self.clientele = None
        self.port = 5039
        self.serverIsRunning = False #server initiated from server
        #multiplayer prePlay 
        self.multiplayerPrePlayButtons = [Button1(40, 40, self.titleButtonSize, "Back",
                                                self),
                                          Button1(self.width/2, self.height/2, 2*self.titleButtonSize, 
                                            "Multiplayer Play", self)]
        #multiplayerPlay
        self.msg = None
        self.multiplayerPlayCar = Player(self.width/2, self.height/2, self)
        self.multiplayerPlayOtherCar = Player(self.width/2, self.height/2, self)
        self.readyCount = 0 #for starting the game

        #entry buttons
        self.IPEntry = None
        self.IPButton = None
        self.tempRoot = None
        self.scoreRoot = None
        self.nameEntry = None
        self.nameButton = None
        self.name = None

    def loadWallImage(self):
        size = 2*self.wallSize #makes for better impact
        image = Image.open(self.wallFile) #open the image
        maxSize = (size, size) #max size for scaling
        image.thumbnail(maxSize, Image.ANTIALIAS) #resizing the image
        tkimage = ImageTk.PhotoImage(image)#making the image a pyimage
        self.wallImage = tkimage

    def rgbString(self, rgb):
        return "#%02x%02x%02x" % (rgb)

    def getCurrentBackground(self):
        if self.view == "title":
            return self.titleColor
        elif self.view == "play":
            return self.playColor
        elif self.view == "gameOver":
            return self.gameOverColor
        elif self.view == "help":
            return self.helpColor
        elif self.view == "multiplayerPlay":
            return self.multiplayerPlayColor

    ### Splashscreen stuff ###
    ### CONCEPT TAKEN FROM CLASS NOTES ###

    def keyPressed(self, event):
        if self.view == "title":
            self.titleKeyPressed(event)
        elif self.view == "gameOver":
            self.gameOverKeyPressed(event)
        elif self.view == "play":
            self.playKeyPressed(event)
        elif self.view == "help":
            self.helpKeyPressed(event)
        elif self.view == "settings":
            self.settingsKeyPressed(event)
        elif self.view == "multiplayer":
            self.multiplayerKeyPressed(event)
        elif self.view == "multiplayer prePlay":
            self.multiplayerPrePlayKeyPressed(event)
        elif self.view == "multiplayerPlay":
            self.multiplayerPlayKeyPressed(event)

    def keyReleased(self, event):
        if self.view == "title":
            self.titleKeyReleased(event)
        elif self.view == "gameOver":
            self.gameOverKeyReleased(event)
        elif self.view == "play":
            self.playKeyReleased(event)
        elif self.view == "help":
            self.helpKeyReleased(event)
        elif self.view == "settings":
            self.settingsKeyReleased(event)
        elif self.view == "multiplayer":
            self.multiplayerKeyReleased(event)
        elif self.view == "multiplayer prePlay":
            self.multiplayerPrePlayKeyReleased(event)
        elif self.view == "multiplayerPlay":
            self.multiplayerPlayKeyReleased(event)

    def mousePressed(self, event, canvas):
        if self.view == "title":
            self.titleMousePressed(event)
        elif self.view == "gameOver":
            self.gameOverMousePressed(event)
        elif self.view == "play":
            self.playMousePressed(event)
        elif self.view == "help":
            self.helpMousePressed(event)
        elif self.view == "settings":
            self.settingsMousePressed(event)
        elif self.view == "multiplayer":
            self.multiplayerMousePressed(event, canvas)
        elif self.view == "multiplayer prePlay":
            self.multiplayerPrePlayMousePressed(event)
        elif self.view == "multiplayerPlay":
            self.multiplayerPlayMousePressed(event)

    def timerFired(self):
        if self.view == "title":
            self.titleTimerFired()
        elif self.view == "gameOver":
            self.gameOverTimerFired()
        elif self.view == "play":
            self.playTimerFired()
        elif self.view == "help":
            self.helpTimerFired()
        elif self.view == "settings":
            self.settingsTimerFired()
        elif self.view == "multiplayer":
            self.multiplayerTimerFired()
        elif self.view == "multiplayer prePlay":
            self.multiplayerPrePlayTimerFired()
        elif self.view == "multiplayerPlay":
            self.multiplayerPlayTimerFired()

    def redrawAll(self, canvas):
        if self.view == "title":
            self.titleRedrawAll(canvas)
        elif self.view == "gameOver":
            self.gameOverRedrawAll(canvas)
        elif self.view == "play":
            self.playRedrawAll(canvas)
        elif self.view == "help":
            self.helpRedrawAll(canvas)
        elif self.view == "settings":
            self.settingsRedrawAll(canvas)
        elif self.view == "multiplayer":
            self.multiplayerRedrawAll(canvas)
        elif self.view == "multiplayer prePlay":
            self.multiplayerPrePlayRedrawAll(canvas)
        elif self.view == "multiplayerPlay":
            self.multiplayerPlayRedrawAll(canvas)

    ### MODES ###

    ### multiplayer ### Sockets taken from sockets demo with rohan
    #server 

    ### SERVER/SOCKETS STUFF ### from rohan's demo
    def runServer(self, host):
        self.host = host #getting local ip address 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server = self.server
        HOST = host
        BACKLOG = self.backlog
        server.settimeout(self.timeout) #setting the time to look for a connection
        server.bind((HOST,self.port)) 
        self.serverIsRunning = True 

        server.listen(BACKLOG)
        print("Looking for connection")

        self.clientele = []

        def handleClient(client, serverChannel):
            while True:
                msg = client.recv(100).decode("UTF-8")
                serverChannel.put(msg)

        def serverThread(clientele, serverChannel): #sends messages constantly to servers
            while True:
                msg = serverChannel.get(True, None)
                for client in self.clientele:
                    client.send(bytes(msg, "UTF-8")) #sending the message out

        serverChannel = Queue(100)

        start_new_thread(serverThread, (self.clientele, serverChannel)) 

        def lookForConnections():
            while True:
                client, address = server.accept() #keeps waiting until client connects
                print("Connection received")
                self.clientele.append(client)
                self.timeout = None
                server.settimeout(self.timeout)
                start_new_thread(handleClient, (client, serverChannel))
                print(self.clientele)
                if len(self.clientele) == self.backlog: #connected
                    _thread.exit()

        start_new_thread(lookForConnections, ())

    def joinServer(self, host):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        HOST = host
        PORT = self.port
        print("trying to connect")
        server.connect((HOST,PORT))
        self.server = server
        print("connected")
        self.view = "multiplayer prePlay"

        def handleServerMsg(server): #handles the messages from the host
            while True:
                self.msg = server.recv(100).decode("UTF-8")
                #do something with message to move car

        start_new_thread(handleServerMsg, (server, ))#start new thread to process controls from other player

    def multiplayerKeyPressed(self, event):
        pass

    def multiplayerKeyReleased(self, event):
        pass

    ###button and entry code taken from http://effbot.org/tkinterbook/entry.htm
    def callback(self):
        self.host = self.IPEntry.get()
        self.tempRoot.quit()

    def multiplayerMousePressed(self, event, canvas):
        x, y = event.x, event.y
        for button in self.multiplayerButtons:
            if button.isClicked(x, y):
                if button.Type == "Back":
                    if self.serverIsRunning:
                        self.server.close() #close the server if back is pressed
                    self.view = "title"
                elif button.Type == "Find Game":
                    if self.serverIsRunning:
                        HOST = socket.gethostbyname(socket.gethostname())
                        self.joinServer(HOST)
                    else: #HOST must be inputed manually
                        self.tempRoot = Tk()
                        self.IPEntry = Entry(self.tempRoot)
                        self.IPEntry.pack()
                        self.IPEntry.focus_set()
                        self.IPButton = Button(self.tempRoot, text="Input IP", command = self.callback)
                        self.IPButton.pack()
                        self.tempRoot.mainloop()
                        HOST = self.host
                    if HOST != None and type(HOST) == str:
                        try:
                            self.tempRoot.destroy()
                            self.joinServer(HOST) 
                        except:
                            canvas.create_text(self.width/4, 3*self.height/5, text="Input valid IP or Create Game")
                elif button.Type == "Create Game":
                    HOST = socket.gethostbyname(socket.gethostname())
                    self.runServer(HOST)#create it first, then join

    def multiplayerTimerFired(self):
        pass

    def drawIP(self, canvas):#draws the ip when server is run
        canvas.create_text(self.width/2, 1*self.height/4, text="Your IP %s" % self.ip)

    def drawMultiplayerTitle(self, canvas):
        canvas.create_text(self.width/2, 40, 
            text="Multiplayer", font="Helvetica 30")

    def drawMultiplayerBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.multiplayerColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def drawMultiplayerButtons(self, canvas):
        for button in self.multiplayerButtons:
            button.draw(canvas)

    def multiplayerRedrawAll(self, canvas):
        self.drawMultiplayerBackground(canvas)
        self.drawMultiplayerTitle(canvas)
        self.drawMultiplayerButtons(canvas)
        self.drawIP(canvas)

    ### multiplayer prePlay ###

    def multiplayerPrePlayKeyPressed(self, event):
        pass

    def multiplayerPrePlayKeyReleased(self, event):
        pass

    def multiplayerPrePlayMousePressed(self, event):
        x, y = event.x, event.y
        for button in self.multiplayerPrePlayButtons:
            if button.isClicked(x, y):
                if button.Type == "Back":
                    self.view = "title"
                if button.Type == "Multiplayer Play":
                    msg = "ready"
                    self.server.send(bytes(msg, "UTF-8"))#starts the clients together

    def multiplayerPrePlayTimerFired(self):
        if self.msg == "ready": #play game
            self.view = "multiplayerPlay"

    def drawMultiplayerPrePlayButtons(self, canvas):
        for button in self.multiplayerPrePlayButtons:
            button.draw(canvas)

    def drawMultiplayerPrePlayBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.multiplayerPrePlayColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def multiplayerPrePlayRedrawAll(self, canvas):
        self.drawMultiplayerPrePlayBackground(canvas)
        canvas.create_text(self.width/2, self.height/8, text="Connection succesful!")
        self.drawMultiplayerPrePlayButtons(canvas)
        self.drawIP(canvas)


    ### multiplayerPlay ###
## use clientPlayer and serverPlayer
    def multiplayerPlayKeyPressed(self, event):
        event = event.keysym
        if self.serverIsRunning: #on the server side
            if event == "a":
                msg = "serverPlayer a"
            elif event == "Right":
                msg = "serverPlayer r"
            elif event == "Left":
                msg = "serverPlayer l"
            elif event == "d":
                msg = "serverPlayer d"
        else: #on the client side
            if event == "a":
                msg = "clientPlayer a"
            elif event == "Right":
                msg = "clientPlayer r"
            elif event == "Left":
                msg = "clientPlayer l"
            elif event == "d":
                msg = "clientPlayer d"
        try:
            self.server.send(bytes(msg, "UTF-8"))
        except: #no message sent
            pass

    def multiplayerPlayKeyReleased(self, event):
        pass

    def multiplayerPlayMousePressed(self, event):
        pass

    def moveMultiplayerCars(self):
        yourCar = self.multiplayerPlayCar
        otherCar = self.multiplayerPlayOtherCar
        yourCar.turn()
        otherCar.turn()
        yourCar.move()
        otherCar.move()

    def multiplayerPlayTimerFired(self):
        #print("test")
        self.moveMultiplayerCars()
        yourCar = self.multiplayerPlayCar
        otherCar = self.multiplayerPlayOtherCar
        msg = self.msg

        ###move your car
        if msg == "serverPlayer a":
            yourCar.reverse = False
            yourCar.accel = True
        elif msg == "serverPlayer r":
            yourCar.left = False
            yourCar.right = True
        elif msg == "serverPlayer l":
            yourCar.right = False
            yourCar.left = True
        elif msg == "serverPlayer d":
            yourCar.accel = False
            yourCar.reverse = True

        ###move the other car
        if msg == "clientPlayer a":
            otherCar.reverse = False
            otherCar.accel = True
        elif msg == "clientPlayer r":
            otherCar.left = False
            otherCar.right = True
        elif msg == "clientPlayer l":
            otherCar.right = False
            otherCar.left = True
        elif msg == "clientPlayer d":
            otherCar.accel = False
            otherCar.reverse = True

    def drawMultiplayerCars(self, canvas):
        yourCar = self.multiplayerPlayCar
        otherCar = self.multiplayerPlayOtherCar
        yourCar.draw(canvas)
        otherCar.draw(canvas)

    def drawMultiplayerPlayBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.multiplayerPlayColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def multiplayerPlayRedrawAll(self, canvas):
        self.drawMultiplayerPlayBackground(canvas)
        self.drawMultiplayerCars(canvas)

    ### title ###
    def titleMousePressed(self, event):
        x, y = event.x, event.y
        for button in self.titleButtons:
            if button.isClicked(x, y):
                self.view = button.Type

    def titleKeyPressed(self, event):
        event = event.keysym

    def titleKeyReleased(self, event):
        pass

    def moveTitlePolice(self):
        for police in self.titlePolice:
            police.move()

    def moveTitlePlayerAI(self):
        player = self.titlePlayer
        player.moveAI()

    def titlePoliceFollowPlayer(self):
        player = self.titlePlayer
        policeCars = self.titlePolice
        for police in policeCars:
            police.pursuePlayer(player)

    def titleTimerFired(self):
        #load wall images
        if self.wallImage == None:
            self.loadWallImage()
        if self.titleCounter < 50:
            self.titleCounter += 1
        else: 
            self.titleCounter = 0

        self.moveTitlePlayerAI() 
        self.moveTitlePolice()
        self.titlePlayer.followPath()
        self.titlePoliceFollowPlayer()

    def drawTitle(self, canvas):
        canvas.create_text(self.width/2, self.height/2, text = "PURSUIT!",
                           fill = "black", font = "Helvetica 30 bold")

    def drawTitleBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.titleColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def drawTitlePolice(self, canvas):
        for police in self.titlePolice:
            police.draw(canvas)

    def drawTitleButtons(self, canvas):
        for button in self.titleButtons:
            button.draw(canvas)

    def titleRedrawAll(self, canvas):
        self.drawTitleBackground(canvas)
        self.drawTitleButtons(canvas)
        self.titlePlayer.draw(canvas)
        self.drawTitlePolice(canvas)
        self.drawTitle(canvas)
        self.drawLeaderBoard(canvas)
        
    ### settings ###

    def settingsKeyPressed(self, event):
        pass

    def settingsKeyReleased(self, event):
        pass

    def settingsMousePressed(self, event):
        x, y = event.x, event.y
        for button in self.settingsButtons:
            if button.isClicked(x, y):
                if button.Type == "Back":
                    self.view = "title"
                elif button.Type == "Police\nMarker":
                    self.policeMarker = not self.policeMarker
                elif type(button) == IncrementButton:
                    button.incrementAttribute()

    def settingsTimerFired(self):
        pass

    def drawSettingsButtons(self, canvas):
        for button in self.settingsButtons:
            button.draw(canvas)

    def drawLabels(self, canvas):
        for button in self.settingsButtons:
            if isinstance(button, IncrementButton) and button.Type == "+":#prevent double drawing
                canvas.create_text(button.x - self.width/16, button.y - 40, text="%s" % button.attribute)
                canvas.create_text(button.x - self.width/16, button.y, text="%d" % self.settings[button.attribute])
            elif button.Type == "Police\nMarker":
                if self.policeMarker == True:
                    status = "On"
                else: #false
                    status = "Off"
                canvas.create_text(button.x, button.y-button.size, 
                    text="%s" % status)

    def drawSettingsBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.settingsColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def drawSettingsTitle(self, canvas):
        canvas.create_text(self.width/2, 40, 
            text="Settings", font="Helvetica 30")

    def settingsRedrawAll(self, canvas):
        self.drawSettingsBackground(canvas)
        self.drawSettingsTitle(canvas)
        self.drawSettingsButtons(canvas)
        self.drawLabels(canvas)

    ### help ###

    def helpKeyPressed(self, event):
        event = event.keysym
        if event not in self.pressedKeys:
            self.helpPressedKeys.append(event)

    def helpKeyReleased(self, event):
        event = event.keysym
        if event in self.helpPressedKeys:
            self.helpPressedKeys.remove(event)

    def checkHelpKeys(self):
        pressedKeys = self.helpPressedKeys
        player = self.helpPlayer
        for event in pressedKeys:
            if event == "a":
                player.accel = True
            elif event == "d":
                player.reverse = True
            elif event == "Right":
                player.right = True
            elif event == "Left":
                player.left = True

    def helpMousePressed(self, event):
        x, y = event.x, event.y
        for button in self.helpButtons:
            if button.isClicked(x,y):
                if button.Type == "Back":
                    self.view = "title"

    def moveHelpPlayer(self):
        player = self.helpPlayer
        player.turn()
        player.helpMove() 

    def helpTimerFired(self):
        self.checkHelpKeys()
        self.moveHelpPlayer()
        self.helpPlayer.reset()

    def drawInstructions(self, canvas):
        canvas.create_text(self.width/2, 40, 
            text="Instructions", font="Helvetica 30")
        canvas.create_text(self.width/2, self.height/2, 
            text="""\
1. Avoid the cops
2. Avoid crashing into the buildings 
3. Run the cops into the walls to accumulate points
4. Survive for as long as possible!

Controls:
            a = accelerate 
            d = deccelerate/reverse
            rightArrow = turn right
            leftArrow = turn left

Practice driving the car around! -->
            """, font = "Helvetica 12 bold")

    def drawHelpBoundary(self, canvas):
        fill = "white"
        width = 2
        canvas.create_line(self.scrollMargin-self.player.width/2, self.scrollMargin-self.player.width/2, self.scrollMargin-self.player.width/2, 
            self.height-self.scrollMargin+self.player.width/2, fill=fill, width=width)
        canvas.create_line(self.scrollMargin-self.player.width/2, self.scrollMargin-self.player.width/2, 
            self.width-self.scrollMargin+self.player.width/2, self.scrollMargin-self.player.width/2, fill=fill, width=width)
        canvas.create_line(self.width-self.scrollMargin+self.player.width/2, self.scrollMargin-self.player.width/2, self.width-self.scrollMargin+self.player.width/2, 
            self.height-self.scrollMargin+self.player.width/2, fill=fill, width=width)
        canvas.create_line(self.width-self.scrollMargin+self.player.width/2, self.height-self.scrollMargin+self.player.width/2, self.scrollMargin-self.player.width/2, 
            self.height-self.scrollMargin+self.player.width/2, fill=fill, width=width)

    def drawHelpPlayer(self, canvas):
        player = self.helpPlayer
        player.draw(canvas)

    def drawHelpButtons(self, canvas):
        for button in self.helpButtons:
            button.draw(canvas)

    def drawHelpBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.helpColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def helpRedrawAll(self, canvas):
        self.drawHelpBackground(canvas)
        self.drawHelpPlayer(canvas)
        self.drawHelpBoundary(canvas)
        self.drawHelpButtons(canvas)
        self.drawInstructions(canvas)

    ### gameOver ###

    def drawGameOver(self, canvas):
        canvas.create_text(self.width/2, 3*self.height/8,
                            text = "You were caught!", fill="red",
                            font = "Helvetica 20")
        canvas.create_text(self.width/2, 5*self.height/8,
                            text = "Press r to return to title", fill="red",
                            font = "Helvetica 15")

    def gameOverMousePressed(self, event):
        pass

    def gameOverKeyPressed(self, event):
        event = event.keysym
        if event == "r":
            self.view = "play"
            self.__init__() ## reset game

    def gameOverKeyReleased(self, event):
        pass
        
    def gameOverTimerFired(self):
        pass

    def drawGameOverBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.gameOverColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def gameOverRedrawAll(self, canvas):
        self.drawGameOverBackground(canvas)
        self.drawPlayer(canvas)
        self.drawPolice(canvas)
        self.drawEnvironment(canvas)
        self.drawGameOver(canvas)

    ### play ###
    def policeFollowPlayer(self):
        player = self.player
        policeCars = self.policeCars
        for police in policeCars:
            police.pursuePlayer(player)

    def spawnPolice(self):
        if self.counter == 0:
            coords = self.spawnPoints
            for i in range(self.level):
                index = random.randint(0, len(coords)-1)
                (x, y) = coords[index]
                maxSpeed = random.randint(8, 10+i)
                newPolice = PoliceAI2(x, y, maxSpeed, self)
                self.policeCars.append(newPolice)
            if self.level >= 3:
                self.spawnPoliceBehind()

    def spawnPoliceBehind(self):
        player = self.player
        if math.cos(player.direction) >= 0: #moving right
            x = player.x - self.advantage
        else:
            x = player.x + self.advantage
        if math.sin(player.direction) >= 0:
            y = player.y - self.advantage
        else:
            y = player.y + self.advantage
        xOffset = random.randint(-10,10)#so player can't hide behind walls
        yOffset = random.randint(-10,10)

        maxSpeed = random.randint(10, 15)
        newPolice = PoliceAI2(x+xOffset, y+yOffset, maxSpeed, self)
        self.policeCars.append(newPolice)

    def playMousePressed(self, event):
        pass

    def movePlayer(self):
        self.player.turn()
        self.player.move() 

    def movePolice(self):
        for police in self.policeCars:
            if police.isLegalMove():
                police.move()
            else:
                self.policeCars.remove(police)
                self.score += 1
    
    def playKeyPressed(self, event):
        event = event.keysym
        if self.isPause == True:
            if event == "r":
                self.__init__()
                self.view = "title"
            if event == "p":
                self.isPause = not self.isPause
        else:
            if event == "p":
                self.pause()
            if event not in self.pressedKeys:
                self.pressedKeys.append(event)

    ## taken from misc
    def playKeyReleased(self, event):
        event = event.keysym
        if event in self.pressedKeys:
            self.pressedKeys.remove(event)

    def checkKeys(self):
        pressedKeys = self.pressedKeys
        for event in pressedKeys:
            if event == "a":
                self.player.accel = True
            elif event == "d":
                self.player.reverse = True
            elif event == "Right":
                self.player.right = True
            elif event == "Left":
                self.player.left = True

    ## FORMAT TAKEN FROM CLASS NOTES ##
    def make2dList(self):
        grid = []
        rows, cols = self.rows, self.cols
        for row in range(rows): grid += [[None] * cols]
        return grid

    # TAKEN FROM CLASS NOTES #
    def getWallBounds(self, row, col): #finds the top-left and bottom-right of cell
        gridWidth  = self.totalSize
        gridHeight = self.totalSize
        x0 = gridWidth * col / self.cols
        x1 = x0 + self.wallSize
        y0 = gridHeight * row / self.rows
        y1 = y0 + self.wallSize
        return (x0, y0, x1, y1)

    def generateWalls(self):
        for row in range(-len(self.wallGrid)//2, len(self.wallGrid)//2):
            for col in range(-len(self.wallGrid[0])//2, len(self.wallGrid)//2):
                chance = random.randint(1,self.wallFrequency)
                if chance == 1:
                    (x0, y0, x1, y1) = self.getWallBounds(row, col)
                    colorIndex = random.randint(0,len(self.wallColors)-1)
                    fill = self.wallColors[colorIndex]
                    if ((abs(x0 + (x1-x0) - self.player.x)**2 + 
                        abs(y0 + (y1-y0) - self.player.y)**2) > self.wallSize**2): 
                        self.wallGrid[row][col] = Wall(x0, y0, fill, self)

# collisions http://gamedevelopment.tutsplus.com/tutorials/how-to-create-a-custom-2d-physics-engine-the-basics-and-impulse-resolution--gamedev-6331
    def checkHits(self):
        for car in self.policeCars:
            if self.player.isHit(car):
                self.view = "gameOver"
                self.addScore()

    def updateLevel(self):
        self.level = self.settings["Start Level"] + self.score//5

    def pause(self):
        self.isPause = not self.isPause

    def playTimerFired(self):
        if self.isPause == True: #skip timer fired functions
            pass
        else:
            if self.counter > 0: #police spawn counter
                self.counter -= 1
            else:
                self.counter = 50

            self.checkKeys() #checks which keys are pressed
            #increase the time on screen
            self.movePlayer() #increments dt
            self.movePolice()
            self.policeFollowPlayer()
            self.spawnPolice()
            self.checkHits()
            self.updateLevel()
            self.player.reset()

########## DRAW FUNCTIONS ###########
    def drawWalls(self, canvas):
        for row in range(len(self.wallGrid)):
            for col in range(len(self.wallGrid[0])):
                if self.wallGrid[row][col] != None:
                    self.wallGrid[row][col].draw(canvas)

    def drawPolice(self, canvas):
        (sx, sy) = (self.scrollX, self.scrollY)
        for car in self.policeCars:
            if (car.x - car.width/2 <= self.width+sx and car.x + car.width/2 >= sx and
                car.y - car.height/2 <= self.height+sy and car.y + car.height/2 >= sy):
                car.draw(canvas) 

    def drawPlayer(self, canvas):
        self.player.draw(canvas)

    def drawEnvironment(self, canvas):
        sx = self.scrollX
        sy = self.scrollY
        circSize = 5
        for point in self.spawnPoints:
            (x, y) = point
            canvas.create_oval(x-circSize-sx, y-circSize-sy, x+circSize-sx, y+circSize-sy, fill="white")
        self.drawWalls(canvas)

    def drawScore(self, canvas):#score and police spawn counter
        canvas.create_text(self.scrollMargin/2, self.scrollMargin/2, 
                           text="SCORE: %d" % self.score, fill="red")
        canvas.create_text(self.width-self.scrollMargin/2, self.scrollMargin/2 + 20,
                           text="Next police spawn in %d" % self.counter, fill="blue",
                           anchor=E)
        canvas.create_text(self.scrollMargin/2, self.scrollMargin/2+20,
                           text="Level %d" % self.level, fill="purple")
        canvas.create_text(self.width-self.scrollMargin/2, self.scrollMargin/2,
                           text="Cops currently in Pursuit: %d" % len(self.policeCars), fill="green",
                           anchor=E)
        canvas.create_text(self.scrollMargin/1.5, self.height-self.scrollMargin/2+20,
                           text="Press p to pause", fill="orange")

    def drawBoundary(self, canvas):
        sx = self.scrollX
        sy = self.scrollY
        fill = "white"
        width = 5
        canvas.create_line(-self.totalSize/2-sx,-self.totalSize/2-sy,
                           -self.totalSize/2-sx,self.totalSize/2-sy, 
                           fill=fill, width=width)
        canvas.create_line(-self.totalSize/2-sx,-self.totalSize/2-sy,
                           self.totalSize/2-sx,-self.totalSize/2-sy, 
                           fill=fill, width=width)
        canvas.create_line(-self.totalSize/2-sx, self.totalSize/2-sy,
                           self.totalSize/2-sx,self.totalSize/2-sy, 
                           fill=fill, width=width)
        canvas.create_line(self.totalSize/2-sx,-self.totalSize/2-sy,
                           self.totalSize/2-sx,self.totalSize/2-sy, 
                           fill=fill, width=width)

    def drawPlayBackground(self, canvas):
        width = self.width
        height = self.height
        fill = self.rgbString(self.playColor)
        canvas.create_rectangle(0,0,width,height,fill=fill)

    def drawPause(self, canvas):
        canvas.create_text(self.width/2, self.height/2, text="Pause", font="Helvetica 30", fill="white")
        canvas.create_text(self.width/2, self.height/2 + 40, 
            text="Press r to return to title", font="Helvetica 20",fill="white")

    def playRedrawAll(self, canvas):
        self.drawPlayBackground(canvas)
        self.drawPlayer(canvas)
        self.drawPolice(canvas)
        self.drawBoundary(canvas)
        self.drawEnvironment(canvas)
        self.drawScore(canvas)
        if self.isPause == True:
            self.drawPause(canvas)

    ### RUN FUNCTION ###
    ### taken from course notes ###
    def run(self):
        def redrawAllWrapper(canvas):
            canvas.delete(ALL)
            self.redrawAll(canvas)
            canvas.update()    

        def mousePressedWrapper(event, canvas):
            self.mousePressed(event, canvas)
            redrawAllWrapper(canvas)

        def keyPressedWrapper(event, canvas):
            self.keyPressed(event)
            redrawAllWrapper(canvas)

        def keyReleasedWrapper(event, canvas):
            self.keyReleased(event)
            redrawAllWrapper(canvas)

        def timerFiredWrapper(canvas):
            self.timerFired()
            redrawAllWrapper(canvas)
            # pause, then call timerFired again
            canvas.after(self.timerDelay, timerFiredWrapper, canvas)
        self.timerDelay = 100 # milliseconds
        # create the root and the canvas
        root = Tk()
        #http://stackoverflow.com/questions/21958534/setting-the-window-to-a-fixed-size-with-tkinter
        root.resizable(width=False, height=False)#don't allow for resizing
        canvas = Canvas(root, width=self.width, height=self.height) #background="OliveDrab1")
        canvas.pack()
        self.root = root
        #images
        #http://tkinter.unpythonic.net/wiki/PhotoImage

        # set up events
        root.bind("<Button-1>", lambda event:
                                mousePressedWrapper(event, canvas))
        root.bind("<Key>", lambda event:
                                keyPressedWrapper(event, canvas))
        root.bind("<KeyRelease>", lambda event:
                                keyReleasedWrapper(event, canvas))
        timerFiredWrapper(canvas)
        # and launch the app
        root.mainloop()  # blocks until window is closed
        print("bye!")

###turning physics concepts taken from http://cecilsunkure.blogspot.com/2012/02/basic-2d-vector-physics.html and https://www.youtube.com/watch?v=0arhoq4qh6g
###reset concept taken from the same place
###incorporated multiple key presses which is from the course notes
class Car(object):

    def __init__(self, x, y, game):
        self.game = game
        self.x = x 
        self.y = y 
        
    def updateHeightAndWidth(self):
        image = Image.open(self.file) #open the image
        maxSize = (self.game.scaling, self.game.scaling) #max size for scaling
        image.thumbnail(maxSize, Image.ANTIALIAS) #resizing the image
        self.width = image.width
        self.height = image.height

    ##image stuff taken from http://effbot.org/tkinterbook/photoimage.htm
    ##http://stackoverflow.com/questions/5252170/specify-image-filling-color-when-rotating-in-python-with-pil-and-setting-expand
    def drawImage(self, canvas):
        sx = self.game.scrollX
        sy = self.game.scrollY
        #initialize the image
        angle = self.direction * 360/(2*math.pi)
        image = Image.open(self.file) #open the image
        maxSize = (self.game.scaling, self.game.scaling) #max size for scaling
        image.thumbnail(maxSize, Image.ANTIALIAS) #resizing the image
        image = image.convert('RGBA')
        image = image.rotate(-angle, expand=True) #rotating the image based on direction

        #transparent background
        if self.game.policeMarker == True:
            if isinstance(self, PoliceAI1) or isinstance(self, PoliceAI2):
                if self.game.view == "title":
                    counter = self.game.titleCounter
                elif self.game.view == "play":
                    counter = self.game.counter
                elif self.game.view == "gameOver":
                    counter = self.game.counter

                if counter % 2 == 0:
                    (r,g,b) = (0,0,255)
                else:
                    (r,g,b) = (255,0,0)
            elif isinstance(self, Player):
                self.rgb = self.game.getCurrentBackground()
                (r,g,b) = self.rgb
        else: #no police marker or player car
            self.rgb = self.game.getCurrentBackground()
            (r,g,b) = self.rgb

        intensity = 255
        fff = Image.new('RGBA', image.size, (r,g,b,intensity))
        out = Image.composite(image, fff, image)

        tkimage = ImageTk.PhotoImage(out)#making the image a pyimage
        self.image = tkimage
        #canvas.create_text(self.x, self.y, text ="12")
        canvas.create_image(self.x-sx, self.y-sy, anchor=CENTER, image=self.image)

    ### FORMAT TAKEN FROM CLASS NOTES ###
    def getCarBounds(self): #unrotated
        x0 = self.x-self.width/2
        y0 = self.y-self.height/2
        x1 = self.x+self.width/2
        y1 = self.y+self.height/2
        return (x0, y0, x1, y1)

    def getComplexCarCoords(self): #accounts for rotation without scroll
        complexAngle = cmath.exp(self.direction*1j)
        center = complex(self.x, self.y)
        (x0, y0, x1, y1) = self.getCarBounds() 
        coords = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for i in range(len(coords)):
            x, y = coords[i][0], coords[i][1]
            v = complexAngle*(complex(x, y) - center) + center
            coords[i] = (v.real, v.imag)
        return coords

    def applyScroll(self, coords):
        sx = self.game.scrollX
        sy = self.game.scrollY
        complexScroll = complex(sx, sy)
        for i in range(len(coords)):
            (x, y) = (coords[i][0], coords[i][1])
            x-=complexScroll.real
            y-=complexScroll.imag
            coords[i] = (x, y)
        return coords

    def draw(self, canvas):
        coords = self.getComplexCarCoords()
        coords = self.applyScroll(coords)
        if isinstance(self, Player):
            fill = self.color
        elif isinstance(self, PoliceAI2) or isinstance(self, PoliceAI1): #flashing
            if self.game.view == "title":
                counter = self.game.titleCounter
            elif self.game.view == "play":
                counter = self.game.counter
            elif self.game.view == "gameOver":
                counter = self.game.counter
            if counter % 2 == 0:
                fill = self.color
            else:
                fill = self.color2
            sx = self.game.scrollX
            sy = self.game.scrollY
            root2 = 2**0.5
            if self.game.policeMarker == True:
                canvas.create_oval(self.x-root2*self.width/1.89-sx, self.y-root2*self.width/1.89-sy, 
                                   self.x+root2*self.width/1.89-sx, self.y+root2*self.width/1.89-sy, fill=fill, width=0) #1.89 to hide corners
        #canvas.create_polygon(coords, fill = fill)
        
        self.drawImage(canvas)

    #hit by car
    ###concept taken from class notes for all isHit/getBounds methods
    def isHit(self, other):
        (x0, y0, x1, y1) = self.getCarBounds()
        if isinstance(other, Wall):
            (xx0, yy0, xx1, yy1) = other.getWallBounds()
        elif isinstance(other, Car):
            (xx0, yy0, xx1, yy1) = other.getCarBounds()
        if (x1 > xx0 and xx1 > x0 and y1 > yy0 and yy1 > y0):
            return True
        else:
            return False

    def turn(self):
        self.prevDirection = self.direction
        if self.direction > 2*math.pi:
            self.direction = 0
        elif self.direction < 0:
            self.direction = 2*math.pi
        if self.left == True:
            self.direction -= self.rotationSpeed * self.currSpeed
        if self.right == True:
            self.direction += self.rotationSpeed * self.currSpeed
        if self.direction != self.prevDirection: #made a turn
            self.updatePath()

    def move(self): #updates position based on vx, vy (constantly called by timer fired)
        
        #udpate speed
        if self.accel == True:
            if self.currSpeed < self.maxSpeed and self.isLegalMove():
                self.currSpeed += self.acceleration
        elif self.reverse == True and abs(self.currSpeed) < self.maxSpeed:
            self.currSpeed -= self.acceleration
        else:
            if self.currSpeed > 0:
                self.currSpeed -= self.friction
        #update position
        if self.game.view == "play" and not self.isLegalMove():
            self.currSpeed = 0
        else:
            self.x += self.currSpeed * math.cos(self.direction)
            self.y += self.currSpeed * math.sin(self.direction)
        
    def isLegalMove(self):
        for row in range(len(self.game.wallGrid)):
            for col in range(len(self.game.wallGrid[0])):
                wall = self.game.wallGrid[row][col]
                (x0, y0, x1, y1) = self.getCarBounds()
                if wall != None:
                    if (x1 + self.currSpeed * math.cos(self.direction) >= wall.x-wall.size/2 and
                        x0 + self.currSpeed * math.cos(self.direction) <= wall.x+wall.size/2 and
                        y1 + self.currSpeed * math.sin(self.direction) >= wall.y-wall.size/2 and
                        y0 + self.currSpeed * math.sin(self.direction) <= wall.y+wall.size/2):
                        return False
        return True

    def reset(self):
        self.accel = False
        self.reverse = False
        self.right = False
        self.left = False

### GAME OBJECTS ###

class Player(Car):

    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        #image from http://www.clker.com/cliparts/G/h/8/0/n/S/red-car-top-view-md.png
        self.file = "playerCar1.ppm"
        self.image = None

        #physical attributes
        self.width =  None
        self.height = None
        self.color = "grey"
        
        #updates height and width based on image size
        self.updateHeightAndWidth()
        #turning and speed stuff
        self.prevDirection = None
        self.direction = 0 #start at 0 radians (range of -pi to pi)
        self.acceleration = 0.4 #cars preset acceleration
        self.friction = 0.1
        self.currSpeed = 0
        self.rotationSpeed = 2*math.pi/270
        self.maxSpeed = 20

        #direction stuff
        self.accel = False
        self.reverse = False
        self.left = False
        self.right = False
        
        #player path
        self.path = [(self.x, self.y)] 
        

    def updatePath(self):
        x, y = self.x, self.y #point where the turn is made
        turnAngle = self.direction + (self.direction - self.prevDirection)
        self.path.append((x,y))

    def move(self):
        super().move()
        ## scroll
        if self.game.view != "multiplayerPlay":
            ###side scroller concept taken from class notes
            if (self.x < self.game.scrollX + self.game.scrollMargin):
                self.game.scrollX = self.x - self.game.scrollMargin
            if (self.x > self.game.scrollX + self.game.width - self.game.scrollMargin):
                self.game.scrollX = self.x - self.game.width + self.game.scrollMargin
            if (self.y < self.game.scrollY + self.game.scrollMargin):
                self.game.scrollY = self.y - self.game.scrollMargin
            if (self.y > self.game.scrollY + self.game.width - self.game.scrollMargin):
                self.game.scrollY = self.y - self.game.width + self.game.scrollMargin

        ##bounds
        self.vx = math.cos(self.direction) * self.currSpeed
        self.vy = math.cos(self.direction) * self.currSpeed

        if self.game.view == "multiplayerPlay": #no scroll yet

            if (self.x + self.width/2 +  self.vx > self.game.width):
                self.x = self.game.width - self.width/2
            if (self.x - self.width/2 - self.vx < 0 ):
                self.x = 0 + self.width/2
            if (self.y + self.height/2 + self.vy > self.game.height):
                self.y = self.game.height - self.height/2
            if (self.y - self.height/2 - self.vy < 0 ):
                self.y = 0 + self.height/2

        else:#with scrolling

            if (self.x + self.width/2 +  self.vx> self.game.totalSize/2):
                self.x = self.game.totalSize/2 - self.width/2
            if (self.x - self.width/2 - self.vx < 0 - self.game.totalSize/2):
                self.x = -self.game.totalSize/2 + self.width/2
            if (self.y + self.height/2 + self.vy > self.game.totalSize/2):
                self.y = self.game.totalSize/2 - self.height/2
            if (self.y - self.height/2 - self.vy < 0 - self.game.totalSize/2):
                self.y = -self.game.totalSize/2 + self.height/2
        
    def helpMove(self):
        super().move()
        ##bounds
        self.vx = math.cos(self.direction) * self.currSpeed
        self.vy = math.cos(self.direction) * self.currSpeed

        if (self.x + self.vx > self.game.width-self.game.scrollMargin):
            self.x = self.game.width-self.game.scrollMargin
        if (self.x - self.vx < self.game.scrollMargin):
            self.x = self.game.scrollMargin
        if (self.y + self.vy > self.game.height-self.game.scrollMargin):
            self.y = self.game.height-self.game.scrollMargin
        if (self.y - self.vy < self.game.scrollMargin):
            self.y = self.game.scrollMargin

    ###PLAYER AI STUFF###

    def AIInit(self):
        game = self.game
        self.accel = True #always moving
        self.path += ((game.width/4, game.height-game.height/4),
                         (game.width-game.width/4, game.height-game.height/4),
                         (game.width-game.width/4, game.height/4))

    def moveAI(self):
        if self.accel == True:
            if self.currSpeed < self.maxSpeed:
                self.currSpeed += self.acceleration
        else:
            if self.currSpeed > 0:
                self.currSpeed -= self.friction

    def getDirToPoint(self, x, y):
        (cx, cy) = (x, y)
        (px, py) = (self.x, self.y)
        (dx, dy) = (cx-px, cy-py)
        return (dx, dy)

    def deccelerate(self):
        self.currSpeed -= self.friction 

    def contains(self, point):
        (x, y) = point
        (x0, y0, x1, y1) = self.getCarBounds()
        if x >= x0 and x <= x1 and y >= y0 and y <= y1:
            return True
        else:
            return False

    def followPath(self):
        self.x += math.cos(self.direction) * self.currSpeed
        self.y += math.sin(self.direction) * self.currSpeed
        path = self.path
        if len(path) > 0:
            (x, y) = path[0]
            (dx, dy) = self.getDirToPoint(x, y)
            self.direction = math.atan2(dy, dx)
            if self.contains(path[0]): #reached that point (makes turn)
                self.path = self.path[1:] + [self.path[0]]
                self.deccelerate() #simulated turning friction

    def __repr__(self):
        return "%s at x:%d, y:%d" % (type(self), self.x, self.y)

class PoliceAI1(Car):

    def __init__(self, x, y, game):
        super().__init__(x, y, game)
        self.color = "blue"
        self.color2 = "red"
        self.width = self.game.scaling
        self.height = self.game.scaling
        self.maxSpeed = 10
        self.currSpeed = 0
        self.accel = 1
        self.direction = math.pi
        self.accel = True
        self.acceleration = 0.4
        self.decceleration = 0.2
        #image from http://www.clker.com/cliparts/4/2/n/E/D/M/p-car-top-view-md.png
        self.file = "policeCar.ppm"
        self.image = None

    def getDirToPlayer(self, x, y):
        (cx, cy) = (self.x, self.y)
        (px, py) = (x, y)
        (dx, dy) = (px-cx, py-cy)
        return (dx, dy)

    def move(self): #updates position based on vx, vy (constantly called by timer fired)
        #udpate speed
        if self.accel == True:
            if self.currSpeed < self.maxSpeed:
                self.currSpeed += self.acceleration
        else:
            if self.currSpeed > 0:
                self.currSpeed -= self.friction

    def deccelerate(self):
        self.currSpeed -= self.decceleration  

    def contains(self, point):
        (x, y) = point
        (x0, y0, x1, y1) = self.getCarBounds()
        if x >= x0 and x <= x1 and y >= y0 and y <= y1:
            return True
        else:
            return False

    def turn(self, Dir):
        
        if self.direction > 2*math.pi:
            self.direction = 0
        elif self.direction < 0:
            self.direction = 2*math.pi
        if Dir == "Left":
            self.direction -= self.rotationSpeed * self.currSpeed
        if Dir == "Right":
            self.direction += self.rotationSpeed * self.currSpeed

    def pursuePlayer(self, player):

        path = player.path
        #move police
        self.x += math.cos(self.direction) * self.currSpeed
        self.y += math.sin(self.direction) * self.currSpeed

        if len(path) > 0:
            (x, y) = path[0]
            (dx, dy) = self.getDirToPlayer(x, y)
            self.direction = math.atan2(dy, dx)
            if self.contains(path[0]): #reached that point
                player.path = path[1:]
                self.deccelerate() #simulated turning friction

class PoliceAI2(Car):

    def __init__(self, x, y, maxSpeed, game):
        self.game = game
        self.width = self.game.scaling
        self.height = self.game.scaling
        self.x = x
        self.y = y
        self.color = "blue"
        self.color2 = "red"
        self.direction = math.pi
        self.currSpeed = 0
        self.maxSpeed = maxSpeed
        self.accel = True
        self.acceleration = 0.4
        self.decceleration = 0.2
        #image from http://www.clker.com/cliparts/4/2/n/E/D/M/p-car-top-view-md.png
        self.file = "policeCar.ppm"
        self.image = None

    def getDirToPlayer(self, player):
        (cx, cy) = (self.x, self.y)
        (px, py) = (player.x, player.y)
        (dx, dy) = (px-cx, py-cy)
        return (dx, dy)

    def pursuePlayer(self, player):
        (dx, dy) = self.getDirToPlayer(player)
        self.direction = math.atan2(dy, dx)

    def move(self):
        if self.accel == True:
            if self.currSpeed < self.maxSpeed:
                self.currSpeed += self.acceleration
        else:
            if self.currSpeed > 0:
                self.currSpeed -= self.friction

        self.x += math.cos(self.direction) * self.currSpeed
        self.y += math.sin(self.direction) * self.currSpeed

class Wall(object):

    def __init__(self, x, y, fill, game):
        self.x = x
        self.y = y
        self.game = game
        self.fill = fill
        self.size = self.game.wallSize
        #http://pixlwalkr.com/2013/08/04/top-view-building/ for image

    def drawImage(self, canvas):
        sx = self.game.scrollX
        sy = self.game.scrollY
        #canvas.create_text(self.x, self.y, text ="12")
        canvas.create_image(self.x-sx, self.y-sy, anchor=CENTER, image=self.game.wallImage)

    def draw(self, canvas):
        
        sx = self.game.scrollX
        sy = self.game.scrollY
        (x0, y0, x1, y1) = self.getWallBounds()
        #canvas.create_rectangle(x0-sx, y0-sy, x1-sx, y1-sy, fill=self.fill)

        self.drawImage(canvas)

    ### FORMAT TAKEN FROM CLASS NOTES ###
    def getWallBounds(self):
        #did not divide size by two because it helps the impact engine #
        size = self.size
        x0 = self.x-size
        y0 = self.y-size
        x1 = self.x+size
        y1 = self.y+size
        return (x0, y0, x1, y1)

class Button1(object):

    def __init__(self, x, y, size, Type, game):
        self.game = game
        self.x = x
        self.y = y
        self.size = size
        self.fill = self.game.buttonFill
        self.Type = Type #string with the button's type

    def getButtonBounds(self):
        x0 = self.x-self.size/2
        y0 = self.y-self.size/2
        x1 = self.x+self.size/2
        y1 = self.y+self.size/2
        return (x0, y0, x1, y1)

    def isClicked(self, mouseX, mouseY):
        (x, y) = (mouseX, mouseY)
        (x0, y0, x1, y1) = self.getButtonBounds()
        if x >= x0 and x <= x1 and y >= y0 and y <= y1:
            return True
        else:
            return False

    def draw(self, canvas):
        size = self.size
        fill = self.fill
        (r, g, b) = self.game.titleColor
        rgb = self.game.rgbString((r,g,b))
        canvas.create_rectangle(self.x-size/2, self.y-size/2, self.x+size/2,
                                self.y+size/2, fill=rgb, width=5)
        canvas.create_text(self.x, self.y, text="%s" % self.Type, font="Helvetica 12", activefill=fill)

class IncrementButton(Button1):

    def __init__(self, x, y, size, Type, attribute, game):
        super().__init__(x, y, size, Type, game)
        self.attribute = attribute

    def incrementAttribute(self):
        if self.attribute == "Wall Frequency": #unique ranges
            if (self.game.settings[self.attribute]<10): 
                if self.Type == "+":
                    self.game.settings[self.attribute] += 1
            if (self.game.settings[self.attribute]>0):
                if self.Type == "-":
                    self.game.settings[self.attribute] -= 1

        elif self.attribute == "Start Level":
            if (self.game.settings[self.attribute]<10):
                if self.Type == "+":
                    self.game.settings[self.attribute] += 1
            if (self.game.settings[self.attribute]>1):
                if self.Type == "-":
                    self.game.settings[self.attribute] -= 1


if __name__ == '__main__':
    game = Game()
    game.run()
