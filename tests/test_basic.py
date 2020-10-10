import networkx as nx
import unittest

from simulation.simulation_multi_agent import Multi_Agent_Simulation


distance = 500

distances = [
    [0,distance,distance],
    [distance,0,distance],
    [distance,distance,0]
]

class SimulationSetupAndRunTestSuite(unittest.TestCase):
    def setUp(self):
        self.simu = Multi_Agent_Simulation(100, 50, 2, 0.1, 1, "weighted", _printing=True)

    def tearDown(self):
        pass
        #self.simu.dispose()
        #self.simu = None

    def test_simulation_setup(self):
        self.simu.setup()
        # Test to be written
        pass

    def test_simulation_run(self):
        self.simu.setup()
        self.simu.run()
        # Test to be written
        pass

class AfterSimulationWeightedRandomWalkTestSuite(unittest.TestCase):
    def setUp(self):
        self.simu = Multi_Agent_Simulation(100, 50, 2, 0.1, 1, "weighted", _printing=True)
        self.simu.setup()
        self.simu.run()

    def tearDown(self):
        pass
        #self.simu.dispose()
        #self.simu = None

    def test_calculation_cum_weight(self):
        pass

    def test_calculation_exit_probabilities(self):
        for agent in self.simu.agents:
            self.assertAlmostEqual(sum(tip.exit_probability_multiple_agents[agent] for tip in agent.tips), 1)


if __name__ == '__main__':
    unittest.main()