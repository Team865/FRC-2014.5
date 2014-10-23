import wpiwrapper as wpilib


class Drivetrain(object):
	def __init__(self, lpin, rpin, shiftpin, gyropin):
		self.left = wpilib.Talon(lpin)
		self.right = wpilib.Talon(rpin)
		self.shifter = wpilib.Solenoid(shiftpin)
		self.gyro = wpilib.Gyro(gyropin)

	def setpower(self, lpwm, rpwm):
		self.left.Set(-lpwm)
		self.right.Set(rpwm)

	def shift(self, mode):
		if mode == 'high':
			self.shifter.Set(False)
		elif mode == 'low':
			self.shifter.Set(True)

	def getangle(self):
		a = self.gyro.GetAngle()
		while a < -359:
			a += 360
		while a > 360:
			a -= 360
		return a


class Intake(object):
	def __init__(self, f1, f2, b1, b2, ballsensorpin):
		self.front1, self.front2 = wpilib.Talon(f1), wpilib.Talon(f2)
		self.back1, self.back2 = wpilib.Talon(b1), wpilib.Talon(b2)
		self.ballsensor = wpilib.DigitalInput(ballsensorpin)

	def setpower(self, power):
		self.front1.Set(power)
		self.front2.Set(power)
		self.back1.Set(power)
		self.back2.Set(power)

	def hasball(self):
		return self.ballsensor.Get() == 1

