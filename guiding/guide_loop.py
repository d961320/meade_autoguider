#!/usr/bin/env python3

"""
GuideLoop

Første version af guide-loopet.

Denne version beregner ingen guidepulser endnu.
Den indsamler blot status fra GuideTracker.
"""

from guiding.status import GuideStatus


class GuideLoop:

    def __init__(self, tracker, mount):

        self.tracker = tracker
        self.mount = mount

        self.status = GuideStatus()

    def step(self):
        """
        Kaldes én gang for hvert nyt kamerabillede.
        """

        self.status.mount_connected = self.mount.connected

        self.status.locked = self.tracker.locked
        self.status.lost = self.tracker.lost

        if self.tracker.current_x is not None:
            self.status.current_x = self.tracker.current_x

        if self.tracker.current_y is not None:
            self.status.current_y = self.tracker.current_y

        self.status.dx = self.tracker.dx
        self.status.dy = self.tracker.dy

        self.status.guide_error = (
            self.tracker.dx ** 2 +
            self.tracker.dy ** 2
        ) ** 0.5

        return self.status
