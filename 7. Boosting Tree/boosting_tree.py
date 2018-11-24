import numpy as np
import random as rd
from math import log, exp
from sklearn.datasets import load_wine
from decision_tree import DecisionTree


class BoostingTree:
    def __init__(self, input_dim, tree_num, maximal_depth, minimal_samples, criterion):
        # basic classifier information
        self._input_dim = input_dim
        self._tree_num = tree_num
        self._maximal_depth = maximal_depth
        self._minimal_samples = minimal_samples
        self._criterion = criterion

        # define the list of weak trees
        self._weak_trees = []

    def train(self, x, y):
        # initialize the weights uniformly
        sample_weights = np.ones(len(x)) / len(x)

        while len(self._weak_trees) < self._tree_num:
            # define weak learner
            weak_learner = dict()
            weak_learner['weight'] = None
            weak_learner['model'] = DecisionTree(input_dim=self._input_dim, maximal_depth=self._maximal_depth,
                                                 minimal_samples=self._minimal_samples, criterion=self._criterion)

            # sample(with replacement) training data-set with respect to sample_weights
            sample_index = np.zeros(len(x))
            for counter in range(len(x)):
                pointer = rd.uniform(0, 1)
                accumulated_prob = 0
                for index, w in enumerate(sample_weights):
                    accumulated_prob += w
                    if pointer <= accumulated_prob:
                        sample_index[counter] = index
                    else:
                        continue
            x_sampled, y_sampled = x[sample_index], y[sample_index]

            # train the weak learner
            weak_learner.train(x_sampled, y_sampled)

            # calculate the weak learner's weight
            acc, error, correct_samples_index, mistake_samples_index = weak_learner.evaluate(x_sampled, y_sampled)
            weak_learner['weight'] = 0.5 * log((1 - error) / error)

            # update the sample weights
            # step1: increase the weights of mistaken samples;
            # step2: decrease the weights of correct samples;
            # step3: normalize the distribution
            for i in correct_samples_index:
                sample_weights[sample_index[i]] * exp(-weak_learner['weight'])

            for i in mistake_samples_index:
                sample_weights[sample_index[i]] * exp(weak_learner['weight'])

            sample_weights = sample_weights / sum(sample_weights)

            # discard the weak learners
            if error < 0.5:
                self._weak_trees.append(weak_learner)
            else:
                continue

    def predict(self, x):
        # each tree conducts the inference process independently
        y_vote = np.zeros((self._tree_num, len(x)))
        for index, tree in enumerate(self._weak_trees):
            y_vote[index] = tree['model'].predict(x)

        # voting with respect to the model weights
        y_predicted = np.zeros(len(x))
        for i in range(len(y_predicted)):
            vote_dict = dict()
            for t in range(self._tree_num):
                if y_vote[t][i] in vote_dict:
                    vote_dict[y_vote[t][i]] += self._weak_trees[t]['weight']
                else:
                    vote_dict[y_vote[t][i]] = self._weak_trees[t]['weight']

            y_predicted[i] = max(vote_dict, key=vote_dict.get)

        return y_predicted

    def evaluate(self, x, y):
        y_predict = self.predict(x)
        correct_num = 0
        for i in range(len(y)):
            if y[i] == y_predict[i]:
                correct_num += 1
            else:
                continue
        accuracy = correct_num / len(y)
        return accuracy


if __name__ == '__main__':
    # load wine data
    # each sample has 13 features and 3 possible classes
    wine = load_wine()
    wine_x = wine['data']
    wine_y = wine['target']

    # shuffle the data randomly
    random_idx = rd.sample([i for i in range(len(wine_x))], len(wine_x))
    wine_x = wine_x[random_idx]
    wine_y = wine_y[random_idx]

    # split the data into training data set and testing data set
    train_rate = 0.4
    train_num = int(train_rate*len(wine_x))
    train_x = wine_x[:train_num]
    train_y = wine_y[:train_num]
    test_x = wine_x[train_num:]
    test_y = wine_y[train_num:]

    # compare the performances of random forest and decision tree
    bt = BoostingTree(input_dim=len(train_x[0]), tree_num=100, maximal_depth=2, minimal_samples=5, criterion='gini')
    dt = DecisionTree(input_dim=len(train_x[0]), maximal_depth=10, minimal_samples=5, criterion='gini')
    bt.train(train_x, train_y)
    dt.train(train_x, train_y)
    print('Boosting Tree Accuracy: ' + str(bt.evaluate(test_x, test_y)))
    print('Decision Tree Accuracy: ' + str(dt.evaluate(test_x, test_y)))

