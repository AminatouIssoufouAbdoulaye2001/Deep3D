import numpy as np
import pandas as pd
import tensorflow as tf
import scipy
from tensorflow.python.framework.ops import disable_eager_execution
disable_eager_execution()


# Deep Q Network off-policy
class DeepQNetwork:

    def __init__(
        self,
        n_actions,
        n_features,
        learning_rate = 0.001,
        reward_decay = 0.99,
        e_greedy = 0.9,
        replace_target_iter = 300,
        memory_size = 500,
        batch_size = 32,
        e_greedy_increment = None,
        output_graph = False):

        # Store hyperparameters
        self.n_actions = n_actions
        self.n_features = n_features
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon_max = e_greedy
        self.replace_target_iter = replace_target_iter
        self.memory_size = memory_size
        self.batch_size = batch_size
        self.epsilon_increment = e_greedy_increment
        self.epsilon = self.epsilon_max if e_greedy_increment is None else 0.0
        self.save_file = './weights/model.ckpt'

        # Initialize learning step counter
        self.learn_step_counter = 0

        # Initialize memory [s, a, r, s_]
        self.memory = np.zeros((self.memory_size, n_features * 2 + 2))

        # Build evaluation and target networks
        self._build_net()

        # Replace target network with evaluation network every replace_target_iter steps
        t_params = tf.compat.v1.get_collection('target_net_params')
        e_params = tf.compat.v1.get_collection('eval_net_params')
        self.replace_target_op = [tf.compat.v1.assign(t, e) for t, e in zip(t_params, e_params)]

        # Set up session with GPU options
        config = tf.compat.v1.ConfigProto(log_device_placement = False, allow_soft_placement = True)
        config.gpu_options.per_process_gpu_memory_fraction = 0.6
        self.sess = tf.compat.v1.Session(config = config)

        # Optionally write graph to tensorboard
        if output_graph:
            writer = tf.compat.v1.summary.FileWriter("logs/", self.sess.graph)
            writer.close()

        # Initialize variables
        self.sess.run(tf.compat.v1.global_variables_initializer())

        # Initialize cost history
        self.cost_his = []


    def _build_net(self):
    # ------------------ build evaluate_net ------------------
        self.s = tf.keras.Input(shape = (self.n_features,))
        self.q_target = tf.keras.Input(shape = (self.n_actions,))
        x = tf.keras.layers.Dense(100, activation = 'relu')(self.s)
        self.q_eval = tf.keras.layers.Dense(self.n_actions)(x)

        with tf.compat.v1.variable_scope('loss'):
            tf.compat.v1.disable_eager_execution()
            self.loss = tf.math.reduce_mean(tf.compat.v1.squared_difference(self.q_target, self.q_eval))
            # self.loss = tf.math.reduce_mean(tf.math.squared_difference(self.q_target, self.q_eval))
        with tf.compat.v1.variable_scope('train'):
            optimizer = tf.compat.v1.train.AdamOptimizer(self.lr)
            self._train_op = optimizer.minimize(self.loss)

        # ------------------ build target_net ------------------
        self.s_ = tf.keras.Input(shape = (self.n_features,))
        c_names = ['target_net_params', tf.compat.v1.GraphKeys.GLOBAL_VARIABLES]

        x = tf.keras.layers.Dense(100, activation = 'relu')(self.s_)
        self.q_next = tf.keras.layers.Dense(self.n_actions)(x)

        self.target_net_params = tf.compat.v1.get_collection(tf.compat.v1.GraphKeys.GLOBAL_VARIABLES, scope = 'target_net')


    def store_transition(self, s, a, r, s_):
        if not hasattr(self, 'memory_counter'):
            self.memory_counter = 0
        
        s = np.array(s).flatten()  # applatit l'observation s
        s_ = np.array(s_).flatten()  # applatit la nouvelle observation s_
        transition = np.hstack((s, [a, r], s_))  # crée une transition avec les données

        # remplace l'ancienne mémoire par la nouvelle mémoire
        index = self.memory_counter % self.memory_size
        self.memory[index, :] = transition

        self.memory_counter += 1


    def choose_action(self, observation):
        # Pour avoir une dimension de lot lors de l'alimentation de la placeholder tf
        observation = observation[np.newaxis, :]

        # Si le nombre aléatoire est inférieur à epsilon, choisissez l'action qui maximise Q
        if np.random.uniform() < self.epsilon:
            # Effectuez une propagation avant de l'observation et obtenez la valeur Q pour chaque action
            actions_value = self.sess.run(self.q_eval, feed_dict={self.s: observation})
            action = np.argmax(actions_value)
        else:
            # Sinon, choisissez une action aléatoire
            action = np.random.randint(0, self.n_actions)
        return action
    
    
    def learn(self):
        if not hasattr(self, 'memory_counter'):
            self.memory_counter = 0
        # check to replace target parameters
        if self.learn_step_counter % self.replace_target_iter == 0:
            self.sess.run(self.replace_target_op)
            #print('\ntarget_params_replaced\n')

        # sample batch memory from all memory
        if self.memory_counter > self.memory_size:
            sample_index = np.random.choice(self.memory_size, size=self.batch_size, replace=False)
        else:
            sample_index = np.random.choice(self.memory_counter, size=self.batch_size, replace=False)
        batch_memory = self.memory[sample_index, :]

        # get q_next and q_eval
        q_next, q_eval = self.sess.run([self.q_next, self.q_eval], feed_dict={self.s_: batch_memory[:, -self.n_features:], self.s: batch_memory[:, :self.n_features]})

        # calculate q_target
        q_target = q_eval.copy()
        batch_index = np.arange(self.batch_size, dtype=np.int32)
        eval_act_index = batch_memory[:, self.n_features].astype(int)
        reward = batch_memory[:, self.n_features + 1]
        q_target[batch_index, eval_act_index] = reward + self.gamma * np.max(q_next, axis=1)

        # train eval network
        _, self.cost = self.sess.run([self._train_op, self.loss], feed_dict={self.s: batch_memory[:, :self.n_features], self.q_target: q_target})
        self.cost_his.append(self.cost)

        # increase epsilon
        self.epsilon = min(self.epsilon_max, self.epsilon + self.epsilon_increment)

        # increment learn_step_counter
        self.learn_step_counter += 1

    def plot_cost(self):
        import matplotlib.pyplot as plt
        plt.plot(np.arange(len(self.cost_his)), self.cost_his)
        plt.ylabel('Cost')
        plt.xlabel('training steps')
        plt.savefig('save/cost.png')
        plt.show()

    def store(self):
        saver = tf.compat.v1.train.Saver() 
        saver.save(self.sess, self.save_file)
    
    def restore(self):
        saver = tf.compat.v1.train.Saver() 
        saver.restore(self.sess, self.save_file)



