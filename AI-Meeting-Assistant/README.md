# AI Meeting Assistant

AI Meeting Assistant is a lightweight Streamlit MVP for converting raw meeting transcripts into meeting summaries, decisions, open issues, and action items.

## Features

- Create a meeting with a name, date, participants, and transcript
- Analyze the transcript using a mock AI function
- Review meeting overview, topics, decisions, and key information
- Edit action items and mark them as completed
- Start a new meeting at any time

## Project Structure

```text
AI-Meeting-Assistant/
├── app.py
├── requirements.txt
├── README.md
├── services/
│   ├── __init__.py
│   └── meeting_analyzer.py
└── .streamlit/
```

## Setup

1. Open a terminal.
2. Go to the project folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local URL shown by Streamlit in your browser.
