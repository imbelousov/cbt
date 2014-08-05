#!/usr/bin/python

"""
Console Bit Torrent Client
"""

from bencode import Bencode

def main():
    """File = Bencode()
    File.Open("1.torrent")
    Dict = File.Read()
    File.Close()
    print "announce:"
    print "    %s" % Dict["announce"]
    print "announce-list:"
    for item in Dict["announce-list"]:
        print "    %s" % item[0]
    print "comment:"
    print "    %s" % Dict["comment"].decode("utf-8").encode("cp866")
    print "created by:"
    print "    %s" % Dict["created by"].decode("utf-8").encode("cp866")
    print "creation date:"
    print "    %s" % Dict["creation date"]
    print "encoding:"
    print "    %s" % Dict["encoding"]
    print "files:"
    for item in Dict["info"]["files"]:
        path = ""
        for sub in item["path"]:
            path += sub + " "
        print "    %s(%d)" % (path.decode("utf-8").encode("cp866"), item["length"])
    print "name:"
    print "    %s" % Dict["info"]["name"].decode("utf-8").encode("cp866")
    print "piece length:"
    print "    %s" % Dict["info"]["piece length"]
    print "pieces:"
    print "    %s bytes array" % len(Dict["info"]["pieces"])"""
    File = Bencode()
    File.OpenFromString("d2:ggi100e3:lol5:win!!e")
    print File.Read()
    File.Close()

if __name__ == "__main__":
    main()