#!/usr/bin/env python
import socket, sys, time, datetime, os, json, utils
from termcolor import colored
from utils import *
from os.path import join, dirname
from watson_developer_cloud import TextToSpeechV1,SpeechToTextV1
import zmq
from time import sleep

context = zmq.Context()

class UnexpectedStateError(Exception):
	"""Base class for exceptions in this module."""
	pass

## IBM Watson API
text_to_speech = TextToSpeechV1(
	username='96db6c7a-2595-491a-9a62-740dc31e0482',
	password='azDpe42DlQ5C')

speech_to_text = SpeechToTextV1(
	username='a1c7a39e-6618-4274-98f1-6ec5ef7237b8',
	password='pU5vkvlPIpmZ')

NUM_CLIENTS = 7

class Client:
	def __init__(self, addr):

		self.addr = addr

		statesock = context.socket(zmq.SUB)
		statesock.connect("tcp://"+addr+":5560")
		statesock.setsockopt(zmq.SUBSCRIBE,'')
		statesock.setsockopt(zmq.LINGER, 0)
		statesock.SNDTIMEO = 100
		self.statesock = statesock

		cmdsock = context.socket(zmq.REQ)
		cmdsock.connect("tcp://"+addr+":5561")
		cmdsock.setsockopt(zmq.LINGER, 0)
		cmdsock.SNDTIMEO = 100
		cmdsock.RCVTIMEO = 100
		self.cmdsock = cmdsock

	def send(self, cmd, msg=""):
		print self.addr, "sending", cmd, msg
		self.cmdsock.send_string(cmd + ":" + msg)
		response = self.cmdsock.recv()
		print self.addr, "received cmd", response
		return response

	def expect(self, expectedstate, timeout=100):
		print self.addr, "expecting", expectedstate
		self.statesock.RCVTIMEO = timeout
		[state, data] = self.statesock.recv().split(':')
		if state != expectedstate:
			raise UnexpectedStateError("unexpected state", state)

		return data

clients = [Client('whisper_'+str(x)) for x in range(0,NUM_CLIENTS)]

# audio_int()

while True:
	listen_for_speech()
	with open('output/record.wav', 'rb') as audio_file:
		result = json.dumps(speech_to_text.recognize(audio_file, content_type='audio/wav'))
		parsed_json = json.loads(result)
	try:
		text = parsed_json['results'][0]['alternatives'][0]['transcript']
	except:
		print "Speech-to-text failed"
		continue
	# text = "Brian is in the kitchen"

	for i, client in enumerate(clients):
		if i+1 < len(clients):
			nextclient = clients[i+1]
		else:
			nextclient = None

		try:
			if nextclient:
				nextclient.send("LISTEN")
				nextclient.expect("listening")
		except (zmq.ZMQError, UnexpectedStateError):
			print "Nextclient " + nextclient.addr + "failed"
			nextclient = None

		try:
			# print "sending", text
			client.send("TALK", text)
			client.expect("talking")
			client.expect("waiting", 10*1000)
		except (zmq.ZMQError, UnexpectedStateError):
			print "Client " + client.addr + "failed"

		try:
			if nextclient:
				nextclient.send("STOP_LISTEN")

				clienttext = nextclient.expect("waiting", 10*1000)
				if clienttext:
					print "Updating text from client", clienttext
					text = clienttext
		except (zmq.ZMQError, UnexpectedStateError):
			print "Nextclient " + nextclient.addr + "failed"
# sleep(10)
