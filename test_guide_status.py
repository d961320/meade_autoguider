from guiding.status import GuideStatus

status = GuideStatus()

print(status)

status.mount_connected = True
status.locked = True
status.dx = 1.4
status.dy = -0.8
status.guide_error = 1.61

print()
print(status)
