#!/usr/bin/env python

import sys
import time
import datetime
import cozmo
import fetch_calendar
import send_email
import cozmo_functions

class Robot_Task():
    def __init__(self, user_name):
        self.medicine_cube_id = cozmo.objects.LightCube1Id
        self.kit_cube_id = cozmo.objects.LightCube2Id
        self.water_cube_id = cozmo.objects.LightCube3Id
        self.user_name = user_name
        # Medicine counter is set to 1 for now because of the unavailability of more cubes.
        self.medicine_counter = 1
    
    def robot_say_text(self, robot: cozmo.robot.Robot, speech_text):
        robot.say_text(speech_text, duration_scalar=0.65).wait_for_completed()

    def greet_user(self, robot: cozmo.robot.Robot):
        # Detect the user's face and save its position
        self.face_pose, self.detected_face = cozmo_functions.detect_face_pose(robot=robot, timeout=60, name=self.user_name)
        if self.detected_face is None:
            # If the cozmo is unable to find the user, It will do the same task again.
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabBored, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
            self.robot_say_text(robot, "Hello {0}, Are you there? I can't find you.".format(self.user_name))
            self.face_pose, self.detected_face = cozmo_functions.detect_face_pose(robot=robot, timeout=30, name=self.user_name)
            if self.detected_face is None:
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabBored, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
                self.robot_say_text(robot, "I can't find you {0}. Please let me know if you are here.".format(self.user_name))
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSleep).wait_for_completed()
                return False
        
        # If the cozmo detect the person, it turns toward the person
        # and greet him/her based on the time of the day.
        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabCelebrate, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()
        robot.turn_towards_face(self.detected_face).wait_for_completed()
        greet_msg = ""
        time_now = time.localtime()
        if time_now.tm_hour < 12:
            greet_msg = "Good Morning {0}, Hope you are enjoying your day well.".format(self.user_name)
        elif time_now.tm_hour >= 12 and time_now.tm_hour <= 14:
            greet_msg = "Good Afternoon {0}, Hope you are enjoying your day well".format(self.user_name)
        else:
            greet_msg = "Good Evening {0}, Hope you had a wonderful day today".format(self.user_name)
            
        self.robot_say_text(robot, greet_msg)
        return True
    
    def pickup_deliver_cube(self, robot: cozmo.robot.Robot, cube):
        # Command the robot to pickup the cube
        print('Picking up the cube')
        robot.pickup_object(cube, num_retries=3).wait_for_completed()
        # Command the robot to go to the person's position
        print('Move to person\'s position')
        robot.go_to_pose(self.face_pose, relative_to_robot=False, num_retries=3).wait_for_completed()
        # Place the object infront of the person
        print('Place on the object')
        robot.place_object_on_ground_here(cube, num_retries=3).wait_for_completed()
        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabAmazed, ignore_lift_track=True, ignore_body_track=True).wait_for_completed()

    def pick_medicine_based_on_time(self, robot: cozmo.robot.Robot, event):
        # Find the time of medication.
        event_datetime_ts = event['start'].get('dateTime', event['start'].get('date'))
        event_datetime = datetime.datetime.fromisoformat(event_datetime_ts[0:-1])
        current_datetime = datetime.datetime.now()
        datetime_difference = current_datetime - event_datetime
        remaining_minutes = datetime_difference.total_seconds() / 60
        if abs(remaining_minutes) < 30:
            # Get the medicine from the locker
            medicine_cube = robot.world.get_light_cube(self.medicine_cube_id)
            robot.turn_towards_face(self.detected_face, num_retries=1).wait_for_completed()
            robot_text = 'It is time for your {0} medicine. I am going to get the medicine for you now.'.format(event['description'])
            self.robot_say_text(robot, robot_text)
            
            if not self.is_all_cube_located:
                self.locate_cubes(robot)

            if self.is_all_cube_located:
                medicine_cube.set_lights(cozmo.lights.red_light)
                self.pickup_deliver_cube(robot, medicine_cube)
                self.robot_say_text(robot, 'Here is your medicine. Please take it.')
                # wait for the person to tap the 'medicine' cube
                cozmo_functions.react_robot_tap_cube(robot, medicine_cube, 'Please take your medicine.')
                medicine_cube.set_lights(cozmo.lights.off_light)

                self.medicine_counter = self.medicine_counter - 1
                if self.medicine_counter < 1:
                    # Report the authorised person regarding the unavailability of the medicine for the future through email.
                    email_subject = 'Medicine is Out-of-Stock for {0}'.format(self.user_name)
                    email_content = 'This is to inform that {0} medicine went out of stock for {1}, Please refill it as soon as possible before the next reminder.'.format(event['description'], self.user_name)
                    send_email.send_email(email_subject, email_content)

                # Robot then goes to fetch water for the person
                robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabThinking, ignore_lift_track=False, ignore_body_track=True).wait_for_completed()
                robot_text = 'Sorry, I forgot to bring you water. I am going to get it for you.'
                self.robot_say_text(robot, robot_text)
                water_cube = robot.world.get_light_cube(self.water_cube_id)
                water_cube.set_lights(cozmo.lights.blue_light)
                self.pickup_deliver_cube(robot, water_cube)
                self.robot_say_text(robot, 'Sorry. Please have the water.')
                cozmo_functions.react_robot_tap_cube(robot, water_cube, 'Please take the water.')
                water_cube.set_lights(cozmo.lights.off_light)
                return True
        
        return False
    
    def pick_medicine_kit_based_on_event(self, robot: cozmo.robot.Robot, event):
        # Find the time of the event
        event_datetime_ts = event['start'].get('dateTime', event['start'].get('date'))
        event_datetime = datetime.datetime.fromisoformat(event_datetime_ts[0:-1])
        current_datetime = datetime.datetime.now()
        datetime_difference = current_datetime - event_datetime
        remaining_hours = datetime_difference.total_seconds() / (60 * 60)
        if remaining_hours < 3:
            # Get the kit from the locker
            if event['location'] == None:
                self.robot_say_text(robot, 'Oh. I can see you are travelling today. I will bring you the medicine kit now.')
            else:
                self.robot_say_text(robot, 'Oh. I can see you are travelling to {0} today. I will bring you the medicine kit now.'.format(event['location']))
            if not self.is_all_cube_located:
                self.locate_cubes(robot)

            if self.is_all_cube_located:
                kit_cube = robot.world.get_light_cube(self.kit_cube_id)
                kit_cube.set_lights(cozmo.lights.green_light)
                self.pickup_deliver_cube(robot, kit_cube)
                self.robot_say_text(robot, 'Here is your medical kit. Please take it along with you during the travel.')
                cozmo_functions.react_robot_tap_cube(robot, kit_cube, 'Please take the kit along with you.')
                kit_cube.set_lights(cozmo.lights.off_light)
                return True
        return False

    def run_robot(self, robot: cozmo.robot.Robot):
        # Main function
        # Firstly Cozmo should detect the position of the user and greet 
        # based on the time and situation.
        self.is_all_cube_located = False
        result = self.greet_user(robot=robot)
        if not result:
            print("Cozmo is unable to find {0}.".format(self.user_name))
            return

        # Fetch the next 3 upcoming events using the Google Calendar API.
        self.event_dict = fetch_calendar.fetch_calendar_events(3)
        if self.event_dict is None:
            # If there are no events added, let the person know about it.
            self.robot_say_text(robot, 'You don\'t have any medicine or upcoming event as of now')
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSleep).wait_for_completed()
            return

        for event in self.event_dict:
            event_summary = event['summary']
            if event_summary.lower() == 'medicine':
                # If the title of the event is medicine
                self.pick_medicine_based_on_time(robot, event)
            elif event_summary.lower() == 'travel':
                # If the title of the event is travel
                self.pick_medicine_kit_based_on_event(robot, event)
            else:
                print('Unknown event')
        
        self.robot_say_text(robot, 'That is all for now. Enjoy your time.')
        robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabSleep).wait_for_completed()
    
    def locate_cubes(self, robot: cozmo.robot.Robot):
        print('Locating the cubes')
        cubes = cozmo_functions.detect_cubes(robot=robot)
        if not cubes:
            robot.play_anim_trigger(cozmo.anim.Triggers.CodeLabWondering).wait_for_completed()
            self.robot_say_text(robot, 'I am unable to find the medicines in the locker. I will send an email to the supervisor regarding this.')
            return
        self.is_all_cube_located = True
        
            

if __name__ == "__main__":
    user_name = "neeraj"
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
    robot_task = Robot_Task(user_name)
    cozmo.robot.Robot.drive_off_charger_on_connect = True
    cozmo.run_program(robot_task.run_robot, use_viewer=True, deprecated_filter="ignore")