import wpiwrapper as wpilib


class Drivetrain(object):
    def __init__(self, lpin, rpin, shiftpin):
        self.left = wpilib.Talon(lpin)
        self.right = wpilib.Talon(rpin)
        self.shifter = wpilib.Solenoid(shiftpin)

    def setpower(self, lpwm, rpwm):
        self.left.Set(-lpwm)
        self.right.Set(rpwm)

    def shift(self, mode):
        self.shifter.Set(False)
        if mode == 'high':
            pass
        elif mode == 'low':
            self.shifter.Set(True)


class Intake(object):
    def __init__(self, f1, f2, b1, b2):
        self.front1, self.front2 = wpilib.Talon(f1), wpilib.Talon(f2)
        self.back1, self.back2 = wpilib.Talon(b1), wpilib.Talon(b2)

    def setpower(self, power):
        self.front1.Set(power)
        self.front2.Set(power)
        self.back1.Set(power)
        self.back2.Set(power)

