from TrackerRequest import TrackerRequest

class UdpTrackerRequest(TrackerRequest):
    def __init__(self, Host, Info):
        super(UdpTrackerRequest, self).__init__(Host, Info)
    
    def Request(self, Event, Uploaded=0, Downloaded=0, Left=0):
        return None