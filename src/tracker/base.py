class BaseTracker(object):
    def check(self):
        return False

    def get_peers(self):
        pass

    def send_finished(self):
        pass

    def send_regular(self):
        pass

    def send_start(self):
        pass

    def send_stop(self):
        pass
