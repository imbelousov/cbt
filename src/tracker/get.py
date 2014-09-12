import tcptracker


def get(urls):
    tracker = None
    for url in urls:
        protocol = url.split(":")[0]
        if protocol in ("http", "https"):
            tracker = tcptracker.TCPTracker(url)
            if tracker.check():
                break
    return tracker
