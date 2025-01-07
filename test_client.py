import asyncio
import websockets
import sounddevice as sd
import numpy as np
from typing import Optional
import click
import sys

async def record_audio(duration: float = 0.5, sample_rate: int = 16000) -> np.ndarray:
    """Record audio from microphone."""
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    return audio_data

async def play_audio(audio_data: bytes, sample_rate: int = 16000):
    """Play audio data."""
    audio_array = np.frombuffer(audio_data, dtype=np.float32)
    sd.play(audio_array, sample_rate)
    sd.wait()

async def main(server_url: str = "ws://localhost:8000/ws/conversation"):
    """Main client function."""
    try:
        async with websockets.connect(server_url) as websocket:
            print("Connected to voice agent server")
            print("Press Enter to start speaking (q + Enter to quit)")
            
            while True:
                command = input()
                if command.lower() == 'q':
                    break
                    
                print("Recording... (speak now)")
                audio_data = await record_audio()
                
                # Send audio to server
                await websocket.send(audio_data.tobytes())
                
                # Receive response
                print("Waiting for response...")
                response = await websocket.recv()
                
                # Play response
                print("Playing response...")
                await play_audio(response)
                
    except websockets.exceptions.ConnectionClosed:
        print("Connection to server closed")
    except Exception as e:
        print(f"Error: {str(e)}")

@click.command()
@click.option('--server', default="ws://localhost:8000/ws/conversation", help='WebSocket server URL')
def run(server):
    """Run the test client."""
    try:
        asyncio.run(main(server))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    run()
