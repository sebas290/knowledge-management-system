# Deployment

## Streamlit Community Cloud (recommended)

1. Upload this folder to a public GitHub repository. `app.py`, `requirements.txt`, and the `kms/`
   and `data/` folders must be at the root of the repository.
2. Sign in at <https://share.streamlit.io> with your GitHub account.
3. Click **Create app** → **Deploy a public app from GitHub**.
4. Fill in the repository, branch `main`, and main file path `app.py`.
5. Open **Advanced settings** and choose **Python 3.12**.
6. Click **Deploy**. The first build installs `requirements.txt` and takes about 2–4 minutes.
7. Copy the public URL (for example, `https://<your-app>.streamlit.app`) into the README and the
   presentation.

No secrets or API keys are needed. Each visitor gets their own session, with their own search history,
conversation, and added documents. Nothing that a visitor adds is saved to the repository.

## Hugging Face Spaces (alternative)

1. Create a Space with the **Streamlit** SDK.
2. Upload the same files, or push the repository to the Space.
3. Add this header at the top of the README of the Space:

```yaml
---
title: Altavista Knowledge Management System
sdk: streamlit
app_file: app.py
---
```

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: kms` | Run the commands from the repository root, where `app.py` is |
| The build fails on Streamlit Cloud | Check that Python 3.12 was selected in Advanced settings |
| The graph is blank | Wait a few seconds while the layout stabilizes, or click the fit button (bottom right of the graph) |
| The app "falls asleep" | Free Streamlit apps sleep after a period without visits; open the link and click "wake up" |
