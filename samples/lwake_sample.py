import lwake

# Record audio sample
lwake.record("ref/sample.wav", duration=1, trim_silence=True)

# Compare two audio files
distance = lwake.compare("ref/sample.wav", "file2.wav", method="embedding")
print(f"Distance: {distance}")

# Real-time detection. Callback blocks further listening until return.
# Callback also exposes underlying sounddevice stream if you need to read more audio
def handle_detection(detection, stream):
    print(f"Detected '{detection['wakeword']}' at {detection['timestamp']}")
    # audio, _ = stream.read(16000)                         # Read 1 second of audio
    # soundfile.write("input.wav", audio, samplerate=16000) # Save recording

lwake.listen("reference/folder", threshold=0.1, method="embedding", callback=handle_detection)