"""
Mock wake-word detector driven by plain text input.
"""


class WakeDetectorMock:
    def __init__(self, wake_words=None):
        if wake_words is None:
            wake_words = ["hey chess"]
        self.wake_words = [w.lower() for w in wake_words]

    def detect(self, text: str) -> bool:
        return text.strip().lower() in self.wake_words
