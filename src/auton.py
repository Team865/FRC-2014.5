from helpers import GyroHelper
import wpiwrapper as wpilib


class Auton(object):
	def __init__(self, robot):
		self.robot = robot
		self.mode = self.noauton

	def select(self, mode):
		try:
			self.mode = getattr(self, mode)
		except AttributeError:
			print("Auton mode %s does not exist!" % mode)

	def run(self):
		self.mode()

	def noauton(self):
		pass

	def cheesyvision(self):
		r = self.robot
		r.GetWatchdog().SetEnabled(False)
		r.drivetrain.shift('low')
		r.drivetrain.setpower(1, 1)
		wpilib.Wait(2.7)
		r.drivetrain.setpower(1, 1)
		timer = wpilib.Timer()
		timer.Start()

		while timer.Get() < 3.8 and not r.cheesyvision.hot:
			pass  # keep checking!!!

		r.intake.setpower(1)

	def scorelowgoal(self):
		r = self.robot
		r.GetWatchdog().SetEnabled(False)
		r.drivetrain.shift('low')
		r.drivetrain.setpower(1, 1)
		wpilib.Wait(2.7)
		r.drivetrain.setpower(0, 0)
		wpilib.Wait(3.8)

	def drivestraight(self):
		r = self.robot
		r.GetWatchdog().SetEnabled(False)
		r.drivetrain.gyro.Reset()
		r.drivetrain.shift('low')
		kP = 0.1
		while r.IsAutonomous() and r.IsEnabled():
			angle = r.drivetrain.gyro.GetAngle()
			print(angle)
			r.cdh.cheesydrive(-0.25, -angle * kP, False, False)
			wpilib.Wait(0.04)

	def testball(self):
		r = self.robot
		r.GetWatchdog().SetEnabled(False)
		r.drivetrain.gyro.Reset()
		r.intake.setpower(1)

		while not r.intake.hasball():
			pass  # keep checking!!!

		r.intake.setpower(0)
		gyroPID = GyroHelper(r)
		gyroPID.set_angle(180)
		while not gyroPID.at_setpoint():
			gyroPID.update()

		r.drivetrain.setpower(0, 0)
		r.intake.setpower(1)
		while r.intake.hasball():
			pass

		wpilib.Wait(1)
		r.intake.setpower(0)

		gyroPID.set_angle(0)
		while not gyroPID.at_setpoint():
			gyroPID.update()

		r.drivetrain.setpower(0, 0)