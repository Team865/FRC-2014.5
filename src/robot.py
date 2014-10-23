import sys
from cheesyvision import CheesyVisionServer
from helpers import CheesyDriveHelper, IntakeHelper
from systems import Intake, Drivetrain
import auton
import wpiwrapper as wpilib


class RobotGuy(wpilib.SimpleRobot):
	def __init__(self):
		super().__init__()
		self.controller = wpilib.Joystick(1)
		self.drivetrain = Drivetrain(1, 2, 1, 1)
		self.intake = Intake(5, 8, 3, 4, 2)
		self.compressor = wpilib.Compressor(1, 1)

		self.ds = wpilib.DriverStation.GetInstance()
		self.auton = auton.Auton(self)
		self.cheesyvision = CheesyVisionServer()

		self.cdh = CheesyDriveHelper(self)
		self.ith = IntakeHelper(self)

		# Auton mode
		self.auton.select('noauton')

	def RobotInit(self):
		self.cheesyvision.start()
		self.compressor.Start()

	def Disabled(self):
		while self.IsDisabled():
			wpilib.Wait(0.01)

	def Autonomous(self):
		self.auton.run()
		while self.IsAutonomous() and self.IsEnabled():
			wpilib.Wait(0.1)
	
	def OperatorControl(self):
		dog = self.GetWatchdog()
		dog.SetEnabled(True)
		dog.SetExpiration(0.25)
		while self.IsOperatorControl() and self.IsEnabled():
			if self.controller.GetRawButton(6):
				self.drivetrain.shift('low')
			else:
				self.drivetrain.shift('high')

			qt = self.controller.GetRawButton(5)
			turn = self.controller.GetRawAxis(4)
			if qt:
				negturn = turn < 0
				turn = abs(turn * turn) * (-1 if negturn else 1)  # could have easily done math.pow but whatever

			self.cdh.cheesydrive(-self.controller.GetRawAxis(2), turn, qt, not self.controller.GetRawButton(6))
			self.ith.do_intake(self.controller.GetRawButton(1), self.controller.GetRawButton(2))
			dog.Feed()
			wpilib.Wait(0.04)


def run():
	robot = RobotGuy()
	robot.StartCompetition()
	return robot

if __name__ == '__main__':
	wpilib.require_version('2014.7.2')

	import physics
	wpilib.internal.physics_controller.setup(physics)

	wpilib.run()