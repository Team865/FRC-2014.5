from pyfrc import wpilib


class Auton(object):
	def __init__(self, robot):
		self.robot = robot
		self.mode = self.noauton

	def select(self, mode):
		try:
			self.mode = getattr(self, mode)
		except AttributeError as e:
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

		r.intake.setpower(1)