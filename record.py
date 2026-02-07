# import wave
# import pyaudio
# import audioop
# import time

# FRAME_PER_BUFFER = 3200
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 16000

# SILENCE_THRESHOLD = 500
# SILENCE_SECONDS = 1

# def record_audio(output_file="output.wav"):
#     p = pyaudio.PyAudio()

#     stream = p.open(
#         format=FORMAT,
#         channels=CHANNELS,
#         rate=RATE,
#         input=True,
#         frames_per_buffer=FRAME_PER_BUFFER
#     )

#     print("Speak now...")

#     frames = []
#     silence_start = None

#     while True:
#         data = stream.read(FRAME_PER_BUFFER, exception_on_overflow=False)
#         frames.append(data)

#         rms = audioop.rms(data, 2)  

#         if rms < SILENCE_THRESHOLD:
#             if silence_start is None:
#                 silence_start = time.time()
#             elif time.time() - silence_start >= SILENCE_SECONDS:
#                 break
#         else:
#             silence_start = None

#     stream.stop_stream()
#     stream.close()
#     p.terminate()
#     print("Speak end...")
#     with wave.open(output_file, "wb") as wf:
#         wf.setnchannels(CHANNELS)
#         wf.setsampwidth(p.get_sample_size(FORMAT))
#         wf.setframerate(RATE)
#         wf.writeframes(b"".join(frames))

#     return output_file
