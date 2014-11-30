import copy

# For this experiment, the world will be defined as a simple tile map with
# the map laid out as below:
#
#    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6
#    -----------         -------------
# 0 |. . . . . .|-------|. . . .|. . .|
# 1 |. . R . . . . . . .|. . . X|. . Q|
# 2 |. . . . . . . . . V|. . . .C. . .|
# 3 |. . . . . . . . . .D. . . .|X . B|
# 4 |. A . . . . . . . .|V . . .|. S S|
# 5 |. . . . . .|-------|. . . .|. S S|
#    -----------         -------------
#
#       ROOM1             ROOM2  ROOM3
#
#    | - VERTICAL WALL (edge)
#    - - HORIZONTAL WALL (edge)
#    . - OPEN FLOOR (node)
#    A - AGENT (game entity)
#    R - RED ACCESS CARD (game object)
#    V - ACTIVATOR (DOOR) (game object)
#    D - DOOR (ANY ACCESS) (edge)
#    X - ACTIVATOR (RED ACCESS DOOR) (game object)
#    C - DOOR (RED ACCESS) (edge)
#    Q - ACTIVATOR (SHUTTLE POWER) (game object)
#    B - ACTIVATOR (SHUTTLE) (game object)
#    S - SHUTTLE (node)
#
# The agent (A) is on the left.  Their goal is to
# take off in the shuttle.  The ideal sequence
# of actions is:
#
# 1. Goto Red Access Card (R)
# 2. Pick up Red Access Card
# 3. Goto Door Activator (V)
# 4. Use Door Activator (V)
# 5. Goto Door (D) (NOTE:  Nodes Left/Right)
# 6. Go Through Door (D)
# 7. Goto Door Activator (X)
# 8. Use Door Activator (X)
# 9. Goto Door (C) (NOTE: Nodes Left/Right)
# 10. Goto Shuttle Power Activator (Q)
# 11. Use Shuttle Power Activator (Q)
# 12. Goto Shuttle Activator (B)
# 13. Use Shuttle Activator (B)
#
# If we just break this down as three rooms and make the "goto" an
# implicit operation, we get the following sequence:
#
# 1. Pick Up (R) in ROOM 1
# 2. Use Door Activator (V) in ROOM 1
# 3. Go Through Door (D) in ROOM 1
# 4. Use Door Activator (X) in ROOM 2
# 5. Go Through Door (C) in ROOM 2
# 6. Use Shuttle Power Activator in ROOM 3
# 7. Use Shuttle Activator in ROOM 3

# These key strings define the keys for information in the simulation.
kInRoom = "In Room"                     # Integer room number
kIsPowered = "Is Powered"               # Boolean
kIsClosed = "Is Closed"                 # Boolean
kIsActivated = "Is Activated"           # Boolean
kHasRedAccess = "Has Red Access"        # Boolean
kRoomPortal = "Room Portal"             # Tuple of two rooms
kActivatorTarget = "Activator Target"   # Subject ID of a target
kSubjectType = "Subject Type"           # What kind of "thing" is this?
kIsBeingCarried = "Is Carried By"       # Something that was picked up (game object perspective)
kIsCarrying = "Is Carrying"             # List of subject IDs
kAction = "Action"                      # List of actionIDs

# These keys define the different types of game objects that exist.
goDoor = "Access Door"
goDoorAct = "Access Door Activator"
goRedDoor = "Red Access Door"
goRedDoorAct = "Red Access Door Activator"
goRedDoorKey = "Red Access Door Key"
goShuttleGen = "Shuttle Generator"
goShuttleAct = "Shuttle Launch Activator"
goAgent = "Agent"

# These keys define the different game actions that may be performed
gaGoThroughDoor = "Go Through Door"
gaPickUpObject = "Pick Up Object"
gaActivateDoor = "Activate Door"
gaActivateRADoor = "Activate RA Door"
gaActivateShuttle = "Activate Shuttle"
gaActivateShuttleGen = "Activate Shuttle Gen"

# Subject IDs
sidAgent = "Agent"
sidRedCard = "Red Card"
sidAccessDoor = "Access Door"
sidAccessDoorActivator1 = "Access Door Activator 1"
sidAccessDoorActivator2 = "Access Door Activator 2"
sidRedAccessDoor = "Red Access Door"
sidRedAccessDoorActivator1 = "Red Access Door Activator 1"
sidRedAccessDoorActivator2 = "Red Access Door Activator 2"
sidShuttleGen = "Shuttle Generator"
sidShuttleLaunch = "Shuttle Activator"

# Some Constants
cRoom1 = "Room 1"
cRoom2 = "Room 2"
cRoom3 = "Room 3"


# Given an action and the subject type, is the action compatible?
def IsActionAllowed(action, subjectType):
    if action == gaGoThroughDoor:
        if subjectType == goRedDoor:
            return True
        if subjectType == goDoor:
            return True
        return False
    elif action == gaActivateDoor:
        if subjectType == goDoorAct:
            return True
        return False
    elif action == gaActivateRADoor:
        if subjectType == goRedDoorAct:
            return True
        return False
    elif action == gaPickUpObject:
        if subjectType == goRedDoorKey:
            return True
        return False
    elif action == gaActivateShuttle:
        if subjectType == goShuttleAct:
            return True
        return False
    elif action == gaActivateShuttleGen:
        if subjectType == goShuttleGen:
            return True
        return False
    return False


class WorldState(object):
    def __init__(self):
        self.SetDefaultStates()

    def RemoveStateListKeys(self, stateList, stateKey):
        for i in xrange(len(stateList) - 1, -1, -1):
            key, value = stateList[i]
            if key == stateKey:
                del stateList[i]

    def StateListValues(self, stateList, stateKey):
        result = [v for k, v in stateList if k == stateKey]
        return result

    # Setup the default game world.
    def SetDefaultStates(self):
        states = [
            # Agent
            (sidAgent, kInRoom, cRoom1),
            (sidAgent, kSubjectType, goAgent),
            (sidAgent, kHasRedAccess, False),
            (sidAgent, kAction, [gaGoThroughDoor,
                                 gaPickUpObject,
                                 gaActivateDoor,
                                 gaActivateRADoor,
                                 gaActivateShuttle,
                                 gaActivateShuttleGen]),
            (sidAgent, kIsCarrying, []),
            # Red Access Card
            (sidRedCard, kInRoom, cRoom1),
            (sidRedCard, kSubjectType, goRedDoorKey),
            # Access Door
            (sidAccessDoor, kRoomPortal, (cRoom1, cRoom2)),
            (sidAccessDoor, kIsClosed, True),
            (sidAccessDoor, kSubjectType, goDoor),
            # Access Door Activators
            (sidAccessDoorActivator1, kInRoom, cRoom1),
            (sidAccessDoorActivator1, kSubjectType, goDoorAct),
            (sidAccessDoorActivator1, kActivatorTarget, sidAccessDoor),
            (sidAccessDoorActivator2, kInRoom, cRoom2),
            (sidAccessDoorActivator2, kSubjectType, goDoorAct),
            (sidAccessDoorActivator2, kActivatorTarget, sidAccessDoor),
            # Red Access Door
            (sidRedAccessDoor, kRoomPortal, (cRoom2, cRoom3)),
            (sidRedAccessDoor, kIsClosed, True),
            (sidRedAccessDoor, kSubjectType, goRedDoor),
            # Red Access Door Activators
            (sidRedAccessDoorActivator1, kInRoom, cRoom2),
            (sidRedAccessDoorActivator1, kSubjectType, goRedDoorAct),
            (sidRedAccessDoorActivator1, kActivatorTarget, sidRedAccessDoor),
            (sidRedAccessDoorActivator2, kInRoom, cRoom3),
            (sidRedAccessDoorActivator2, kSubjectType, goRedDoorAct),
            (sidRedAccessDoorActivator2, kActivatorTarget, sidRedAccessDoor),
            # Shuttle Power
            (sidShuttleGen, kIsPowered, False),
            (sidShuttleGen, kInRoom, cRoom3),
            (sidShuttleGen, kSubjectType, goShuttleGen),
            # Shuttle Launcher
            (sidShuttleLaunch, kIsActivated, False),
            (sidShuttleLaunch, kInRoom, cRoom3),
            (sidShuttleLaunch, kSubjectType, goShuttleAct),
        ]
        self.worldState = {}
        for (sid, key, value) in states:
            if not sid in self.worldState.keys():
                self.worldState[sid] = {}
            self.worldState[sid][key] = value

    # Based on the room ID, create a list of all the subjectIDs
    # in the room that are NOT the agent
    def GetGameObjectsForAgent(self, agentID):
        # The agent's current room
        agentRoom = self.worldState[agentID][kInRoom]
        # Iterate over ALL states (lots?)
        result = []
        for sid in self.worldState.keys():
            if (sid == agentID):
                continue
            if self.worldState[sid].has_key(kInRoom):
                sidRooms = [self.worldState[sid][kInRoom]]
            elif self.worldState[sid].has_key(kRoomPortal):
                sidRooms = list(self.worldState[sid][kRoomPortal])
                # Now that we have the room list, check if the agent
            # is in any of them.
            if agentRoom in sidRooms:
                result.append(sid)
        print "Game Room Objects: ROOM[%s] %s" % (agentRoom, result)
        return result

    # Generate a list of actions that the agent can execute
    # in the current room.  This will generate a list of
    # tuples.  Each tuple will be of the form;
    # (agentID, actionID, actionSubjectID)
    def GetValidActions(self, agentID):
        # Get the list of actions that the agent can perform
        actionList = self.worldState[agentID][kAction]
        # Get the list of objects in the room
        objectList = self.GetGameObjectsForAgent(agentID)
        result = []
        # Double loop to find all the combinations that are valid.
        for action in actionList:
            for sid in objectList:
                if IsActionAllowed(action, self.worldState[sid][kSubjectType]):
                    result.append((agentID, action, sid))
        return result

    def GetEffectsForAction(self,agentID,action,actionSubjectID):
        result = []
        if action == gaGoThroughDoor:
            agentRoom = self.worldState[agentID][kInRoom]
            pr1, pr2 = self.worldState[actionSubjectID][kRoomPortal]
            otherRoom = pr1
            if pr1 == agentRoom:
                otherRoom = pr2
            result.append((agentID,kInRoom,otherRoom))
        elif action == gaActivateDoor:
            result.append((self.worldState[actionSubjectID][kActivatorTarget],kIsClosed,False))
        elif action == gaActivateRADoor:
            result.append((self.worldState[actionSubjectID][kActivatorTarget], kIsClosed, False))
        elif action == gaPickUpObject:
            if self.worldState[actionSubjectID][kSubjectType] == goRedDoorKey:
                result.append((agentID,kHasRedAccess,True))
        elif action == gaActivateShuttle:
            result.append((actionSubjectID,kIsActivated,True))
        elif action == gaActivateShuttleGen:
            result.append((actionSubjectID,kIsPowered,True))

        # Now remove any of these that have already been met in the current world state
        result = [(sid, key, value) for (sid, key, value) in result if (key, value) not in self.worldState[sid]]
        return result

    # Generate a list of precondition tuples that must be satisfied as world
    # states.  If the world state is already satisfied, then it is NOT added
    # to the list.  Tuples are of the form: (subjectID, key, value)
    def GetPreconditionsForAction(self, agentID, action, actionSubjectID):
        result = []
        if action == gaGoThroughDoor:
            result.append((actionSubjectID, kIsClosed, False))
        elif action == gaActivateDoor:
            # Get the subjectID that the door is tied to and use
            # this.  The door should be closed before we try to
            # open it.
            result.append((self.worldState[actionSubjectID][kActivatorTarget], kIsClosed, True))
        elif action == gaActivateRADoor:
            result.append((self.worldState[actionSubjectID][kActivatorTarget], kIsClosed, True))
            result.append((agentID, kHasRedAccess, True))
            # NOTE:  There is also a procedural check to see if the agent has the Red Door Key.
        elif action == gaPickUpObject:
            if self.worldState[actionSubjectID][kSubjectType] == goRedDoorKey:
                result.append((agentID,kHasRedAccess,False))
            pass
        elif action == gaActivateShuttle:
            result.append((sidShuttleLaunch, kIsActivated, False))
        elif action == gaActivateShuttleGen:
            result.append((sidShuttleGen, kIsPowered, False))

        # Now remove any of these that have already been met in the current world state
        result = [(sid, key, value) for (sid, key, value) in result if not self.worldState[sid].has_key(key) or self.worldState[sid][key] != value]
        return result

    # Generate a list of precondition tuples that must be satisfied as world
    # states.  If the world state is already satisfied, then it is NOT added
    # to the list.  Tuples are of the form: (subjectID, key, value)
    def CheckPreconditionsForAction(self, agentID, action, actionSubjectID):
        result = True
        if action == gaGoThroughDoor:
            pass
        elif action == gaActivateDoor:
            pass
        elif action == gaActivateRADoor:
            # Iterate through the agent's inventory and see if it has the
            # Red Access Card.  If it does not, return False
            inventory = self.worldState[agentID][kIsCarrying]
            for sid in inventory:
                if self.worldState[sid][kSubjectType] == goRedDoorKey:
                    return True
                return False
        elif action == gaPickUpObject:
            pass
        elif action == gaActivateShuttle:
            pass
        elif action == gaActivateShuttleGen:
            pass
        return result

    def ExecuteAction(self, agentID, action, actionSubjectID):
        if action == gaGoThroughDoor:
            agentRoom = self.worldState[agentID][kInRoom]
            pr1, pr2 = self.worldState[actionSubjectID][kRoomPortal]
            otherRoom = pr1
            if pr1 == agentRoom:
                otherRoom = pr2
            self.worldState[agentID][kInRoom] = otherRoom
        elif action == gaActivateDoor:
            self.worldState[actionSubjectID][kIsClosed] = False
        elif action == gaActivateRADoor:
            self.worldState[actionSubjectID][kIsClosed] = False
        elif action == gaPickUpObject:
            del self.worldState[actionSubjectID][kInRoom]
            self.worldState[actionSubjectID][kIsBeingCarried] = agentID
            if not actionSubjectID in self.worldState[agentID][kIsCarrying]:
                self.worldState[agentID][kIsCarrying].append(actionSubjectID)
            if self.worldState[actionSubjectID][kSubjectType] == goRedDoorKey:
                self.worldState[agentID][kHasRedAccess] = True
        elif action == gaActivateShuttle:
            self.worldState[actionSubjectID][kIsActivated] = True
        elif action == gaActivateShuttleGen:
            self.worldState[actionSubjectID][kIsPowered] = True


    def Dump(self):
        keys = self.worldState.keys()
        keys.sort()
        for sid in keys:
            print "Subject ID: ", sid
            sidKeys = self.worldState[sid].keys()
            sidKeys.sort()
            for key in sidKeys:
                print " - (%s, %s)" % (key, self.worldState[sid][key])


class GameWorld(object):
    def __init__(self):
        # Dictionary of lists, keyed by subject ID.
        # Each list contains the "facts" about that
        # subject.
        self.worldState = WorldState()


gameWorld = GameWorld()
#gameWorld.worldState.Dump()
print
print
validActions = gameWorld.worldState.GetValidActions(sidAgent)
print "Valid Actions for %s:" % sidAgent
for (agentID, action, actionSubjectID) in validActions:
    print "  - (%s, %s, %s) "%(agentID, action, actionSubjectID)
    print "    Preconditions:"
    preconds = gameWorld.worldState.GetPreconditionsForAction(agentID,action,actionSubjectID)
    if len(preconds) > 0:
        for item in preconds:
            print "       - ",item
    else:
            print "       - None or Already Met"
    print "    Effects:"
    effects = gameWorld.worldState.GetEffectsForAction(agentID, action, actionSubjectID)
    for item in effects:
        sid,key,newValue = item
        currentValue = gameWorld.worldState.worldState[sid][key]
        print "       - (%s, %s, %s --> %s)"%(sid,key,currentValue,newValue)
