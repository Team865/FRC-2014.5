from wpiwrapper import PIDOutput, PIDController, Timer
import util


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
		self.state = 'off'
		self.timer = Timer()

	def do_intake(self, in_button, out_button):
		if self.state is 'off':
			self.intake.setpower(0)
			if in_button:  # do inbound
				self.state = 'inbound'
			elif out_button:
				self.state = 'reverse_inbound'

		if self.state is 'inbound':
			self.intake.setpower(1)
			if self.intake.hasball():
				self.state = 'hold'
			elif out_button:
				self.state = 'off'

		if self.state is 'reverse_inbound':
			self.intake.setpower(-1)
			if self.intake.hasball():
				self.state = 'hold'
			elif in_button:
				self.state = 'off'

		if self.state is 'hold':
			self.intake.setpower(0)
			if in_button:
				self.state = 'pass'
			elif out_button:
				self.state = 'eject'

		if self.state is 'pass':
			self.intake.setpower(1)
			if self.timer.Get() > 1 and not self.intake.hasball():  # eject for 1s
				self.timer.Stop()
				self.timer.Reset()
				self.state = 'off'
			elif self.timer.Get() == 0:
				self.timer.Start()

		if self.state is 'eject':
			self.intake.setpower(-1)
			if self.timer.Get() > 2.5 and not self.intake.hasball():  # eject for 1s
				self.timer.Stop()
				self.timer.Reset()
				self.state = 'off'
			elif self.timer.Get() == 0:
				self.timer.Start()






class GyroHelper(object):
	def __init__(self, robot):
		self.robot = robot
		self.output = self.PIDRotate()

		self.controller = PIDController(0.1, 0, 0, self.robot.drivetrain.gyro, self.output)
		self.controller.SetTolerance(0.5)
		self.controller.SetContinuous(True)
		self.controller.Enable()

	def set_angle(self, angle):
		self.controller.SetSetpoint(angle)
		self.controller.Enable()

	def at_setpoint(self):
		return self.controller.OnTarget()

	def update(self):
		self.robot.cdh.cheesydrive(0.0, self.output.angle, True, True)
		if self.controller.OnTarget():
			self.controller.Disable()

	def enable(self):
		self.controller.Enable()

	def disable(self):
		self.controller.Disable()

	class PIDRotate(PIDOutput):
		def __init__(self):
			super().__init__()
			self.angle = 0

		def PIDWrite(self, val):
			self.angle = val
