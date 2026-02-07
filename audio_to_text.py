import whisper
import subprocess
from record import record_audio
import os

def audio_to_text():
    raw_audio = record_audio()   
    print("Speak record in wav form")
    clean_audio = "clean.wav"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_audio,
        "-ar", "16000",        
        "-ac", "1",            
        "-c:a", "pcm_s16le", 
        clean_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    model = whisper.load_model("medium", device="cpu")

    result = model.transcribe(
        clean_audio,
        # language="hi",  
        task="transcribe",
        fp16=False
    )

    print("\nTranscription:")
    print(result["text"])
    return result["text"]   


def audio_to_text_fn(audio_file):
    raw_audio =audio_file   
    clean_audio = "clean.wav"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", raw_audio,
        "-ar", "16000",        
        "-ac", "1",            
        "-c:a", "pcm_s16le", 
        clean_audio
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    model = whisper.load_model("medium", device="cpu")

    result = model.transcribe(
        clean_audio,
        # language="hi",  
        task="transcribe",
        fp16=False
    )
    os.remove(clean_audio)
    # os.remove(raw_audio)
    print("\nTranscription:")
    print(result["text"])

    return result["text"] 

# text_to_audio()