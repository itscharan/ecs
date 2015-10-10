__author__='Sricharan'
from kazoo.client import KazooClient
import sys
import gevent
import zerorpc
from random import randrange


class Server():
    def __init__(self, addr, zk_server_list=["127.0.0.1:2181"]):
        self.addr=addr
        self.zk_slist = ",".join(zk_server_list)
        self.zk = KazooClient(self.zk_slist)
        self.current = 0
        self.request = 0
        self.goal = 0
        self.requests = []
        self.status = 'stop'
        self.ispicked = False

        #self.recover()

        try:
            self.zk.start()
        except:
            print "Couldn't connect to zookeeper start zkServer.sh"
            sys.exit()
        self.path='/zookeeper/election'

        if not self.zk.exists(self.path):
            self.zk.create(self.path, 'ecs')

        self.election()
        gevent.spawn(self.start)

    def election(self):

        self.zk.ensure_path(self.path)
        Lpath = self.zk.create(self.path+"/child_", self.addr, ephemeral=True, sequence=True)
        self.seq = Lpath.split("/election/")[1]
        children = self.zk.get_children(self.path)
        children.sort()
        child_index = children.index(self.seq)
        if child_index == 0:
            self.leader = self.addr
            self.children_addr = self.children_addr_list()
            self.zk.set(self.path, self.addr)
        else:
            self.zk.exists(self.path + "/" + children[child_index-1], watch = self.previous_child_watch)
            leader = self.zk.get(self.path, self.leader_watch)
            self.leader = str(leader[0])

    def previous_child_watch(self, event):
        children = self.zk.get_children(self.path)
        children.sort()
        child_index = children.index(self.seq)
        if child_index == 0:
            self.leader = self.addr
            self.children_addr = self.children_addr_list()
            self.zk.set(self.path, self.addr)
        else:
            self.zk.exists(self.path + "/" + children[child_index-1], watch = self.previous_child_watch)

    def leader_watch(self, event):
        leader = self.zk.get(self.path, self.leader_watch)
        self.leader = str(leader[0])

    def watch_children(self, event):
        self.children_addr = self.children_addr_list()
        pass

    def children_addr_list(self):
        children = self.zk.get_children(self.path, self.watch_children)
        children_addr = []
        for child in children:
            child_data = self.zk.get(self.path + "/" + child)
            children_addr.append(child_data[0])
        return children_addr

    def server(self):
        self.servers=self.children_addr_list()
        self.connections=[]
        for serve in self.servers:
            if serve == self.addr:
                self.connections.append(self)
            else:
                c = zerorpc.Client(timeout=10)
                c.connect('tcp://' + serve)
                self.connections.append(c)
        return self.servers

    # def recover(self):
    #     #TODO share the load from other elevators after recover

    def pickup_request(self, pickup_floor, goal_floor):
        i = randrange(0,len(self.server()))
        result = self.connections[i].add_request(pickup_floor,goal_floor)
        print 'request received from pick up floor %s and drop floor %s' %(abs(pickup_floor), goal_floor)
        return "request sent to %s" % self.connections[i].get_addr()

    def add_request(self, pickup_floor, goal_floor):
        self.requests.append((pickup_floor,goal_floor))

    def drop(self):
        self.ispicked = False
        print 'dropped passenger on %s floor' % self.goal

    def see_request(self):
        return self.requests

    def pickup(self):
        self.ispicked = True
        print 'picked passenger from %s floor' % abs(self.request)

    def step(self):
        #time based simulation of server
        gevent.sleep(2)
        if not self.ispicked:
            temp = abs(self.request)
        else:
            temp = self.goal
        if self.current > temp:
            self.move_down()
        else:
            self.move_up()

    def move_up(self):
        self.current += 1
        self.status = 'up'
        print 'At floor %s  and moving up' % self.current

    def move_down(self):
        self.current -= 1
        self.status = 'down'
        print 'At floor %s  and moving down' % self.current

    def stop(self):
        self.status = 'stop'
        print 'Elevator stopped at %s floor' % self.current

    def get_addr(self):
        return self.addr

    def get_curr_floor(self):
        return self.current

    def get_goal_floor(self):
        return self.goal

    def get_status(self):
        return self.status

    def query_status(self):
        status = ""
        for i, server in enumerate(self.server()):
            if self.connections[i].get_status() == 'stop':
                status += '%s stopped at floor %s\n' % (self.connections[i].get_addr(), self.connections[i].get_curr_floor())
            else:
                status += '%s is going from %s to %s\n' %(self.connections[i].get_addr(), self.connections[i].get_curr_floor(), self.connections[i].get_goal_floor())
        return status

    def start(self):
        while True:
            gevent.sleep(2)
            print 'I am %s and Elevator Control System is running on [%s]' % (self.addr, self.leader)
            if len(self.requests):
                self.request, self.goal = self.requests.pop(0)
                if not self.ispicked:
                    while self.current is not abs(self.request):
                        self.step()
                    self.pickup()

                while self.current is not self.goal:
                    self.step()
                self.drop()
            else:
                self.stop()
            pass

if __name__ == "__main__":
    server = Server(sys.argv[1])
    serv = zerorpc.Server(server)
    serv.bind("tcp://" + sys.argv[1])
    print "Starting Elevator %s" % sys.argv[1]
    serv.run()