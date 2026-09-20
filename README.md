# jevtest

用「他說『好』，是真的好嗎？」這個情境（聽出話裡沒明講的意思）來說明 [TypeSafe Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)（System One 模型）和一般 LLM 的差別。Jev 與對照用的 LLM 都透過 [OpenRouter](https://openrouter.ai/typesafe) 呼叫，只需要一把 OpenRouter 金鑰。

## 這個範例在做什麼

「好」和「好。」差很多；「隨便」通常不是隨便；主管說「再研究看看」多半是不行。這種話沒有標準答案，正好用來看一個模型怎麼表達「我不確定」。

Jev 不產生文字，只回答三種型別化問題，每個答案都附機率：

| 型別 | 範例裡的問題 | 回傳 |
| --- | --- | --- |
| `Choice` | 真正的意思（真的沒事／有點失落／在生氣／在試探你） | `choice`、各選項的 `probabilities`、`confidence` |
| `Score` | 火氣（平靜到快要爆炸，四級） | `score`、各級的 `probabilities`、`confidence` |
| `Noul` | 該馬上關心嗎 | `noul`（答案為「是」的機率） |

## 互動式 demo

```bash
cp .env.example .env   # 填入 OPENROUTER_API_KEY
uv sync
uv run uvicorn app:app --port 8010
# 打開 http://127.0.0.1:8010
```

- **邊打字邊判斷：** 在對方的對話框打字，每停一下就把整段對話送給 Jev 一次，機率長條跟著變。也可以點現成的句子，讓它逐字自動打出來。
- **機率軌跡：** 折線圖畫出每一次呼叫後各選項的機率，滑鼠移上去可以看那一次送出的是哪句話。
- **一次多問 30 題：** 同一個 request 再附上 30 題是非題（生氣、在敷衍、想結束話題等等），30 個小指針同時更新。另有按鈕現場實測問 1、5、15、30 題各要多久。
- **門檻刻度尺：** 指針是 Jev 的 confidence，兩個門檻可以拖動，對應「直接問清楚／先試探／直接行動」三個分支，並標出會執行到的 Python 分支。
- **LLM 對照：** 同一段對話和同一組問題送給一般 LLM 一次，顯示耗時、費用、輸出能不能直接解析，以及同樣的時間和費用 Jev 可以回答幾次。
- 三個情境：另一半、主管、朋友。每個情境的 questions 都可以在頁面上直接改。

金鑰只存在伺服器端（`app.py`），瀏覽器拿不到。頁面顯示的毫秒數是伺服器到 OpenRouter 的來回時間。

## 實測數字（2026-09-20，從台灣連線）

- Jev 一次來回約 350 到 600 毫秒，偶爾到 1 秒。官方說的 70 到 500 毫秒是在美西量的。
- 題數對延遲影響很小：問 1 題 396 ms，問 30 題 567 ms；33 題一次問完約 0.000045 美元。
- 同一段對話加 33 題送給 `google/gemini-3.5-flash-lite`：2747 ms、0.002 美元，約慢 5 倍、貴 60 倍。送給 `anthropic/claude-sonnet-5`（只問 3 題）：7422 ms、0.0047 美元。
- 同一句話重複問，判斷結果一致，但機率會有約 ±0.03 的浮動，不是完全確定性的。
- 中文潛台詞讀得出來：「隨便你」判為在生氣 0.71，「好啊～玩得開心」判為真的沒事 0.64；「好」加上句號後，真的沒事從 0.35 降到 0.22。

## 命令列版本

```bash
uv run python main.py
```

對同一句「我今天跟同事聚餐，會晚點回家喔」，依序送出六種回覆，印出每一種的機率分布。

## Jev 怎麼走 OpenRouter

Jev 在 OpenRouter 上為 beta，走獨立的 `POST /api/v1/systemone` 端點，所以不會出現在一般的 `/api/v1/models` 清單裡。官方 `typesafe-sdk` 只要改 base URL 就能用：

```python
TypeSafeClient(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api")
```

模型 ID 可寫 `jev-latest`、`jev-1.13`，或帶前綴的 `typesafe/jev-1.13`。

| 環境變數 | 說明 |
| --- | --- |
| `OPENROUTER_API_KEY` | 從 <https://openrouter.ai/settings/keys> 取得，Jev 與 LLM 共用 |
| `JEV_MODEL` | 選填，預設 `jev-latest` |
| `OPENROUTER_MODEL` | 選填，對照用的 LLM，預設 `google/gemini-3.5-flash-lite` |

## 參考

- [TypeSafe 文件](https://docs.typesafe.ai/)
- [OpenRouter：TypeSafe SDK 指南](https://openrouter.ai/docs/guides/community/typesafe-sdk)
- [Confidence-gated routing pattern](https://docs.typesafe.ai/patterns/confidence-routing)
