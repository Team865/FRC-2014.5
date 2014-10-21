#!/usr/bin/env python
# Copyright (c) 2014, Team 254
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#	1. Redistributions of source code must retain the above copyright notice, this
#	   list of conditions and the following disclaimer.
#	2. Redistributions in binary form must reproduce the above copyright notice,
#	   this list of conditions and the following disclaimer in the documentation
#	   and/or other materials provided with the distribution.
#
#	   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#	   ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#	   WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#	   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#	   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#	   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#	   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#	   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#	   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#	   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#	   The views and conclusions contained in the software and documentation are those
#	   of the authors and should not be interpreted as representing official policies,
#	   either expressed or implied, of the FreeBSD Project.

import numpy as np
import cv2 as cv
import socket
import time

# network comms stuff
HOST, PORT = "10.8.65.2", 1180
#HOST, PORT = "127.0.0.1", 1180

# Name of displayed window
WINDOW_NAME = "CheesyVision"


# Dimensions of the webcam image (it will be resized to this size)
WEBCAM_WIDTH_PX = 640
WEBCAM_HEIGHT_PX = 360

# The location of the calibration rectangle.
CAL_UL = (WEBCAM_WIDTH_PX/2 - 20, 180)
CAL_LR = (WEBCAM_WIDTH_PX/2 + 20, 220)

# The location of the target rectangle.
TARGET_UL = (WEBCAM_WIDTH_PX/2 - 50, 250)
TARGET_LR = (WEBCAM_WIDTH_PX/2 + 50, 300)

# Constants for drawing.
BOX_BORDER = 3
CONNECTED_BORDER = 15
INDICATOR_HEIGHT = 30

# This is the rate at which we will send updates to the cRIO.
UPDATE_RATE_HZ = 40.0
PERIOD = (1.0 / UPDATE_RATE_HZ) * 1000.0


# How sure are we that there's a hand there?
AVERAGE_THRESHOLD = 0.8

def get_time_millis():
	''' Get the current time in milliseconds. '''
	return int(round(time.time() * 1000))

def color_distance(c1, c2):
	''' Compute the difference between two HSV colors.

	Currently this simply returns the "L1 norm" for distance,
	or delta_h + delta_s + delta_v.  This is not a very robust
	way to do it, but it has worked well enough in our tests.

	Recommended reading:
	http://en.wikipedia.org/wiki/Color_difference
	'''
	total_diff = 0
	for i in (0, 1, 2):
		diff = (c1[i]-c2[i])
		# Wrap hue angle...OpenCV represents hue on (0, 180)
		if i == 0:
			if diff < -90:
				diff += 180
			elif diff > 90:
				diff -= 180
		total_diff += abs(diff)
	return total_diff

def color_far(img, ul, lr):
	''' Light up a bright yellow rectangle if the color distance is large. '''
	cv.rectangle(img, ul, lr, (0, 255, 255), -1)

def draw_static(img, connected):
	''' Draw the image and boxes. '''
	bg = np.zeros((img.shape[0], WEBCAM_WIDTH_PX, 3), dtype=np.uint8)
	bg[:,0:WEBCAM_WIDTH_PX,:] = img
	cv.rectangle(bg, TARGET_UL, TARGET_LR, (0, 255, 255), BOX_BORDER)
	cv.rectangle(bg, CAL_UL, CAL_LR, (255, 255, 255), BOX_BORDER)
#	if connected:
#		cv.rectangle(bg, (0, 0), (bg.shape[1]-1, bg.shape[0]-1), (0, 255, 0), CONNECTED_BORDER)
#	else:
#		cv.rectangle(bg, (0, 0), (bg.shape[1]-1, bg.shape[0]-1), (0, 0, 255), CONNECTED_BORDER)
	return bg

def detect_color(img, box):
	''' Return the average HSV color of a region in img. '''
	h = np.mean(img[box[0][1]+3:box[1][1]-3, box[0][0]+3:box[1][0]-3, 0])
	s = np.mean(img[box[0][1]+3:box[1][1]-3, box[0][0]+3:box[1][0]-3, 1])
	v = np.mean(img[box[0][1]+3:box[1][1]-3, box[0][0]+3:box[1][0]-3, 2])
	return (h,s,v)

def detect_colors(img):
	''' Return the average colors for the calibration and target boxes. '''
	cal = detect_color(img, (CAL_UL, CAL_LR))
	target = detect_color(img, (TARGET_UL, TARGET_LR))

	return cal, target

def main():
	cv.namedWindow(WINDOW_NAME, 1)

	# Open the webcam (should be the only video capture device present).
	capture = cv.VideoCapture(0)

	# The maximum difference in average color between two boxes to consider them
	# the same.  See color_distance.
	max_color_distance = 100
	last_max_color_distance = max_color_distance

	# Manually set the exposure, because a lot of webcam drivers will overexpose
	# the image and lead to poor separation between foreground and background.
	exposure = -4
	last_exposure = exposure
	capture.set(15, exposure)  # 15 is the enum value for CV_CAP_PROP_EXPOSURE

	# Keep track of time so that we can provide the cRIO with a relatively constant
	# flow of data.
	last_t = get_time_millis()

	# Are we connected to the server on the robot?
	connected = False
	s = None
	
	average_target = 0 # This is to smooth target errors.
	average_list = [0,0,0,0,0,0] # 10 seems to be a good length, but lower means faster response.
	
	
	while 1:
		# Get a new frame.
		_, img = capture.read()
		if not img == None: # Prevent a crash if the webcam doesn't serve up an image
			# Flip it and shrink it.
			small_img = cv.flip(cv.resize(img, (WEBCAM_WIDTH_PX, WEBCAM_HEIGHT_PX)), 1)

			# Render the image onto our canvas.
			bg = draw_static(small_img, connected)

			# Get the average color of each of the boxes.
			cal, target = detect_colors(cv.cvtColor(bg, cv.COLOR_BGR2HSV))

			# Get the difference between the target box vs. calibration.
			target_dist = color_distance(target, cal)

			# Check the difference.
			target_on = target_dist < max_color_distance

			'''
			#average smoothing
			average_list.pop(0) #get rid of the 1st item in the list
			average_list.append(target_on) # add a new one
			average_target = 0.0
			for num in average_list:
				average_target += num
			
			average_target /= len(average_list)
			
			target_probably_on = (average_target > AVERAGE_THRESHOLD)
			if average_target > 0.9:
				average_list = [True,True,True,True,True,True]
				
			print average_list
			print average_target
			'''
			
			target_probably_on = target_on
			
			# If we detect a hand, color the widget.
			B = CONNECTED_BORDER
			if target_probably_on:
				color_far(bg, (B, WEBCAM_HEIGHT_PX - INDICATOR_HEIGHT - B), ((WEBCAM_WIDTH_PX - B), WEBCAM_HEIGHT_PX-B))
			
			'''
			if target_on:
				color_far(bg, (B,B), (B+10,B+10))
			'''

			# Throttle the output
			cur_time = get_time_millis()
			if last_t + PERIOD <= cur_time:
				# Try to connect to the robot on open or disconnect
				if not connected:
					try:
						# Open a socket with the cRIO so that we can send the state of the hot goal.
						s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

						# This is a pretty aggressive timeout...we want to reconnect automatically
						# if we are disconnected.
						s.settimeout(0.05)
						s.connect((HOST, PORT))
					except:
						print("failed to reconnect");
						last_t = cur_time + 1000
				try:
					# Send one byte to the cRIO:
					# 0x00: Off
					# 0x01: On
					write_bytes = bytearray()
					v = (target_probably_on << 0)
					write_bytes.append(v)
					s.send(write_bytes)
					last_t = cur_time
					connected = True
					print("Hot: %s" % target_probably_on)
				except:
					connected = False

			# Show the image.
			cv.imshow(WINDOW_NAME, bg)

			# Capture a keypress.
			key = cv.waitKey(10) & 255

			# Escape key.
			if key == 27:
				break
	if not s == None:
		s.close()

if __name__ == '__main__':
	main()