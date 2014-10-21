import socket
import threading
import util


class CheesyVisionServer(object):
	def __init__(self):
		self.hot = False

		self.last_t = util.get_time_millis()

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.bind(('10.8.65.2', 1180))  # 10.8.65.2
		self.sock.listen(5)
		self.sock.setblocking(0)
		self.connected = False
		self.running = False

	def start(self):
		t = threading.Thread(target=self.cheese)
		self.running = True
		t.start()

	def cheese(self):
		while self.running:
			cur_time = util.get_time_millis()
			if self.last_t + 50 <= cur_time:
				if not self.connected:
					try:
						client, address = self.sock.accept()
						try:
							data = client.recv(1)
							if data:
								self.hot = data[0] == 0x01
							self.last_t = cur_time
							self.connected = True
						except:  # TODO narrow this down
							self.connected = False
					except:  # TODO narrow this down
						print("connect failed")
						self.last_t = cur_time + 1000
