#!/usr/bin/env python3

import asyncio
import math
import time
import datetime
import cozmo
from cozmo.util import degrees, distance_mm, Pose, speed_mmps

def detect_face_pose(robot: cozmo.robot.Robot, timeout=30.0, name="sheena"):
    lookaround = robot.start_behavior(cozmo.behavior.BehaviorTypes.FindFaces)
    is_face_detected = False
    face_position = None
    sleep_rate = 4
    expected_final_time = time.time() + timeout
    detected_face = None
    while not is_face_detected:
        try:
            visible_face_list = robot.world.visible_faces
            for visible_face in visible_face_list:
                if visible_face.name.lower() == name:
                    is_face_detected = True
                    detected_face = visible_face
                    face_pos = visible_face.pose
                    robot_position = robot.pose
                    r_x, r_y = robot_position.position.x, robot_position.position.y
                    f_x, f_y = face_pos.position.x, face_pos.position.y
                    distance = math.sqrt((f_x - r_x)**2 + (f_y - r_y)**2)
                    new_x = f_x - (250 * (f_x - r_x) / distance)
                    new_y = f_y - (250 * (f_y - r_y) / distance)
                    face_position = Pose(x=new_x, y=new_y, z=0, angle_z=robot_position.rotation.angle_z, origin_id=face_pos.origin_id)
            time.sleep(1.0 / sleep_rate)
        except Exception:
            continue

        if time.time() > expected_final_time:
            break
    lookaround.stop()
    if is_face_detected:
        robot.turn_towards_face(detected_face, num_retries=3).wait_for_completed()
    return face_position, detected_face


def detect_cubes(robot: cozmo.robot.Robot):
    lookaround = robot.start_behavior(cozmo.behavior.BehaviorTypes.LookAroundInPlace)
    cubes = None
    try:
        cubes = robot.world.wait_until_observe_num_objects(num=3, object_type=cozmo.objects.LightCube, timeout=60)
    except asyncio.TimeoutError:
        return None
    lookaround.stop()
    return cubes

def react_robot_tap_cube(robot:cozmo.robot.Robot, cube:cozmo.objects.LightCube, error_text):
    while True:
        try:
            cube.wait_for_tap(timeout=10)
            break
        except asyncio.TimeoutError:
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabFrustrated, use_lift_safe=True, ignore_body_track=True).wait_for_completed()
            robot.say_text(error_text).wait_for_completed()
        
