# QuickFix AI Customer Support Classifier

**Multilingual AI-powered customer message classification using FastAPI, Ollama, and Qwen 2.5 3B.**

QuickFix AI is a customer support message classification application built for a fictional home-services company, QuickFix Home Services.

It accepts customer messages in **English, Telugu, and Tenglish** and identifies the customer's intent, service category, safety risk, urgency, and a short AI-generated summary.

## Live Demo

- **Hugging Face Application:** https://giriyadagiri-quickfix-ai-customer-support.hf.space
- **GitHub Repository:** https://github.com/k-yadagiri/quickfix-customer-classifier
- **Backend Health Check:** https://mounted-broader-mats-aspect.trycloudflare.com/health
- **Interactive API Documentation (Swagger):** https://mounted-broader-mats-aspect.trycloudflare.com/docs

> Note: The backend root URL does not provide a homepage. Use `/health` to check backend availability and `/docs` to explore and test the API.

## Features

- Multilingual customer message classification (English, Telugu, and Tenglish).
- Open-source local LLM using Ollama and Qwen 2.5 3B.
- Intent and service-category identification.
- Safety-risk detection.
- Python-based urgency determination.
- JSON output validation, retry, and fallback handling.
- SQLite database storage.
- REST API built using FastAPI.
- Gradio-based user interface.
- Automated tests using Pytest.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| LLM runtime | Ollama |
| AI model | Qwen 2.5 3B |
| Backend | FastAPI |
| Frontend | Gradio |
| Database | SQLite |
| API communication | REST API |
| Deployment | Hugging Face Spaces + Cloudflare Tunnel |
| Testing | Pytest |

## How It Works

1. Customer enters a message through the Gradio interface.
2. Gradio sends the message to the FastAPI `/classify` endpoint.
3. FastAPI sends the message to the local Ollama model.
4. Qwen 2.5 3B identifies the intent, category, safety risk, and summary.
5. Python validates the model output and retries once if necessary.
6. Python rules determine urgency.
7. The result is stored in SQLite and returned to the interface.

### Classification Logic

**AI model responsibilities:**
- Intent
- Service category
- Safety risk
- Short summary

**Python responsibilities:**
- Validate allowed intent and category labels.
- Validate the safety-risk boolean.
- Retry invalid model responses once.
- Apply fallback handling if the response remains invalid.
- Determine urgency using safety rules and classification results.
- Enforce the rule that `other` intent maps to `none` category.

### Supported Intents

`book_service`, `reschedule`, `cancel`, `complaint`, `price_enquiry`, `status_check`, `other`

### Supported Service Categories

`plumbing`, `electrical`, `ac_repair`, `appliance_repair`, `cleaning`, `pest_control`, `carpentry`, `painting`, `none`

### Urgency Levels

- `high`: Safety risk detected.
- `normal`: Regular service-related requests.
- `low`: Price enquiries, cancellations, and other requests, unless a safety risk is detected.

## Project Structure

```text
quickfix-customer-classifier/
│
├── app/
│   ├── main.py
│   ├── classifier.py
│   ├── prompt.py
│   ├── urgency.py
│   ├── labels.py
│   ├── db.py
│   ├── schemas.py
│   └── config.py
│
├── data/
│   └── quickfix_messages.csv
│
├── tests/
│
├── .env.example
├── .gitignore
├── eval.py
├── EVAL_run.md
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Run Locally

### 1. Install Ollama

Download and install Ollama from:

https://ollama.com/

Pull the required model:

```powershell
ollama pull qwen2.5:3b
ollama list
```

Make sure Ollama is running.

### 2. Clone the repository

```powershell
git clone https://github.com/k-yadagiri/quickfix-customer-classifier.git

cd quickfix-customer-classifier
```

### 3. Create a virtual environment

```powershell
python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
copy .env.example .env
```

The default configuration uses the local Ollama endpoint.

### 5. Start the FastAPI backend

```powershell
uvicorn app.main:app --reload
```

Open the API documentation:

http://localhost:8000/docs

### 6. Run automated tests

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Run:

```powershell
python -m pytest -q
```

**Latest verified test result:** 41 passed.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/classify` | Classifies a customer message |
| GET | `/messages` | Retrieves saved classification records |
| GET | `/stats` | Returns classification statistics |
| GET | `/health` | Checks backend health |

Example request:

```json
{
  "message": "My AC is not cooling properly. Please send a technician tomorrow."
}
```

Example response:

```json
{
  "message": "My AC is not cooling properly. Please send a technician tomorrow.",
  "intent": "book_service",
  "category": "ac_repair",
  "urgency": "normal",
  "safety_risk": false,
  "summary": "Customer requests a new AC technician visit for tomorrow."
}
```

The actual API response also includes additional fields such as the record ID, model name, response time, review status, and invalid-attempt count.

## Evaluation

The project includes an evaluation script:

```powershell
python eval.py
```

It evaluates the classifier against 40 labelled customer messages and reports:

- Intent accuracy.
- Category accuracy.
- Urgency accuracy.
- Language-wise accuracy.
- Average and slowest response times.
- Invalid model outputs.
- Incorrect predictions.

A previous baseline evaluation achieved **37 correct predictions out of 40 (92.5%)**. This was measured before the latest prompt correction; the final evaluation has not been rerun.

The evaluation script is included in the repository so that results can be reproduced.

## Testing

The project has **41 passing automated tests**.

Tests cover:

- Urgency determination.
- Invalid model response handling.
- Retry and fallback behaviour.
- API endpoint behaviour.
- Input validation.

The automated tests use a simulated model response and do not require Ollama to be running.

## Environment Variables

| Variable | Purpose |
|---|---|
| `LLM_BASE_URL` | Ollama OpenAI-compatible API endpoint |
| `LLM_MODEL` | Model name (`qwen2.5:3b`) |
| `LLM_API_KEY` | API key configuration |
| `LLM_TIMEOUT_SECONDS` | Model request timeout |
| `DB_PATH` | SQLite database location |

## Known Limitations

- The backend currently depends on a local computer running Ollama.
- Cloudflare Quick Tunnel URLs are temporary and can change.
- CPU-based inference can be slow, especially for longer messages.
- A small 3B model can occasionally confuse similar intents.
- Telugu and Tenglish spelling variations may affect classification.
- Each customer message is classified independently without conversation history.
- Safety keyword matching may produce false positives.
- The API does not currently implement authentication or rate limiting.
- SQLite is suitable for this small demonstration but is not a production-scale database.

## Future Improvements

- Deploy the backend on a persistent hosting platform that supports the required open-source model.
- Improve Telugu and Tenglish classification accuracy.
- Optimize inference speed.
- Add authentication and API rate limiting.
- Introduce conversation context.
- Expand the labelled evaluation dataset.
- Add a more comprehensive monitoring and analytics dashboard.

## Author

**Yadagiri Kuruva**

B.Tech – Computer Science and Engineering (AI & DS)

GitHub: https://github.com/k-yadagiri

---

**QuickFix AI Customer Support Classifier**  
Built with Python, FastAPI, Ollama, Qwen 2.5 3B, SQLite, and Gradio.
