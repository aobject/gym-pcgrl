from gym_pcgrl.envs.pcgrl_env import PcgrlEnv

class PcgrlCtrlEnv(PcgrlEnv):
    def __init__(self, prob="binary_ctrl", rep="narrow", **kwargs):
        super(PcgrlCtrlEnv, self).__init__(prob, rep, **kwargs)
        self.metrics = {}
        print('problem static trgs: {}'.format(self._prob.static_trgs))
        for k in {**self._prob.static_trgs}:
            self.metrics[k] = None
        print('env metrics: {}'.format(self.metrics))
        self.weights = self._prob.weights
        self.cond_bounds = self._prob.cond_bounds
        self.static_trgs = self._prob.static_trgs
        self.width = self._prob._width
        self._max_changes = max(int(1 * self._prob._width * self._prob._height), 1)

    def set_map(self, init_map):
        self._rep._random_start = False
        self._rep._old_map = init_map.copy()

    # FIXME: this isn't necessary right? Dictionary is the same yeah? ....yeah?

    def reset(self):
        obs = super().reset()
        self.metrics = self._rep_stats
        return obs

    def step(self, actions):
        ret = super().step(actions)
        self.metrics = self._rep_stats
        return ret
