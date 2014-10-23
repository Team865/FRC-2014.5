import math
import time


def deadband(rawaxis, amount):
	return rawaxis if abs(rawaxis) > abs(amount) else 0


def sinscale(val, nonlinearity, count=1):
	count -= 1
	s = math.sin(math.pi / 2 * nonlinearity * val) / math.sin(math.pi / 2 * nonlinearity)
	if count > 0:
		return sinscale(s, nonlinearity)
	else:
		return s


def limit(v, limit):
	return v if abs(v) < limit else (-1 if v < 0 else 1)


def get_time_millis():
	return int(round(time.time() * 1000))