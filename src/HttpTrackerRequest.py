from TrackerRequest import TrackerRequest
from PeerId import GetPeerId
from BCode import BCode
import urllib
import urllib2

class HttpTrackerRequest(TrackerRequest):
    EVENT_STARTED = "started"
    EVENT_STOPPED = "stopped"

    def __init__(self, Host, Info):
        super(HttpTrackerRequest, self).__init__(Host, Info)
    
    def Request(self, Event, Uploaded=0, Downloaded=0, Left=0):
        Url = self.Host
        if not "?" in Url:
            UrlSeparator = "?"
        else:
            UrlSeparator = "&"
        Url += UrlSeparator
        Get = {}
        Get["info_hash"] = self.GetInfoHash()
        Get["peer_id"] = GetPeerId()
        Get["port"] = self.GetPort()
        Get["uploaded"] = Uploaded
        Get["downloaded"] = Downloaded
        Get["left"] = Left
        Get["compact"] = 1
        Get["event"] = Event
        UrlParams = urllib.urlencode(Get)
        Url += UrlParams
        Response = urllib2.urlopen(Url).read()
        Encoder = BCode()
        Encoder.OpenFromString(Response)
        Result = Encoder.Decode()
        Encoder.Close()
        return Result