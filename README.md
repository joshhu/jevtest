# 情緒測謊器

嘴上說「好」，心裡真的好嗎？用這個情境展示 [TypeSafe Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)（System One 模型）和一般 LLM 的差別。兩者都透過 [OpenRouter](https://openrouter.ai/typesafe) 呼叫，只需要一把金鑰。

## Jev 是什麼

Jev 不產生文字，只在你定義的選項上給機率。

| 型別 | 範例裡的問題 | 回傳 |
| --- | --- | --- |
| `Choice` | 真正的意思（四選一） | `choice`、各選項 `probabilities`、`confidence` |
| `Score` | 火氣（四級） | `score`、各級 `probabilities`、`confidence` |
| `Noul` | 該馬上關心嗎 | `noul`（「是」的機率） |

## 執行

需要 [uv](https://docs.astral.sh/uv/)。

```bash
cp .env.example .env   # 填入 OPENROUTER_API_KEY
uv sync
uv run uvicorn app:app --port 8010   # 開啟 http://127.0.0.1:8010
uv run python main.py                # 命令列版
```

| 環境變數 | 說明 |
| --- | --- |
| `OPENROUTER_API_KEY` | [取得金鑰](https://openrouter.ai/settings/keys)，Jev 與 LLM 共用 |
| `JEV_MODEL` | 選填，預設 `jev-latest` |
| `OPENROUTER_MODEL` | 選填，對照用 LLM，預設 `google/gemini-3.5-flash-lite` |

金鑰只留在伺服器端（`app.py`），瀏覽器拿不到。

## 頁面功能

- **即時判斷：** 打字或點現成句子，每次停頓就問 Jev 一次，機率長條跟著變。
- **機率軌跡：** 每個字如何改變各選項的機率。
- **多問 30 題：** 同一個 request 附上 30 題是非題，並可實測 1、5、15、30 題的耗時。
- **門檻刻度尺：** 拖動兩個 confidence 門檻，對應「直接問／先試探／直接行動」與 Python 分支。
- **LLM 對照：** 同一題送給一般 LLM，比較耗時、費用與輸出格式。
- 三個情境：另一半、主管、朋友。questions 可在頁面上直接改。

## 實測（2026-09-20，台灣連線）

- Jev 一次來回 350 到 600 ms，偶爾 1 秒。官方的 70 到 500 ms 是在美西量的。
- 問 1 題 396 ms，問 30 題 567 ms；33 題約 0.000045 美元。
- 同樣 33 題給 `google/gemini-3.5-flash-lite`：2747 ms、0.002 美元，約慢 5 倍、貴 60 倍。
- 同一句話重複問，結論一致，機率浮動約 ±0.03。
- 中文讀得懂：「隨便你」在生氣 0.71；「好啊～玩得開心」真的沒事 0.64；「好」加句號後，真的沒事從 0.35 降到 0.22。

## Jev 怎麼走 OpenRouter

Jev 走獨立的 `POST /api/v1/systemone` 端點，不在 `/api/v1/models` 清單裡。官方 `typesafe-sdk` 改 base URL 即可：

```python
TypeSafeClient(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api")
```

模型 ID 可寫 `jev-latest`、`jev-1.13` 或 `typesafe/jev-1.13`。

## 參考

- [TypeSafe 文件](https://docs.typesafe.ai/)
- [OpenRouter：TypeSafe SDK 指南](https://openrouter.ai/docs/guides/community/typesafe-sdk)
- [Confidence-gated routing](https://docs.typesafe.ai/patterns/confidence-routing)
