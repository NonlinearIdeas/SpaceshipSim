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
#    | - VERTICAL WALL (just for show)
#    - - HORIZONTAL WALL (just for show)
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
# take off in the shuttle.  The shuttle needs power
# to launch, provided by the generator Q.
#
# The ideal sequence of actions is:
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

def GetRoomDistanceCost(srcRoom,desRoom):
    costs = {
        cRoom1:{
            cRoom1:0,
            cRoom2:1,
            cRoom3:2
        },
        cRoom2:{
            cRoom1:1,
            cRoom2:0,
            cRoom3:1
        },
        cRoom3:{
            cRoom1:2,
            cRoom2:1,
            cRoom3:0
        }
    }
    return costs[srcRoom][desRoom]


def GetActionCost(action):
    if action == gaGoThroughDoor:
        return 1
    elif action == gaActivateDoor:
        return 1
    elif action == gaActivateRADoor:
        return 1
    elif action == gaPickUpObject:
        return 1
    elif action == gaActivateShuttle:
        return 1
    elif action == gaActivateShuttleGen:
        return 1
    return 25


class WorldState(object):
    def __init__(self):
        self.worldState = {}
        self.SetDefaultStates()

    # Setup the default game world.
    def SetDefaultStates(self):
        states = [
            # Agent
            (sidAgent, kInRoom, cRoom2),
            (sidAgent, kSubjectType, goAgent),
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
            sidRooms = []
            if sid == agentID:
                continue
            if self.worldState[sid].has_key(kInRoom):
                sidRooms = [self.worldState[sid][kInRoom]]
            elif self.worldState[sid].has_key(kRoomPortal):
                sidRooms = list(self.worldState[sid][kRoomPortal])
                # Now that we have the room list, check if the agent
            # is in any of them.
            if agentRoom in sidRooms:
                result.append(sid)
        #print "Game Room Objects: ROOM[%s] %s" % (agentRoom, result)
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
            # NOTE:  There is also a procedural check to see if the agent has the Red Door Key.
        elif action == gaPickUpObject:
            # There are not any constraints on what can be picked up.  As long as it can
            # be picked up.
            pass
        elif action == gaActivateShuttle:
            result.append((sidShuttleLaunch, kIsActivated, False))
            result.append((sidShuttleGen, kIsPowered, True))
        elif action == gaActivateShuttleGen:
            result.append((sidShuttleGen, kIsPowered, False))

        # Now remove any of these that have already been met in the current world state
        result = [(sid, key, value) for (sid, key, value) in result if
                  not self.worldState[sid].has_key(key) or self.worldState[sid][key] != value]
        return result

    # Procedural preconditions are used to prune paths from the tree.  This allows
    # complex calculations to be done to evaluate whether an action should be run or
    # not.
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
            doorID = self.worldState[actionSubjectID][kActivatorTarget]
            self.worldState[doorID][kIsClosed] = False
        elif action == gaActivateRADoor:
            doorID = self.worldState[actionSubjectID][kActivatorTarget]
            self.worldState[doorID][kIsClosed] = False
        elif action == gaPickUpObject:
            del self.worldState[actionSubjectID][kInRoom]
            self.worldState[actionSubjectID][kIsBeingCarried] = agentID
            if not actionSubjectID in self.worldState[agentID][kIsCarrying]:
                self.worldState[agentID][kIsCarrying].append(actionSubjectID)
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


class PlannerNode(object):
    def __init__(self, worldState, goalList, actionHistory):
        self.worldState = copy.deepcopy(worldState)
        self.actionHistory = copy.deepcopy(actionHistory)
        self.goalList = copy.deepcopy(goalList)
        self.score = 0

    def CalculateScore(self,agentID):
        score = 0
        for agentIDOther, action, actionSubjectID in self.actionHistory:
            score += GetActionCost(action)
        # Add in something for how far away the agent is from the
        # final room.  This may help or may hinder depending on how
        # much back-and-forth is required.
        srcRoom = self.worldState.worldState[agentID][kInRoom]
        if len(self.goalList) > 0:
            desRoom = self.worldState.worldState[self.goalList[0][0]][kInRoom]
        else:
            desRoom = srcRoom
        roomCost = GetRoomDistanceCost(srcRoom,desRoom)
        score += roomCost*5
        return score

    def CanApplyAction(self, agentID, action, actionSubjectID, uniqueActions=False):
        # Already applied it before
        actionTup = (agentID, action, actionSubjectID)
        if uniqueActions:
            if actionTup in self.actionHistory:
                return False
        else:
            # Still, should not even try the same action again immediately...
            # that would be just silly.
            if len(self.actionHistory) > 0 and self.actionHistory[-1] == actionTup:
                return False
        # Cannot apply it if there are preconditions that are not met.
        preconds = self.worldState.GetPreconditionsForAction(agentID, action, actionSubjectID)
        if len(preconds) > 0:
            return False
        if not self.worldState.CheckPreconditionsForAction(agentID,action,actionSubjectID):
            return False
        return True

    def ApplyAction(self, agentID, action, actionSubjectID):
        # Execute the action
        self.worldState.ExecuteAction(agentID, action, actionSubjectID)
        # Now look through the goal states and compare them to the generated
        # world states. If any of the states have been satisfied, pull them
        # from the goal states.
        goalsLeft = [(sid, key, value) for (sid, key, value) in self.goalList if
                     not self.worldState.worldState[sid].has_key(key) or self.worldState.worldState[sid][key] != value]
        self.goalList = goalsLeft
        # Add this action to the previous actions performed so we don't
        # try this again.
        self.actionHistory.append((agentID, action, actionSubjectID))
        # Update the score
        self.score = self.CalculateScore(agentID)


class Planner(object):
    def __init__(self, goalList, worldState, agentID):
        self.goalList = copy.deepcopy(goalList)
        self.worldState = copy.deepcopy(worldState)
        self.agentID = agentID

    def PlanActions(self, uniqueActions, iterCountLimit):
        iterCount = 0
        openList = [PlannerNode(self.worldState, self.goalList, [])]
        while len(openList) > 0:
            iterCount = iterCount + 1
            if iterCountLimit != None and iterCount >= iterCountLimit:
                return []
                # Sort the list so the least cost node is at the front.
            openList.sort(key=lambda x: x.score,reverse=False)
            # Pull off the least cost node.
            node = openList[0]
            print
            print "-------------------"
            print "Generating Nodes [%d] (open list len = %d)" % (iterCount, len(openList))
            print "  History = ", node.actionHistory
            print "  Score   = ", node.score
            print "-------------------"
            # Take it off the open list
            openList.remove(node)
            # Generate the valid actions for the node
            validActions = node.worldState.GetValidActions(self.agentID)
            # If the action has not been applied already and the
            # preconditions have been met, then apply the action to the
            # world state and update the goals.
            for agentID, action, actionSubjectID in validActions:
                if node.CanApplyAction(agentID, action, actionSubjectID, uniqueActions):
                    # This action is applicable, create a new node, apply
                    # the action, add it to the open list.
                    print " - Creating node to apply action: ", (agentID, action, actionSubjectID)
                    newNode = PlannerNode(node.worldState, node.goalList, node.actionHistory)
                    print "   - Executing Action:", (agentID, action, actionSubjectID)
                    newNode.ApplyAction(agentID, action, actionSubjectID)
                    # If the new node has an empty goal set, it means we are done!
                    if len(newNode.goalList) == 0:
                        return iterCount, newNode.actionHistory
                    print "   - Node Action History: ", newNode.actionHistory
                    print "   - Node Score for Actions: ", newNode.score
                    openList.append(newNode)
                    # If we got here, it means we tried EVERYTHING possible and could not
            # create a valid plan.
        return (iterCount,[])

    def PrintSolutionBanner(self,iterCount,actions):
        if len(actions) > 0:
            print "   ----------------------------------"
            print "   SOLUTION FOUND"
            if len(actions) > 0:
                print "   Iterations / Actions = %f" % (iterCount * 1.0 / len(actions))
            print "   ----------------------------------"
        else:
            print "   ----------------------------------"
            print "   NO SOLUTION FOUND"
            print "   Iterations = %d" % (iterCount)
            print "   ----------------------------------"


    def PlanActionsMixed(self, iterCountLimit=100):
        iterCount1, actions = self.PlanActions(uniqueActions=True, iterCountLimit=None)
        # If we got an answer from unique actions, then we are done.
        if len(actions) > 0:
            self.PrintSolutionBanner(iterCount1,actions)
            return actions
        # Return the result from the longer search.
        iterCount2, actions = self.PlanActions(uniqueActions=False, iterCountLimit=iterCountLimit)
        self.PrintSolutionBanner(iterCount1+iterCount2, actions)
        return actions


def PrintActions(actions):
    print
    print "Actions:"
    if len(actions) == 0:
        print "  - None"
    else:
        for act in actions:
            print "  - ", act

baseWorldState = WorldState()
#baseWorldState.Dump()
goalList = [
    (sidShuttleLaunch, kIsActivated, True)
]
planner = Planner(goalList, baseWorldState, sidAgent)
actions = planner.PlanActionsMixed()
PrintActions(actions)
