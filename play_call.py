import random
import sys

gvgai_path = '/Volumes/Data_01/home/g/hybrid/GVGAI_GYM/'
sys.path.insert(0,gvgai_path)
from play import play

def local_play(level, player, gvgai_path, max_len=1000):
    """
    local_play is a utility function.
    The function allows us to call play from inside the pcgrl repository. 
    """

    result = None

    try:
        result = play(level, player, gvgai_path, 1000)
    except:
        result = -1.0

    return result