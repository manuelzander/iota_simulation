import sys
import timeit
import random
import math
from collections import Counter
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from simulation.helpers import update_progress, create_distance_matrix, \
common_elements, clamp, load_file
from simulation.plotting import print_info, print_graph, print_tips_over_time, \
print_tips_over_time_multiple_agents, print_tips_over_time_multiple_agents_with_tangle, \
print_attachment_probabilities_alone,print_attachment_probabilities_all_agents
from simulation.agent import Agent
from simulation.transaction import Transaction


class Multi_Agent_Simulation:
    def __init__(self, _no_of_transactions, _lambda, _no_of_agents, \
                 _alpha, _distance, _tip_selection_algo, _latency = 1, \
                 _agent_choice=None, _printing=False):

        #Use configuration file when provided
        if(len(sys.argv) != 1):
            self.config = load_file(sys.argv[1])
            self.no_of_transactions = self.config[0][0]
            self.lam = self.config[0][1]
            self.no_of_agents = self.config[0][2]
            self.alpha = self.config[0][3]
            self.latency = self.config[0][4]
            self.distances = self.config[0][5]
            self.tip_selection_algo = self.config[0][6]
            self.agent_choice = self.config[0][7]
            self.printing = self.config[0][8]
        #Otherwise use the provided parameters
        else:
            self.no_of_transactions = _no_of_transactions
            self.lam = _lambda
            self.no_of_agents = _no_of_agents
            self.alpha = _alpha
            self.latency = _latency
            if (type(_distance) is float or type(_distance) is int):
                self.distances = create_distance_matrix(self.no_of_agents, _distance)
            else:
                self.distances = _distance
            self.tip_selection_algo = _tip_selection_algo
            if _agent_choice is None:
                _agent_choice = list(np.ones(self.no_of_agents)/self.no_of_agents)
            self.agent_choice = _agent_choice
            self.printing = _printing

        #Basic parameter checks
        if (round(sum(self.agent_choice), 3) != 1.0):
            print("Agent choice not summing to 1.0: {}".format(sum(self.agent_choice)))
            sys.exit(1)
        if (len(self.agent_choice) != self.no_of_agents):
            print("Agent choice not matching no_of_agents: {}".format(len(self.agent_choice)))
            sys.exit(1)
        if (self.no_of_agents == 1):
            print("ERROR:  Use a Single_Agent_Simulation()")
            sys.exit()

        self.transactions = []
        self.agents = []
        self.arrival_times = []
        self.not_visible_transactions = []

        #For analysis only
        self.record_tips = []
        self.record_attachment_probabilities = []

        #For max. four agents always the same colors in prints
        self.agent_colors = ['#a8d6ff', '#ff9494', '#dcc0dd', '#e0ff80']
        self.agent_tip_colors = ['#f5faff', '#ffe0e0', '#f8f2f8', '#f9ffe6']

        #For more than four agents random colors and lighter tip colors
        for i in range(self.no_of_agents-4):
            r = lambda: random.randint(0,255)
            color = '#{:02x}{:02x}{:02x}'.format(r(), r(), r())
            self.agent_colors.append(color)
            self.agent_tip_colors.append(color)


    #############################################################################
    # SIMULATION: SETUP
    #############################################################################


    def setup(self):

        #Create agents
        agent_counter = 0
        for agent in range(self.no_of_agents):
            self.agents.append(Agent(agent_counter))
            agent_counter += 1

        #Create directed graph object
        self.DG = nx.DiGraph()

        #Create random arrival times
        inter_arrival_times = np.random.exponential(1 / self.lam, self.no_of_transactions)
        self.arrival_times = list(np.cumsum(inter_arrival_times))

        #Create genesis transaction object, store in list and add to graph object
        transaction_counter = 0
        self.transactions.append(Transaction(0, transaction_counter))
        self.DG.add_node(self.transactions[0], pos=(0, 0), no=transaction_counter, node_color='#99ffff')

        transaction_counter += 1

        #Create other transaction objects and store in list
        for i in range(len(self.arrival_times)):
            self.transactions.append(Transaction(self.arrival_times[i], transaction_counter))
            transaction_counter += 1


    #############################################################################
    # SIMULATION: MAIN LOOP
    #############################################################################


    def run(self):

        start_time = timeit.default_timer()

        if self.printing:
            print_info(self)

        #Create dictionary with simulation parameter changes when provided
        if(len(sys.argv) != 1):
            dic = {x[0]: x[1:] for x in self.config[1:]}

        #Start with first transaction (NOT genesis)
        for transaction in self.transactions[1:]:

            #Execute simulation parameter changes when provided
            if(len(sys.argv) != 1):
                self.check_parameters_changes(transaction, dic)

            #Do something every 100th transition
            if (transaction.id >= 0 and
                transaction.id % 100 == 0):
                self.record_attachment_probabilities.append((transaction.id,self.calc_attachment_probabilities(transaction)))
                # self.record_attachment_probabilities.append(self.calc_attachment_probabilities(transaction))

            #Choose an agent
            transaction.agent = np.random.choice(self.agents, p=self.agent_choice)

            #Add transaction to directed graph object (with random y coordinate for plotting the graph)
            self.DG.add_node(transaction,pos=(transaction.arrival_time, \
                random.uniform(0, 1)-transaction.agent.id*1.3), \
                node_color=self.agent_colors[transaction.agent.id])

            #Select tips
            self.tip_selection(transaction)

            #Update weights (of transactions referenced by the current transaction)
            if(self.tip_selection_algo == "weighted"):
                self.update_weights_multiple_agents(transaction)

            #Progress bar update
            if self.printing:
                update_progress(transaction.id/self.no_of_transactions, transaction)

        if self.printing:
            print("Simulation time: " + str(np.round(timeit.default_timer() - start_time, 3)) + " seconds\n")

        #For measuring partitioning
        start_time2 = timeit.default_timer()
        # self.calc_exit_probabilities_multiple_agents(transaction)
        # self.calc_attachment_probabilities(transaction)
        # self.calc_confirmation_confidence_multiple_agents(transaction)

        if self.printing:
            print("Calculation time further measures: " + str(np.round(timeit.default_timer() - start_time2, 3)) + " seconds\n")
            # print("\nGraph information:\n" + nx.info(self.DG))


    def tip_selection(self, transaction):

        if(self.tip_selection_algo == "random"):
            self.random_selection(transaction)
        elif (self.tip_selection_algo == "unweighted"):
            self.unweighted_MCMC(transaction)
        elif(self.tip_selection_algo == "weighted"):
            self.weighted_MCMC(transaction)
        else:
            print("ERROR:  Valid tip selection algorithms are 'random', 'weighted', 'unweighted'")
            sys.exit()


    def check_parameters_changes(self, transaction, parameters):

        #If change event for a transaction is provided
        if transaction.id in parameters:
            #If change of distance is provided
            if parameters[transaction.id][0] != False:
                self.distances = parameters[transaction.id][0]
            #If change of agent probabilities is provided
            if parameters[transaction.id][1] != False:
                self.agent_choice = parameters[transaction.id][1]


    #############################################################################
    # SIMULATION: HELPERS
    #############################################################################


    def get_tips(self):

        tips = []
        for transaction in self.DG.nodes:
            if (len(list(self.DG.predecessors(transaction))) == 0):
                tips.append(transaction)

        return tips


    def get_visible_transactions(self, incoming_transaction_time, incoming_transaction_agent):

        #Initialize empty lists (for each transaction these are populated again)
        self.not_visible_transactions = []
        for agent in self.agents:
            agent.visible_transactions = []

        #Loop through all transactions in DAG
        for transaction in self.DG.nodes:

            #For EACH agent record the currently visible and not visible transactions
            for agent in self.agents:

                #Genesis always visible
                if (transaction.arrival_time == 0):

                    agent.visible_transactions.append(transaction)

                else:
                    #Get distance from agent to agent of transaction from distance matrix
                    distance = self.distances[agent.id][transaction.agent.id]

                    #Determine if the transaction is visible (incoming_transaction.arrival_time determines current time)
                    if (transaction.arrival_time + self.latency + distance <= incoming_transaction_time):

                        agent.visible_transactions.append(transaction)

                    #Record not visible transactions for 'current agent' only (reduces overhead)
                    elif(incoming_transaction_agent == agent):
                        self.not_visible_transactions.append(transaction)


    def get_valid_tips_multiple_agents(self, agent):

        valid_tips = []

        for transaction in agent.visible_transactions:

            #Add to valid tips if transaction has no approvers at all
            if(len(list(self.DG.predecessors(transaction))) == 0):

                valid_tips.append(transaction)

            #Add to valid tips if all approvers not visible yet
            elif(self.all_approvers_not_visible(transaction)):

                valid_tips.append(transaction)

        return valid_tips


    def all_approvers_not_visible(self, transaction):
        return set(list(self.DG.predecessors(transaction))).issubset(set(self.not_visible_transactions))


    def calc_transition_probabilities_multiple_agents(self, approvers, agent):

        weights = [approver.cum_weight_multiple_agents[agent] for approver in approvers]
        normalized_weights = [weight - max(weights) for weight in weights]

        denominator_transition_probabilities = sum([math.exp(self.alpha * weight) \
        for weight in normalized_weights])

        return [math.exp(self.alpha * (approver.cum_weight_multiple_agents[agent] \
                - max(weights))) / denominator_transition_probabilities \
                for approver in approvers]


    #############################################################################
    # TIP-SELECTION: RANDOM
    #############################################################################


    def random_selection(self, transaction):

        #Needed for plotting number of tips over time for ALL agents
        for agent in self.agents:
            if(agent != transaction.agent):
                self.get_visible_transactions(transaction.arrival_time, agent)
                valid_tips = self.get_valid_tips_multiple_agents(agent)
                agent.record_tips.append(valid_tips)

        #Get visible transactions and valid tips (and record these)
        self.get_visible_transactions(transaction.arrival_time, transaction.agent)
        valid_tips = self.get_valid_tips_multiple_agents(transaction.agent)
        transaction.agent.record_tips.append(valid_tips)
        self.record_tips.append(valid_tips)

        #Reference two random valid tips
        tip1 = np.random.choice(valid_tips)
        tip2 = np.random.choice(valid_tips)

        self.DG.add_edge(transaction, tip1)
        if (tip1 != tip2):
            self.DG.add_edge(transaction, tip2)


    #############################################################################
    # TIP-SELECTION: UNWEIGHTED
    #############################################################################


    def unweighted_MCMC(self, transaction):

        #Needed for plotting number of tips over time for ALL agents
        for agent in self.agents:
            if(agent != transaction.agent):
                self.get_visible_transactions(transaction.arrival_time, agent)
                valid_tips = self.get_valid_tips_multiple_agents(agent)
                agent.record_tips.append(valid_tips)

        #Get visible transactions and valid tips (and record these)
        self.get_visible_transactions(transaction.arrival_time, transaction.agent)
        valid_tips = self.get_valid_tips_multiple_agents(transaction.agent)
        transaction.agent.record_tips.append(valid_tips)
        self.record_tips.append(valid_tips)

        #Walk to two tips
        tip1 = self.unweighted_random_walk(transaction, valid_tips)
        tip2 = self.unweighted_random_walk(transaction, valid_tips)

        #Add tips to graph (only once)
        self.DG.add_edge(transaction,tip1)
        if(tip1 != tip2):
            self.DG.add_edge(transaction,tip2)


    def unweighted_random_walk(self, transaction, valid_tips):

        #Start walk at genesis
        walker_on = self.transactions[0]

        #If only genesis a valid tip, approve genesis
        if (valid_tips == [walker_on]):
            return walker_on

        while (walker_on not in valid_tips):

            approvers = list(self.DG.predecessors(walker_on))
            visible_approvers = common_elements(approvers, transaction.agent.visible_transactions)

            walker_on = np.random.choice(visible_approvers)

        return walker_on


    #############################################################################
    # TIP-SELECTION: WEIGHTED
    #############################################################################


    def weighted_MCMC(self, transaction):

        #Needed for plotting number of tips over time for ALL agents
        for agent in self.agents:
            if(agent != transaction.agent):
                self.get_visible_transactions(transaction.arrival_time, agent)
                valid_tips = self.get_valid_tips_multiple_agents(agent)
                agent.record_tips.append(valid_tips)

        #Get visible transactions and valid tips (and record these)
        self.get_visible_transactions(transaction.arrival_time, transaction.agent)
        valid_tips = self.get_valid_tips_multiple_agents(transaction.agent)
        transaction.agent.record_tips.append(valid_tips)
        self.record_tips.append(valid_tips)

        #Walk to two tips
        tip1 = self.weighted_random_walk(transaction, valid_tips)
        tip2 = self.weighted_random_walk(transaction, valid_tips)

        #Add tips to graph (only once)
        self.DG.add_edge(transaction, tip1)
        if (tip1 != tip2):
            self.DG.add_edge(transaction, tip2)


    def weighted_random_walk(self, transaction, valid_tips):

        #Start walk at genesis
        walker_on = self.transactions[0]

        #If only genesis a valid tip, approve genesis
        if (valid_tips == [walker_on]):
            return walker_on

        while (walker_on not in valid_tips):

            approvers = list(self.DG.predecessors(walker_on))
            visible_approvers = common_elements(approvers, transaction.agent.visible_transactions)
            transition_probabilities = self.calc_transition_probabilities_multiple_agents(visible_approvers, transaction.agent)

            #Choose with transition probabilities
            walker_on = np.random.choice(visible_approvers, p=transition_probabilities)

        return walker_on


    #############################################################################
    # CONFIRMATION CONFIDENCE: MULTI AGENT
    #############################################################################


    def update_weights_multiple_agents(self, incoming_transaction):

        #Update all descendants of incoming_transaction only (cum_weight += 1)
        for transaction in nx.descendants(self.DG, incoming_transaction):

            #Update for each agent separately
            for agent in self.agents:
                if(transaction in agent.visible_transactions):
                    transaction.cum_weight_multiple_agents[agent] += 1


    def calc_exit_probabilities_multiple_agents(self, incoming_transaction):

        for agent in self.agents:

            #Reset exit probability of all transactions to 0%, just needed when run multiple times throughout simulation
            for transaction in self.DG.nodes:
                transaction.exit_probability_multiple_agents[agent] = 0

            #Set genesis to 100%
            self.transactions[0].exit_probability_multiple_agents[agent] = 1

            #Determine visible transaction for t + 1, so that all transactions (h = 1) are included
            self.get_visible_transactions(incoming_transaction.arrival_time + self.latency, agent)

        #Start at genesis, tips in the end
        sorted = list(reversed(list(nx.topological_sort(self.DG))))

        #Calculate exit probabilities
        for transaction in sorted:

            for agent in self.agents:

                if (transaction in agent.visible_transactions):

                    #Get visible direct approvers and transition probabilities to walk to them
                    approvers = list(self.DG.predecessors(transaction))
                    visible_approvers = common_elements(approvers, agent.visible_transactions)
                    transition_probabilities = self.calc_transition_probabilities_multiple_agents(visible_approvers, agent)

                    #For every visible direct approver update the exit probability by adding the exit probability
                    #of the current transaction times the transition probabilitiy of walking to the approver
                    for (approver, transition_probability) in zip(visible_approvers, transition_probabilities):
                        approver.exit_probability_multiple_agents[agent] += (
                                    transaction.exit_probability_multiple_agents[agent] * transition_probability)


    def calc_confirmation_confidence_multiple_agents(self, incoming_transaction):

        #Loop over agents and get visible transactions and valid tips
        for agent in self.agents:
            self.get_visible_transactions(incoming_transaction.arrival_time + self.latency, agent)
            agent.tips = self.get_valid_tips_multiple_agents(agent)

            #Loop over visible transactions
            for transaction in agent.visible_transactions:
                #Reset confirmation confidence to 0%, just needed when function called multiple times during simulation
                # transaction.confirmation_confidence_multiple_agents[agent] = 0

                #Loop over valid tips
                for tip in agent.tips:

                    if(nx.has_path(self.DG,tip,transaction) and tip != transaction):

                        transaction.confirmation_confidence_multiple_agents[agent] += tip.exit_probability_multiple_agents[agent]

                    #Tips have 0 confirmation confidence by default
                    tip.confirmation_confidence_multiple_agents[agent] = 0


    #Uses exit probabilities to caluclate attachment probabilities
    def calc_attachment_probabilities(self, incoming_transaction):

        attachment_probabilities_without_main = []
        attachment_probabilities_all = []

        self.calc_exit_probabilities_multiple_agents(incoming_transaction)

        for agent in self.agents:
            self.get_visible_transactions(incoming_transaction.arrival_time + self.latency, agent)
            agent.tips = self.get_valid_tips_multiple_agents(agent)

        for agent in self.agents:

            sum_ = 0
            sum_ = sum(tip.exit_probability_multiple_agents[agent] for tip in agent.tips if tip.agent == agent)

            for other_agent in self.agents:
                if(other_agent != agent):
                    sum_ += sum(tip.exit_probability_multiple_agents[other_agent] for tip in other_agent.tips if tip.agent == agent)

            attachment_probabilities_all.append(sum_/self.no_of_agents)

            if(agent != self.agents[0]):
                attachment_probabilities_without_main.append(sum_/self.no_of_agents)

        # print(attachment_probabilities_without_main)
        # print(attachment_probabilities_all)
        return attachment_probabilities_all

    #Performs 100 random walks per agent to caluclate attachment probabilities
    def attachment_probabilities_2(self, incoming_transaction):

        self.calc_exit_probabilities_multiple_agents(incoming_transaction)

        all_tips = []

        for agent in self.agents:

            #Get visible transactions and valid tips (and record these)
            self.get_visible_transactions(incoming_transaction.arrival_time + self.latency, agent)
            valid_tips = self.get_valid_tips_multiple_agents(agent)

            for i in range(100):
                tip = self.weighted_random_walk(incoming_transaction, valid_tips)
                all_tips.append(tip.agent)

        print(all_tips)
        c = Counter(all_tips)
        perc = [(i, c[i] / len(all_tips) * 100.0) for i in c]

        return perc
