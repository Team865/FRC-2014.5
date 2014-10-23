from pyfrc.wpilib import PIDOutput, PIDController
import util
import wpiwrapper as wpilib

class CheesyDriveHelper(object):
	def __init__(self, robot):
		self.drive = robot.drivetrain
		self.oldwheel = 0
		self.quickstopbuffer = 0

	def cheesydrive(self, throttle, wheel, quickturn, highgear):
		negintertia = wheel - self.oldwheel
		self.oldwheel = wheel

		if highgear:  # TODO if is high gear
			wheel = util.sinscale(wheel, 0.6, count=2)
		else:
			wheel = util.sinscale(wheel, 0.5, count=3)

		negintertiabuffer = 0

		if highgear:  # TODO if high gear
			sensitivity = 0.65
			negintertiascalar = 5
		else:
			sensitivity = 0.75
			if wheel * negintertia > 0:
				negintertiascalar = 2.5
			else:
				if abs(wheel) > 0.65:
					negintertiascalar = 5
				else:
					negintertiascalar = 3


		negintertiapower = negintertia * negintertiascalar
		negintertiabuffer += negintertiapower

		wheel += negintertiabuffer
		linearpower = throttle


		if quickturn:
			if abs(linearpower) < 0.2:
				alpha = 0.1
				self.quickstopbuffer = (1 - alpha) * self.quickstopbuffer + alpha * util.limit(wheel, 1.0) * 5
			overpower = 1
			angularpower = wheel
		else:
			overpower = 0
			angularpower = abs(linearpower) * wheel * sensitivity - self.quickstopbuffer
			if self.quickstopbuffer > 1:
				self.quickstopbuffer -= 1
			elif self.quickstopbuffer < -1:
				self.quickstopbuffer += 1
			else:
				self.quickstopbuffer = 0

		lpower = linearpower + angularpower
		rpower = linearpower - angularpower

		if lpower > 1:
			rpower -= overpower * (lpower - 1)
			lpower = 1
		elif rpower > 1:
			lpower -= overpower * (-1 - lpower)
			rpower = 1
		elif lpower < -1:
			rpower += overpower * (-1 * lpower)
			lpower = -1
		elif rpower < -1:
			lpower += overpower * (-1 - rpower)
			rpower = -1

		self.drive.setpower(lpower, rpower)


class IntakeHelper(object):
	def __init__(self, robot):
		self.intake = robot.intake

	def runintake(self):
		pass


class GyroHelper(object):
	def __init__(self, robot):
		self.drive = robot.drivetrain
		self.setpoint = 180
		self.kP = 0.1
		self.error = 9999999999

		self.controller = PIDController(0.1, 0, 0, self.drive.gyro, self.output)

	def update(self):
		self.error = self.setpoint - self.drive.getangle()
		pid = self.kP * self.error
		pid = min(pid, 0.2)
		self.drive.setpower(pid, -pid)
		print(self.drive.gyro.PIDGet())

	def ontarget(self):
		return 3 > self.error > -3

	class PIDRotate(PIDOutput):
		def __init__(self):
			self.val = 0

		def PIDWrite(self, val):
			self.val = val

		def getvalue(self):
			return self.val