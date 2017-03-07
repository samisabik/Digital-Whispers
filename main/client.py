import os,sys,random,utils,json,zmq
from os.path import join, dirname
from sys import exit
from time import sleep
from watson_developer_cloud import TextToSpeechV1,SpeechToTextV1

## IBM Watson API
text_to_speech = TextToSpeechV1(
	username='96db6c7a-2595-491a-9a62-740dc31e0482',
	password='azDpe42DlQ5C')

speech_to_text = SpeechToTextV1(
	username='a1c7a39e-6618-4274-98f1-6ec5ef7237b8',
	password='pU5vkvlPIpmZ')

TTSvoices = ["en-US_AllisonVoice","en-US_LisaVoice","en-GB_KateVoice","en-US_MichaelVoice"]

context = zmq.Context()
statesock = context.socket(zmq.PUB)
statesock.bind("tcp://*:5560")

cmdsock = context.socket(zmq.REP)
cmdsock.bind("tcp://*:5561")

state = "waiting"

def changestate(newstate, data=""):
	state = newstate
	statesock.send_string(state + ":" + data)
	print "state", state

def ok():
	cmdsock.send_string("OK")

changestate("waiting")

rec = utils.Recorder(channels=1)

recfile = None
while True:
	[cmd, data] = cmdsock.recv().split(':')
	print "received", cmd, data

	if cmd == "LISTEN":
		ok()
		recfile2 = rec.open('output/record.wav', 'wb')
		recfile2.start_recording()
		changestate("listening")

	elif cmd == "STOP_LISTEN":
		recfile2.stop_recording()
		recfile2.close()
		ok()
		with open('output/record.wav', 'rb') as audio_file:
			result = json.dumps(speech_to_text.recognize(audio_file, content_type='audio/wav'))
			parsed_json = json.loads(result)
		try:
			text = parsed_json['results'][0]['alternatives'][0]['transcript']
		except:
			print "STT failed !"
			text = ""
		changestate("waiting", text)

	elif cmd == "TALK":
		ok()
		changestate("talking")
		with open('output/synthesize.wav', 'wb') as audio_file:
			audio_file.write(text_to_speech.synthesize(data,TTSvoices[random.randrange(0, 4)],"audio/wav"))
		os.system('play -q --ignore-length output/synthesize.wav')
		changestate("waiting")

	else:
		cmdsock.send_string("ERROR")
		exit()
