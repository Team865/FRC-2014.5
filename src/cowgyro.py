#TODO this bullshit

import collections
import time
import wpiwrapper as wpilib
COWGYRO_RING_SIZE = 10


class CowGyro(object):
	def __init__(self, channel):
		self.ringbuffer = collections.deque(maxlen=COWGYRO_RING_SIZE)
		self.gyro = wpilib.AnalogChannel(channel)

		self.voltsPerDegreePerSecond = wpilib.Gyro.kDefaultVoltsPerDegreePerSecond

		self.center = 0
		self.offset = 0
		self.lastsave = 0
		self.recallqueued = True

		self.gyro.SetAverageBits(wpilib.Gyro.kAverageBits)
		self.gyro.SetOversampleBits(wpilib.Gyro.kOversampleBits)
		samplerate = wpilib.Gyro.kSamplesPerSecond * (1 << (wpilib.Gyro.kAverageBits + wpilib.Gyro.kOversampleBits))
		self.gyro.GetModule().SetSampleRate(samplerate)

		wpilib.Wait(1.0)  # for some reason wpilib does it so we will too

		self.gyro.InitAccumulator()

	def timeSinceLastSave(self):
		return time.time() - self.lastsave

	def getAngle(self):
		if self.center == 0 and self.offset == 0:
			return -999

		raw, count = self.gyro.GetAccumulatorOutput()
		value = raw - (count * self.offset)
		return value * 1e-9 * self.gyro.GetLSBWeight() * (1 << self.gyro.GetAverageBits()) / (self.gyro.GetModule().GetSampleRate() * self.voltsPerDegreePerSecond)

	def reset(self):
		self.gyro.ResetAccumulator()

	#def calibrate(self):
		#if self.timeSinceLastSave() > COWGYRO_ACCUMULATION_PERIOD:
		#	val, count = self.gyro.GetAccumulatorOutput()

		#if self.recallqueued and rngNBytes(self.ringbuffer)