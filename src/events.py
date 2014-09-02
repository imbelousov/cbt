class EventsModel(object):
    def __init__(self):
        self._handlers = {}

    def event_call(self, event, *args, **kwargs):
        if event not in self._handlers:
            return
        for func in self._handlers[event]:
            func(*args, **kwargs)

    def event_connect(self, event, handler):
        if event in self._handlers and handler not in self._handlers[event]:
            self._handlers[event].append(handler)

    def event_init(self, *events):
        for event in events:
            self._handlers[event] = []

