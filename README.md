# copilot-workshop20260417

## 1.pomodoro の起動手順

```bash
cd 1.pomodoro
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

ブラウザで以下にアクセスします。

- `http://127.0.0.1:5000/`

## テスト実行

```bash
cd 1.pomodoro
source .venv/bin/activate
pytest -q
```
