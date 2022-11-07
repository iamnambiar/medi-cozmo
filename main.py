#!/usr/bin/env python

import sys
import time
import datetime
import cozmo
import fetch_calendar
import cozmo_functions

class Robot_Task():
    def __init__(self, user_name):
        self.medicine_cube_id = cozmo.objects.LightCube1Id
        self.party_cube_id = cozmo.objects.LightCube2Id
        self.water_cube_id = cozmo.objects.LightCube3Id
        # print(self.event_dict)
        self.user_name = user_name
    
    def robot_say_text(self, robot: cozmo.robot.Robot, speech_text):
        robot.say_text(speech_text, duration_scalar=0.7).wait_for_completed()

    def greet_user(self, robot: cozmo.robot.Robot):
        self.face_pose, self.detected_face = cozmo_functions.detect_face_pose(robot=robot, timeout=60, name=self.user_name)
        if self.detected_face is None:
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabBored, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
            self.robot_say_text(robot, "Hello {0}, Are you there? I can't find you.".format(self.user_name))
            self.face_pose, self.detected_face = cozmo_functions.detect_face_pose(robot=robot, timeout=30, name=self.user_name)
            if self.detected_face is None:
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabBored, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
                self.robot_say_text(robot, "I can't find you {0}. Please let me know if you are here.".format(self.user_name))
                return False
        
        robot.play_anim_trigger(cozmo.anim.Triggers.NamedFaceInitialGreeting, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
        robot.turn_towards_face(self.detected_face).wait_for_completed()
        greet_msg = ""
        time_now = time.localtime()
        if time_now.tm_hour < 12:
            greet_msg = "Good Morning {0}, Hope you had a good sleep.".format(self.user_name)
        elif time_now.tm_hour >= 12 and time_now.tm_hour <= 14:
            greet_msg = "Good Afternoon {0}".format(self.user_name)
        else:
            greet_msg = "Good Evening {0}, Hope you had a wonderful day today".format(self.user_name)
            
        self.robot_say_text(robot, greet_msg)
        return True
    
    def pickup_deliver_cube(self, robot: cozmo.robot.Robot, cube):
        robot.pickup_object(cube, num_retries=3).wait_for_completed()
        robot.go_to_pose(self.face_pose, relative_to_robot=False).wait_for_completed()
        robot.place_object_on_ground_here(cube, num_retries=3).wait_for_completed()

    def pick_medicine_based_on_time(self, robot: cozmo.robot.Robot, event, cubes_list):
        event_datetime_ts = event['start'].get('dateTime', event['start'].get('date'))
        event_datetime = datetime.datetime.fromisoformat(event_datetime_ts[0:-1])
        current_datetime = datetime.datetime.now()
        datetime_difference = current_datetime - event_datetime
        remaining_minutes = datetime_difference.total_seconds() / 60
        if abs(remaining_minutes) < 30:
            medicine_cube = robot.world.get_light_cube(self.medicine_cube_id)
            event_description = event['description']
            robot_text = 'It is time for your {0} medicine.'.format(event['description'])
            self.robot_say_text(robot, robot_text)
            medicine_cube.set_lights(cozmo.lights.red_light)
            self.pickup_deliver_cube(robot, medicine_cube)
            medicine_cube.set_lights(cozmo.lights.off_light)
            robot_text = 'I forget to bring your water. I will bring it now.'
            self.robot_say_text(robot, robot_text)
            water_cube = robot.world.get_light_cube(self.water_cube_id)
            water_cube.set_lights(cozmo.lights.blue_light)
            self.pickup_deliver_cube(robot, water_cube)
            water_cube.set_lights(cozmo.lights.off_light)
            return True
        
        return False
    
    def pick_medicine_based_on_event(self, robot: cozmo.robot.Robot, event, cubes_list):
        event_datetime_ts = event['start'].get('dateTime', event['start'].get('date'))
        event_datetime = datetime.datetime.fromisoformat(event_datetime_ts[0:-1])
        current_datetime = datetime.datetime.now()
        datetime_difference = current_datetime - event_datetime
        remaining_hours = datetime_difference.total_seconds() / (60 * 60)
        if remaining_hours < 12:
            robot_text = 'Ohh. I can see you have a trip today. I will bring you the medicine kit now.'
            self.robot_say_text(robot, robot_text)
            kit_cube = robot.world.get_light_cube(self.party_cube_id)
            kit_cube.set_lights(cozmo.lights.green_light)
            self.pickup_deliver_cube(robot, kit_cube)
            kit_cube.set_lights(cozmo.lights.off_light)

            return True
        return False

    def main(self, robot: cozmo.robot.Robot):
        # Firstly Cozmo should detect the position of the user and greet 
        # based on the situation.
        result = self.greet_user(robot=robot)
        if not result:
            print("Cozmo is unable to find {0}.".format(self.user_name))
            return

        self.event_dict = fetch_calendar.fetch_calendar_events(3)
        if self.event_dict is None:
            self.robot_say_text(robot, 'You don\'t have any medicine or upcoming event as of now')
            return

        # # Detect cubes in the area.
        cubes = cozmo_functions.detect_cubes(robot=robot)
        if not cubes:
            print("Cozmo is unable to find all the three cubes")
            return

        for event in self.event_dict:
            event_summary = event['summary']
            if event_summary.lower() == 'medicine':
                self.pick_medicine_based_on_time(robot, event, cubes)
            elif event_summary.lower() == 'party':
                self.pick_medicine_based_on_event(robot, event, cubes)
            
        
            

if __name__ == "__main__":
    user_name = "neeraj"
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    robot_task = Robot_Task(user_name)
    cozmo.run_program(robot_task.main, use_viewer=True, deprecated_filter="ignore")