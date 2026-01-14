
import asyncio
import sys
import os

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.chat.intent_detector import IntentDetector, ChatIntent

async def main():
    detector = IntentDetector()

    queries = [
        "كيف هو أدائي التعليمي",
        "كيف هو ادائي التعليمي",
        "مستواي",
        "تحليل الاداء",
        "اريد تمرين",
        "عطيني تمرين صعب",
    ]

    print("--- Debugging Intent Detector ---")
    for q in queries:
        result = await detector.detect(q)
        print(f"Query: '{q}' -> Intent: {result.intent} (Confidence: {result.confidence})")

if __name__ == "__main__":
    asyncio.run(main())
