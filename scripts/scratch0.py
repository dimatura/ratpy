
from ratpy import RatPy as rp

rp.update()

rp.debug_dump()

frame = rp.current_frame()

#print(frame.gx, frame.gy)

fleft = rp.global_find_frame_left()
print(fleft)
#rp.global_focusleft()

rp.global_focusright()
