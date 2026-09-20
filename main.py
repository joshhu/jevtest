"""判斷「話裡真正的意思」的命令列版本：同一句回覆只差一個標點，Jev 給的機率分布差多少。

Jev 透過 OpenRouter 呼叫：官方 typesafe-sdk 只要把 base_url 指到 OpenRouter 即可。
"""

import os
import sys
import time

from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()

JEV_MODEL = os.getenv("JEV_MODEL") or "jev-latest"

CONTEXT = {"relationship": "交往三年的另一半", "you_said": "我今天跟同事聚餐，會晚點回家喔"}
REPLIES = ["好", "好。", "好啊～玩得開心", "沒事，你去忙吧", "隨便你", "你開心就好"]

MEANINGS = {
    "真的沒事": "Genuinely fine, nothing hidden",
    "有點失落": "A bit disappointed or lonely, but not angry",
    "在生氣": "Angry or resentful, saying the opposite of what they mean",
    "在試探你": "Testing whether you will notice and care",
}

QUESTIONS = {
    "真正的意思": Choice(
        instructions="What is the real feeling behind they_replied, given relationship and you_said?",
        criteria=MEANINGS,
    ),
    "火氣": Score(
        instructions="How upset is the person who wrote they_replied",
        criteria=["平靜", "有點悶", "明顯不高興", "快要爆炸"],
    ),
    "該馬上關心": Noul(
        instructions="The person who wrote they_replied expects you to reach out or change your plan right now",
    ),
}


def main() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("缺少環境變數：OPENROUTER_API_KEY（請參考 .env.example 建立 .env）")

    print(f"你傳的：{CONTEXT['you_said']}")
    with TypeSafeClient(api_key=api_key, base_url="https://openrouter.ai/api", model=JEV_MODEL) as jev:
        for reply in REPLIES:
            started = time.perf_counter()
            response = jev.system_one(state={**CONTEXT, "they_replied": reply}, questions=QUESTIONS)
            ms = (time.perf_counter() - started) * 1000

            meaning = response.choices["真正的意思"]
            print(f"\n對方回：「{reply}」（{ms:.0f} ms）")
            # 回應裡的選項順序每次不同，固定照題目定義的順序印
            for option in MEANINGS:
                p = meaning.probabilities[option]
                mark = "◀" if option == meaning.choice else ""
                print(f"  {option:　<5} {'█' * round(p * 30):<30} {p:.2f} {mark}")
            print(
                f"  confidence {meaning.confidence:.2f}，"
                f"火氣 {response.scores['火氣'].score:.1f}/3，"
                f"該馬上關心 {response.nouls['該馬上關心'].noul:.2f}"
            )


if __name__ == "__main__":
    main()
