#! /usr/bin/env python3.8
"""
Created on 23 Dec 2022

@author: Kin ZHANG (kin_eng@163.com)
% Copyright (C) 2022, RPL, KTH Royal Institute of Technology

Part of codes also refers: 
1. https://github.com/kwea123/ROS_notes
2. https://github.com/seaside2mm/sharecode

"""

import rospy
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
import numpy as np
from global_def import *
from visualize_utils import *

class Draw3DBox:
    def __init__(self, box3d_pub, marker_frame_id = 'velodyne', rate=10):
        self.frame_id = marker_frame_id
        self.lifetime = 1.0/rate
        self.box3d_pub = box3d_pub

    def set_frame_id(self, marker_frame_id):
        self.frame_id = marker_frame_id

    def publish_3dbox(self, dt_box_lidar, track_ids, types=None, publish_id=True, move_lidar_center=20):
        """
        Publish 3d boxes in velodyne coordinate, with color specified by object_types
        If object_types is None, set all color to cyan
        corners_3d_velos : list of (8, 4) 3d corners
        """
        # (N, 8, 3)
        # -move_lidar_center
        dt_box_lidar[:,0] = dt_box_lidar[:,0]-move_lidar_center
        corners_3d_velos = boxes_to_corners_3d(dt_box_lidar)

        marker_array = MarkerArray()

        for i, corners_3d_velo in enumerate(corners_3d_velos):
            # 3d box
            marker = Marker()
            marker.header.frame_id = self.frame_id
            marker.header.stamp = rospy.Time.now()
            marker.id = i
            marker.action = Marker.ADD
            marker.lifetime = rospy.Duration(self.lifetime)
            marker.type = Marker.LINE_LIST

            b, g, r = DETECTION_COLOR_MAP[types[i]]
            if types is None:
                marker.color.r = 0.0
                marker.color.g = 1.0
                marker.color.b = 1.0
            else:
                marker.color.r = r/255.0
                marker.color.g = g/255.0
                marker.color.b = b/255.0
            marker.color.a = 1.0
            marker.scale.x = 0.1

            marker.points = []
            for l in LINES:
                p1 = corners_3d_velo[l[0]]
                marker.points.append(Point(p1[0], p1[1], p1[2]))
                p2 = corners_3d_velo[l[1]]
                marker.points.append(Point(p2[0], p2[1], p2[2]))
            marker_array.markers.append(marker)

            # add track id
            if publish_id and track_ids != -1:
                track_id = track_ids[i]
                text_marker = Marker()
                text_marker.header.frame_id = self.frame_id
                text_marker.header.stamp = rospy.Time.now()

                text_marker.id = track_id + 1000
                text_marker.action = Marker.ADD
                text_marker.lifetime = rospy.Duration(self.lifetime)
                text_marker.type = Marker.TEXT_VIEW_FACING

                p4 = corners_3d_velo[4] # upper front left corner

                text_marker.pose.position.x = p4[0]
                text_marker.pose.position.y = p4[1]
                text_marker.pose.position.z = p4[2] + 0.5

                text_marker.text = str(track_id)

                text_marker.scale.x = 1
                text_marker.scale.y = 1
                text_marker.scale.z = 1

                if types is None:
                    text_marker.color.r = 0.0
                    text_marker.color.g = 1.0
                    text_marker.color.b = 1.0
                else:
                    b, g, r = DETECTION_COLOR_MAP[types[i]]
                    text_marker.color.r = r/255.0
                    text_marker.color.g = g/255.0
                    text_marker.color.b = b/255.0
                text_marker.color.a = 1.0
                marker_array.markers.append(text_marker)

        self.box3d_pub.publish(marker_array)

    def compute_3d_box_cam2(self, h, w, l, x, y, z, yaw):
        """
        Return : 3xn in cam2 coordinate
        """
        R = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
        x_corners = [l/2,l/2,-l/2,-l/2,l/2,l/2,-l/2,-l/2]
        y_corners = [0,0,0,0,-h,-h,-h,-h]
        z_corners = [w/2,-w/2,-w/2,w/2,w/2,-w/2,-w/2,w/2]
        corners_3d_cam2 = np.dot(R, np.vstack([x_corners,y_corners,z_corners]))
        corners_3d_cam2[0,:] += x
        corners_3d_cam2[1,:] += y
        corners_3d_cam2[2,:] += z
        return corners_3d_cam2
