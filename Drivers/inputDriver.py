import pygame
import time

class InputDriver:
    def __new__(cls):
        instance = super(InputDriver, cls).__new__(cls)
        return instance

    def __init__(self):
        self.eventlisteners = []
        self.key_states = {}  # Tracks the state of keys
        self.key_timers = {}  # Tracks the last time a key event was processed
        self.original_events = {}  # Stores the original keydown events

    def poll(self, ev=None):
        if ev is None:
            ev = pygame.event.get()
        """Poll for events and notify listeners."""
        for event in ev:
            if event.type == pygame.KEYDOWN:
                key = event.key
                if key not in self.key_states or not self.key_states[key]:
                    # Key was not previously pressed
                    self.key_states[key] = True
                    self.key_timers[key] = time.time()  # Record the current time
                    self.original_events[key] = event  # Store the original event
                    self._notify_listeners(event)
            elif event.type == pygame.KEYUP:
                key = event.key
                self.key_states[key] = False  # Mark the key as released
                if key in self.original_events:
                    del self.original_events[key]  # Remove the stored event
            else:
                # Notify listeners for non-keyboard events
                self._notify_listeners(event)

        # Handle repeated keydown events with a delay
        current_time = time.time()
        for key, pressed in self.key_states.items():
            if pressed:  # If the key is still pressed
                if current_time - self.key_timers[key] >= 0.15:  # 200ms delay
                    if key in self.original_events:
                        fake_event = self._copy_event(self.original_events[key])
                        self._notify_listeners(fake_event)
                        self.key_timers[key] = current_time  # Reset the timer

    def _copy_event(self, event):
        """Create a 1:1 copy of the original event."""
        return pygame.event.Event(event.type, event.dict)

    def _notify_listeners(self, event):
        """Notify listeners of an event."""
        for listener in self.eventlisteners:
            if event.type == listener["type"]:
                listener["func"](event)  # Call the listener's function with the event

    def hook_event(self, type, func):
        """Register an event listener."""
        self.eventlisteners.append({"type": type, "func": func})
        print("Event hooked.")
        return len(self.eventlisteners) - 1
    def get_mouse_position(self):
        return pygame.mouse.get_pos()

    def get_mouse_buttons(self):
        return pygame.mouse.get_pressed()

    def get_keyboard_state(self):
        return pygame.key.get_pressed()

    def poll_events(self):
        return pygame.event.get()
    class keys:
        UNKNOWN = 0
        BACKSPACE = 8
        TAB = 9
        RETURN = 13
        ESCAPE = 27
        SPACE = 32
        EXCLAIM = 33
        QUOTEDBL = 34
        HASH = 35
        DOLLAR = 36
        PERCENT = 37
        AMPERSAND = 38
        QUOTE = 39
        LEFTPAREN = 40
        RIGHTPAREN = 41
        ASTERISK = 42
        PLUS = 43
        COMMA = 44
        MINUS = 45
        PERIOD = 46
        SLASH = 47
        NUM_0 = 48
        NUM_1 = 49
        NUM_2 = 50
        NUM_3 = 51
        NUM_4 = 52
        NUM_5 = 53
        NUM_6 = 54
        NUM_7 = 55
        NUM_8 = 56
        NUM_9 = 57,
        COLON = 58
        SEMICOLON = 59
        LESS = 60
        EQUALS = 61
        GREATER = 62
        QUESTION = 63
        AT = 64
        LEFTBRACKET = 91
        BACKSLASH = 92
        RIGHTBRACKET = 93
        CARET = 94
        UNDERSCORE = 95
        BACKQUOTE = 96
        a = 97
        b = 98
        c = 99
        d = 100
        e = 101
        f = 102
        g = 103
        h = 104
        i = 105
        j = 106
        k = 107
        l = 108
        m = 109
        n = 110
        o = 111
        p = 112
        q = 113
        r = 114
        s = 115
        t = 116
        u = 117
        v = 118
        w = 119
        x = 120
        y = 121
        z = 122
        DELETE = 127
        CAPSLOCK = 1073741881
        F1 = 1073741882
        F2 = 1073741883
        F3 = 1073741884
        F4 = 1073741885
        F5 = 1073741886
        F6 = 1073741887
        F7 = 1073741888
        F8 = 1073741889
        F9 = 1073741890
        F10 = 1073741891
        F11 = 1073741892
        F12 = 1073741893
        PRINT = 1073741894
        PRINTSCREEN = 1073741894
        SCROLLLOCK = 1073741895
        SCROLLOCK = 1073741895
        BREAK = 1073741896
        PAUSE = 1073741896
        INSERT = 1073741897
        HOME = 1073741898
        PAGEUP = 1073741899
        END = 1073741901
        PAGEDOWN = 1073741902
        RIGHT = 1073741903
        LEFT = 1073741904
        DOWN = 1073741905
        UP = 1073741906
        NUMLOCK = 1073741907
        NUMLOCKCLEAR = 1073741907
        NP_DIVIDE = 1073741908
        NP_MULTIPLY = 1073741909
        NP_MINUS = 1073741910
        NP_PLUS = 1073741911
        NP_ENTER = 1073741912
        NP_1 = 1073741913
        NP_2 = 1073741914
        NP_3 = 1073741915
        NP_4 = 1073741916
        NP_5 = 1073741917
        NP_6 = 1073741918
        NP_7 = 1073741919
        NP_8 = 1073741920
        NP_9 = 1073741921
        NP_0 = 1073741922
        NP_PERIOD = 1073741923
        POWER = 1073741926
        NP_EQUALS = 1073741927
        F13 = 1073741928
        F14 = 1073741929
        F15 = 1073741930
        HELP = 1073741941
        MENU = 1073741942
        SYSREQ = 1073741978
        CLEAR = 1073741980
        CURRENCYUNIT = 1073742004
        EURO = 1073742004
        CURRENCYSUBUNIT = 1073742005
        LCTRL = 1073742048
        LSHIFT = 1073742049
        LALT = 1073742050
        LGUI = 1073742051
        LMETA = 1073742051
        LSUPER = 1073742051
        RCTRL = 1073742052
        RSHIFT = 1073742053
        RALT = 1073742054
        RGUI = 1073742055
        RMETA = 1073742055
        RSUPER = 1073742055
        MODE = 1073742081
    class events:
        NOEVENT = 0
        KEYDOWN = 768
        KEYUP = 769
        MOUSEMOTION = 1024
        MOUSEBUTTONDOWN = 1025
        MOUSEBUTTONUP = 1026
        JOYAXISMOTION = 1536
        JOYBALLMOTION = 1537
        JOYHATMOTION = 1538
        JOYBUTTONDOWN = 1539
        JOYBUTTONUP = 1540