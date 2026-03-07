# Lens v1

Lens is a Streamlit batch sentiment analysis app backed by PostgreSQL and the OpenAI API.

## Run locally

1. Create a virtual environment and install dependencies:
   `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set `DATABASE_URL`. Set `OPENAI_API_KEY` only for live mode.
3. Start the app:
   `streamlit run lens/app.py`

## Modes

- Demo mode: `OPENAI_API_KEY` is unset. The app loads seeded history data and disables live pipeline execution.
- Live mode: `OPENAI_API_KEY` is set. The app supports upload, validation, and pipeline execution.

## Deployment

Deploy on Streamlit Cloud with:

- `DATABASE_URL`
- `OPENAI_API_KEY` (optional for demo-only deployment)
- `LENS_CREATED_BY` (optional)

Do not upload sensitive production data to the public portfolio deployment.
