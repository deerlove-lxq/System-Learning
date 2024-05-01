"""
[Note] This script is used to give a sample network topology to test Algorithm-1.
[Details of the network topology]
    - Treat the topology as a multi-root tree with border switches being the roots
    - Starting from each input device, we add all its parents, grandparents and so on until the border switches into the emulated device set.
    - Clos-like datacenter network
        -- The whole network topology islayered
        -- Valley routing is now allowed
        -- The border switches connected to wide area network (WAN) are on the highest layer and usually share a single AS number.
[Network topology layer] Tor -> Leaf -> Spine(Border -> WAN)
"""

import queue

# Define a switch class
class Switch:
    def __init__(self, name, layer, as_num):
        self.name = name
        self.layer = layer
        self.as_num = as_num
        self.children = []
        self.parents = []

    def add_parent(self, parent):
        self.parents.append(parent)

# Add edge between two switches
def add_edge(parent, child):
    child.add_parent(parent)
    
def checkIsHighestLayer(switch):
    if switch.layer == "spine":
        return True
    return False

def findSafeDCBoundary(D):
    Dqueue = queue.Queue()
    DCB = []
    # Initialize queue with D
    for switch in D:
        Dqueue.put(switch)
    while not Dqueue.empty():
        switch = Dqueue.get()
        DCB.append(switch)
        if checkIsHighestLayer(switch):
            continue
        for parent in switch.parents:
            # not in DCB and not in Dqueue
            if parent not in DCB and parent not in list(Dqueue.queue):
                Dqueue.put(parent)
    return DCB

if __name__ == "__main__":
    # Create switches
    t1 = Switch("t1", "tor", 200)
    t2 = Switch("t2", "tor", 200)
    t3 = Switch("t3", "tor", 300)
    t4 = Switch("t4", "tor", 300)
    t5 = Switch("t5", "tor", 400)
    t6 = Switch("t6", "tor", 400)
    l1 = Switch("l1", "leaf", 200)
    l2 = Switch("l2", "leaf", 200)
    l3 = Switch("l3", "leaf", 300)
    l4 = Switch("l4", "leaf", 300)
    l5 = Switch("l5", "leaf", 400)
    l6 = Switch("l6", "leaf", 400)
    s1 = Switch("s1", "spine", 100)
    s2 = Switch("s2", "spine", 100)
    
    # Add edges
    for tor in [t1, t2]:
        for leaf in [l1, l2]:
            add_edge(parent=leaf, child=tor)
    for tor in [t3, t4]:
        for leaf in [l3, l4]:
            add_edge(parent=leaf, child=tor)
    for tor in [t5, t6]:
        for leaf in [l5, l6]:
            add_edge(parent=leaf, child=tor)
    for leaf in [l1, l3, l5]:
        add_edge(parent=s1, child=leaf)
    for leaf in [l2, l4, l6]:
        add_edge(parent=s2, child=leaf)
    
    # Only emulate L1 - L4
    G = [t1, t2, t3, t4, t5, t6, l1, l2, l3, l4, l5, l6, s1, s2]
    D = [l1, l2, l3, l4]
    
    # Get boundary switches according to Algorithm-1
    DCB = findSafeDCBoundary(D)
    print(f"Safe DC boundary includes: {[switch.name for switch in DCB]}")