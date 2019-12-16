from geometry_msgs.msg import Twist
import copy
import numpy as np

import rospy

from simulations_messages.msg import Vector3f

from ddpg_implementation import ddpg_agent

from tf.transformations import euler_from_quaternion, quaternion_from_euler
from ireinforcement_learning_sterring_algorithm import IReinforcementLearningSteeringAlgorithm


class PendulumSteering(IReinforcementLearningSteeringAlgorithm):

    def __init__(self):
        IReinforcementLearningSteeringAlgorithm.__init__(self)
        self.steering_msg = Vector3f()
        self.last_state = np.zeros(6, dtype=np.float32)
        self.controller = ddpg_agent.Agent(6, 1, 0)

    def get_steering_msg(self):
        force = Vector3f()
        force.x = self.steering_msg.x
        return force

    def steer(self, state_msg, reward, terminate):
        current_state = PendulumSteering.get_network_input(state_msg)
        action = self.controller.act(current_state)
        PendulumSteering.log_action(action)
        self.update_steering_msg(action)
        self.step(action, reward, current_state, terminate)
        self.prepare_next_episode(terminate, current_state)
        return self.get_steering_msg()

    def reset_simulation(self):
        self.start = True
        self.last_state = np.zeros(6, dtype=np.float32)

    def step(self, action, reward, current_state, terminate):
        if self.start:
            self.start = False
        else:
            self.controller.step(copy.deepcopy(self.last_state), action, np.array(reward.last_reward, dtype=np.float32),
                                 current_state, np.bool(terminate))

    @staticmethod
    def get_network_input(state_msg):
        cart_state = state_msg.cart_state.pose.position.x
        cart_vel = state_msg.cart_state.linear_vel.x
        cart_accel = state_msg.cart_state.linear_accel.x
        angle = PendulumSteering.get_angle(state_msg)
        fp_vel = state_msg.first_pole.angular_vel.x
        fp_accel = state_msg.first_pole.angular_accel.x
        return np.array((cart_state,
                         cart_vel,
                         cart_accel,
                         angle,
                         fp_vel,
                         fp_accel
                         ), dtype=np.float32)

    def update_steering_msg(self, action):
        self.steering_msg.x = action

    @staticmethod
    def get_angle(state_msg):

        angle = PendulumSteering.get_rpy_from_quaternion(
            state_msg.first_pole.pose.rotation)[0]

        rospy.logdebug("first pole pitch angle: %f", angle,
                       logger_name="double_pendulum_reward_function")

        return angle

    @staticmethod
    def get_rpy_from_quaternion(quaternion):
        return euler_from_quaternion([quaternion.x, quaternion.y, quaternion.z, quaternion.w])

    @staticmethod
    def log_action(action):
        rospy.logdebug("action x: %f", action,
                       logger_name="double_pendulum_rl")
