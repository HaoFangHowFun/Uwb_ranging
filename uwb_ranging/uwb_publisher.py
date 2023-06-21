# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node

from cslam_common_interfaces.msg import Uwbranging
import logging
import sys
import time
from threading import Event

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.crazyflie.syncLogger import SyncLogger
#uri = 'radio://0/60/250K/E7E7E7E701'
uri =  'usb://0'
# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)
cflib.crtp.init_drivers(enable_debug_driver=False)

class MinimalPublisher(Node):

    def __init__(self):

        self.lg_twr = LogConfig(name='twr', period_in_ms=50)
        self.lg_twr.add_variable('ranging.distance0', 'float')
        self.lg_twr.add_variable('ranging.distance1', 'float')
        self.lg_twr.add_variable('ranging.distance2', 'float')
        self.lg_twr.data_received_cb.add_callback(self.twr_log)
        self.scf = SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache'))
        self.scf.open_link()
        self.scf.cf.log.add_config(self.lg_twr)
        self.lg_twr.start()
        self.ranging0 =None
        self.ranging1 =None
        self.ranging2 =None
        self.measureoffset= 0.34
        self.robot_0_0_height = 0
        self.robot_0_1_height = 0
        self.robot_0_2_height = 0
        
        super().__init__('uwb_publisher')
        self.publisher_ = self.create_publisher(Uwbranging, '/cslam/Uwbranging', 10)
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
    def twr_log(self, timestamp, data, logconf):
        self.ranging0 = ((data['ranging.distance0'] + self.measureoffset)**2-self.robot_0_0_height**2)**0.5
        self.ranging1 = ((data['ranging.distance1'] + self.measureoffset)**2-self.robot_0_1_height**2)**0.5
        self.ranging2 = ((data['ranging.distance2'] + self.measureoffset)**2-self.robot_0_2_height**2)**0.5
        #print('[%d][%s]: %s' % (timestamp, logconf, data))
    def timer_callback(self):
        msg = Uwbranging()
        msg.distance = self.ranging1
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.distance)
        self.i += 1


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
