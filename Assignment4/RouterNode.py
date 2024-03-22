#!/usr/bin/env python
import GuiTextArea, RouterPacket, F 
from copy import deepcopy

class RouterNode():
    myID = None
    myGUI = None
    sim = None
    costs = None

    # Access simulator variables with:
    # self.sim.POISONREVERSE, self.sim.NUM_NODES, etc.

    # --------------------------------------------------
    def __init__(self, ID, sim, costs):
        self.myID = ID
        self.sim = sim
        self.myGUI = GuiTextArea.GuiTextArea("  Output window for Router #" + str(ID) + "  ")
        self.costs = deepcopy(costs)

        # Creates an array of four arrays which start as INFINITY. 
        self.routerCosts = []
        for _ in range(self.sim.NUM_NODES):
            row = []
            for _ in range(self.sim.NUM_NODES):
                row.append(self.sim.INFINITY)
            self.routerCosts.append(row)

        for i in range(self.sim.NUM_NODES):
            for j in range(self.sim.NUM_NODES):
                if i == self.myID:
                    self.routerCosts[i][j] = self.costs[j]
                elif i == j:
                    self.routerCosts[i][j] = 0
                else:
                    self.routerCosts[i][j] = self.sim.INFINITY

        # Looks like this:
        """ [
        [999, 999, 999, 999],
        [999, 999, 999, 999],
        [999, 999, 999, 999],
        [999, 999, 999, 999]
        ] """

        # Create an array containing the connections each router has and sets the number 
        # which it is not, if any, connected to as '-'.
        self.nextStep = [self.sim.INFINITY] * self.sim.NUM_NODES
        # Checks if the cost for index (i) is less than infinity, then appends i. Otherwise appends None.
        for i in range(self.sim.NUM_NODES):
            self.nextStep[i] = None if self.costs[i] == self.sim.INFINITY else i
        
        # Share the updated neighbor costs with all neighbors.
        self.shareUpdatesToNeighbors()
        self.printDistanceTable()

    # --------------------------------------------------
    # Process the routing update received from a neighbor.
    def recvUpdate(self, pkt):
        # Update the current cost of the neighbor with the current mincost in the RouterPacket.
        self.routerCosts[pkt.sourceid] = pkt.mincost
        
        # Update the route taken to a packet based on lowest cost after updating neighbor cost.
        if(self.updateRoutes()):
            # Then share the update with all neighbors.
            self.shareUpdatesToNeighbors()

    # --------------------------------------------------
    def sendUpdate(self, pkt):
        # Loop through all routers in the network, checking if their next step is neighbor,
        # if it is, set the copy of minCosts value for the current router to infinity.

        # To simplify, Poison reverse sets the current value to infinity to make sure the neighbor, when receiving
        # this information, doesn't take the same direction through the current node towards the destination.
        # This prevents it from being stuck in a loop trying to get to an unreachable node or taking a costly route.
        if self.sim.POISONREVERSE:
            for router in range(self.sim.NUM_NODES):
                if self.nextStep[router] == pkt.destid:
                    pkt.mincost[router] = self.sim.INFINITY
        
        self.sim.toLayer2(pkt)

    # --------------------------------------------------
    def printInitialTable(self):
        # Prints out the initial table seen in the assignment pdf.
        self.myGUI.println("Current table for " + str(self.myID) + "  at time " + str(self.sim.getClocktime()))
        self.myGUI.println("")
        self.myGUI.println("Distance Table:")
        
        routernumbers = "  dst   |"
        seperator = "--------"

        for router in range(self.sim.NUM_NODES):
            routernumbers += "     " + str(router)
            seperator += "---------"

        self.myGUI.println(routernumbers)
        self.myGUI.println(seperator)

        for router in range(self.sim.NUM_NODES):
            # If it's not itself or an invalid route prepare the line.
            if self.costs[router] != 0 and self.costs[router] != self.sim.INFINITY:
                line = "  nbr " + str(router) + " |"
        
                for _ in range(self.sim.NUM_NODES):
                    line += "     " + str(self.sim.INFINITY)

                # Outputs the line for each neighbor.
                self.myGUI.println(line)
        self.myGUI.println("")

    # --------------------------------------------------
    def printDistanceTable(self):
        # Can comment out the printinitialTable func for better readability.
        self.printInitialTable()
        # Time for our calculated costs and routes
        self.myGUI.println("Our distance vector and routes:")
        
        dst = "  dst   |"
        cost = " cost  |"
        route = " route |"
        seperator = "--------"

        for router in range(self.sim.NUM_NODES):
            # Increase the size of the seperator depending on the amount of nodes / routers in the network
            seperator += "---------"
            # Format the destination numbers.
            dst += "     " + str(router)
            # Format the cost to connect to the destination.
            cost += "     " + str(self.routerCosts[self.myID][router])
            # Format the route which is taken.
            route += "     " + str("-" if self.routerCosts[self.myID][router] >= self.sim.INFINITY else self.nextStep[router])
        
        # Print the destination numbers and seperator
        self.myGUI.println(dst)
        self.myGUI.println(seperator)
        
        # Print the cost to connect to the destination.
        self.myGUI.println(cost)
        
        # Print the route which is taken.
        self.myGUI.println(route)
        
    # --------------------------------------------------
    def updateLinkCost(self, dest, newcost):

        # Updates the cost in the routers' cost table.
        self.costs[dest] = newcost
        
        # Update the cost of the link
        self.routerCosts[self.myID][dest] = newcost
        self.routerCosts[dest][self.myID] = newcost

        # Share the updated neighbor costs with all neighbors.
        self.shareUpdatesToNeighbors()

    # --------------------------------------------------
    def shareUpdatesToNeighbors(self):
        # Loop through all neighbors, making sure their cost isn't infinity, then make a copy of minCosts,
        # which can be modified in case of POISON REVERSE.

        for neighbor in range(self.sim.NUM_NODES):
            if neighbor != self.myID and self.costs[neighbor] != self.sim.INFINITY and self.nextStep[neighbor] != None:
                costCopy = deepcopy(self.routerCosts[self.myID])
                # Share updated routing information to neighbors.
                self.sendUpdate(RouterPacket.RouterPacket(self.myID, neighbor, costCopy))
            
    # --------------------------------------------------
    def updateRoutes(self):
        # Flag to track if any routes were updated
        updateRoute = False

        # Loop through each router in the network
        for router in range(self.sim.NUM_NODES):
            # Skip updating for the current router itself
            if router == self.myID:
                continue
            
            # Get the cost from current to the nextStep router
            nextCost = self.routerCosts[self.myID][self.nextStep[router]]
            
            # Get the cost from the nextStep router to the destination router
            nextToDestCost = self.routerCosts[self.nextStep[router]][router]

            # Calculate the new cost using the Bellman-Ford algorithm
            # (The cost from current to the nextStep + the cost from nextStep of current to the destination router)
            newCost = nextCost + nextToDestCost

            # If the new cost is different from the current cost to the neighbor router
            if self.routerCosts[self.myID][router] != newCost:
                # Update the cost to the neighbor router
                self.routerCosts[self.myID][router] = newCost

                # If the new cost exceeds the default cost, revert to default and update nextStep to the current router
                if self.routerCosts[self.myID][router] > self.costs[router]:
                    self.routerCosts[self.myID][router] = self.costs[router]
                    self.nextStep[router] = router

                # Mark that a route has been updated
                updateRoute = False


            # Update routes for other routers if a shorter path is found
            for nextrouter in range(self.sim.NUM_NODES):

                # Get the cost from the current router to the neighbor router
                nextCost = self.routerCosts[self.myID][nextrouter]

                # The newCost is the Bellman-Ford algorithm.
                # (The cost from current to the next router + the cost from next router to the next router after that)
                newCost = self.routerCosts[self.myID][router] + self.routerCosts[router][nextrouter]

                # If the new cost is lower than the cost to the nextStep router.
                # Pretty much checks if the new route has a lower cost than the default route.  
                if newCost < nextCost:
                    # If the new route is cheaper, update the cost to the neighbor router to the new cost.
                    # And update the nextStep for the neighbor to itself.
                    # Basically says that the destination router is cheapest through neighbor.
                    self.routerCosts[self.myID][nextrouter] = newCost
                    self.nextStep[nextrouter] = self.nextStep[router]

                    # Mark that a route has been updated.
                    updateRoute = False


        # Return whether any routes were updated or not.
        return updateRoute

    