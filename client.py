__author__='Sricharan'
from kazoo.client import KazooClient
import sys
import zerorpc

class Client():
    def __init__(self, zk_server_list=["127.0.0.1:2181"]):
        self.path='/zookeeper/election'
        self.zk_slist = ",".join(zk_server_list)
        self.zk = KazooClient(self.zk_slist)
        try:
            self.zk.start()
        except:
            print "Unable to connect"
            sys.exit()		
	
    def get_leader(self):
        try:
           leader_data = self.zk.get(self.path)
           self.leader = leader_data[0]
        except:
            print "No Storage Server is available"

    def get_status(self):
        self.get_leader()
        try:
            if self.leader:
                self.sto_serv = zerorpc.Client(timeout=3)
                self.sto_serv.connect("tcp://" + self.leader)
            flag = 5
            while flag:
                try:
                    print 'connecting to leader'
                    value = self.sto_serv.query_status()
                    if value is None:
                        print 'Failed to get the status'
                    else:
                        print value
                    break
                except zerorpc.TimeoutExpired:
                    self.leader = None
                    flag -= 1
                print 'Leader failed and '+ str(flag)+ ' retry left'
            if not flag:
                print 'Transaction Failed and No Server is running'
        except AttributeError:
            print "Try again latter"

    def get_requests(self):
        self.get_leader()
        try:
            if self.leader:
                self.sto_serv = zerorpc.Client(timeout=3)
                self.sto_serv.connect("tcp://" + self.leader)
            flag = 5
            while flag:
                try:
                    print 'connecting to leader'
                    value = self.sto_serv.see_request()
                    if value is None:
                        print 'Failed to get the status'
                    else:
                        print value
                    break
                except zerorpc.TimeoutExpired:
                    self.leader = None
                    flag -= 1
                print 'Leader failed and '+ str(flag)+ ' retry left'
            if not flag:
                print 'Transaction Failed and No Server is running'
        except AttributeError:
            print "Try again latter"

    def request(self, pickup, drop):
        self.get_leader()
        try:
            if self.leader:
                self.sto_serv = zerorpc.Client(timeout=3)
                self.sto_serv.connect("tcp://" + self.leader)
            flag = 5
            while flag:
                try:
                    print 'connecting to leader'
                    value = self.sto_serv.pickup_request(pickup, drop)
                    if value is None:
                        print 'Failed to get the status'
                    else:
                        print value
                    break
                except zerorpc.TimeoutExpired:
                    self.leader = None
                    flag -= 1
                print 'Leader failed and '+ str(flag)+ ' retry left'
            if not flag:
                print 'Transaction Failed and No Server is running'
        except AttributeError:
            print "Try again latter"


if __name__ == "__main__":
    store = Client()
    # Loop to send requests, query status

    store.request(10, 20)
    store.request(-15, 10)
    store.request(2, 3)
    #store.get_status()
