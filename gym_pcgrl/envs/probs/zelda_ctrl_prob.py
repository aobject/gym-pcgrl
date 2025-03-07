import numpy as np
from pdb import set_trace as TT

from gym_pcgrl.envs.helper import (
    calc_certain_tile,
    calc_num_regions,
    get_range_reward,
    get_tile_locations,
    run_dikjstra,
    get_path_coords,
)
from gym_pcgrl.envs.probs.zelda_prob import ZeldaProblem


class ZeldaCtrlProblem(ZeldaProblem):
    def __init__(self):
        super(ZeldaCtrlProblem, self).__init__()
        self._max_nearest_enemy = np.ceil(self._width / 2 + 1) * (self._height)
        #FIXME lmao this is half what it should be. Seennndddiiinggg me!! :~)
        self._max_path_length = np.ceil(self._width / 2 + 1) * (self._height)
        # like "_rewards" but for use with ParamRew
        self.weights = {
            "player": 3,
            "key": 3,
            "door": 3,
            "regions": 5,
            "enemies": 1,
            "nearest-enemy": 1,
            "path-length": 1,
        }

        self.static_trgs = {
            "enemies": (2, self._max_enemies),
            "path-length": self._max_path_length,
            "nearest-enemy": (5, self._max_nearest_enemy),
            "regions": 1,
            "player": 1,
            "key": 1,
            "door": 1,
        }
        # conditional inputs/targets ( just a default we don't use in the ParamRew wrapper)
        self.cond_trgs = {
            "player": 1,
            "key": 1,
            "door": 1,
            "regions": 1,
            "enemies": 5,
            "nearest-enemy": 7,
            "path-length": 100,
        }
        # boundaries for conditional inputs/targets
        self.cond_bounds = {
            "nearest-enemy": (0, self._max_nearest_enemy),
            "enemies": (0, self._width * self._height - 2),
            "player": (0, self._width * self._height - 2),
            "key": (0, self._width * self._height - 2),
            "door": (0, self._width * self._height - 2),
            "regions": (0, self._width * self._height / 2),
            # FIXME: we shouldn't assume a square map here! Find out which dimension is bigger
            # and "snake" along that one
            # Upper bound: zig-zag
            "path-length": (0, self._max_path_length),
            #   11111111
            #   00000001
            #   11111111
            #   10000000
            #   11111111
        }

    # We do these things in the ParamRew wrapper
    def get_episode_over(self, new_stats, old_stats):
        return False

    def get_reward(self, new_stats, old_stats):
        return None

    """
    Get the current stats of the map

    Returns:
        dict(string,any): stats of the current map to be used in the reward, episode_over, debug_info calculations.
        The used status are "reigons": number of connected empty tiles, "path-length": the longest path across the map
    """

    def get_stats(self, map):
        self.path = []
        map_locations = get_tile_locations(map, self.get_tile_types())
        map_stats = {
            "player": calc_certain_tile(map_locations, ["player"]),
            "key": calc_certain_tile(map_locations, ["key"]),
            "door": calc_certain_tile(map_locations, ["door"]),
            "enemies": calc_certain_tile(map_locations, ["bat", "spider", "scorpion"]),
            "regions": calc_num_regions(
                map,
                map_locations,
                ["empty", "player", "key", "bat", "spider", "scorpion"],
            ),
            "nearest-enemy": 0,
            "path-length": 0,
        }

        if map_stats["player"] == 1:  # and map_stats["regions"] == 1:
            # NOTE: super whack, just taking random player. The RL agent may learn some weird bias about this but the alternatives seem worse.
            p_x, p_y = map_locations["player"][0]
            enemies = []
            enemies.extend(map_locations["spider"])
            enemies.extend(map_locations["bat"])
            enemies.extend(map_locations["scorpion"])
            # Added this bit
            UPPER_DIST = self._width * self._height * 100

            if len(enemies) > 0:
                dikjstra, _ = run_dikjstra(
                    p_x,
                    p_y,
                    map,
                    ["empty", "player", "key", "bat", "spider", "scorpion"],
                )
                min_dist = UPPER_DIST

                for e_x, e_y in enemies:
                    if dikjstra[e_y][e_x] > 0 and dikjstra[e_y][e_x] < min_dist:
                        min_dist = dikjstra[e_y][e_x]

                if min_dist == UPPER_DIST:
                    # And this
                    min_dist = 0
                map_stats["nearest-enemy"] = min_dist

            if map_stats["key"] == 1 and map_stats["door"] == 1:
                k_x, k_y = map_locations["key"][0]
                d_x, d_y = map_locations["door"][0]
                dikjstra_k, _ = run_dikjstra(
                    p_x,
                    p_y,
                    map,
                    ["empty", "key", "player", "bat", "spider", "scorpion"],
                )
                map_stats["path-length"] += dikjstra_k[k_y][k_x]
                dikjstra_d, _ = run_dikjstra(
                    k_x,
                    k_y,
                    map,
                    ["empty", "player", "key", "door", "bat", "spider", "scorpion"],
                )
                map_stats["path-length"] += dikjstra_d[d_y][d_x]

                if self.render_path and map_stats["regions"] == 1:
                    self.path = np.vstack((get_path_coords(dikjstra_k, init_coords=(k_y, k_x))[1:-1],
                        get_path_coords(dikjstra_d, init_coords=(d_y, d_x))[1:-1]))
                    front_tiles = set(((k_x, k_y), (d_x, d_y), (p_x, p_y)))
                    i = 0
                    render_path = self.path.copy()
                    # slice out any tiles that need to be visualized "in front of" the path (then trim the path as needed)
                    for (x, y) in self.path:
                        if (x, y) in front_tiles:
                            continue
                        render_path[i] = [x, y]
                        i += 1
                    self.path = render_path[:i]
        self.path_length = map_stats['path-length']

        return map_stats
