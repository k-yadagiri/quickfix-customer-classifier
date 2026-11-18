# Evaluation run

- Date: 2026-11-19 01:43
- Model: `qwen2.5:3b`
- API: http://localhost:8000
- Messages: 40
- Machine (auto): Windows 11, Intel64 Family 6 Model 154 Stepping 4, GenuineIntel
- Laptop RAM / GPU: **<fill in by hand>**

## Accuracy

| Group | Intent | Category | Urgency | All three correct |
|---|---|---|---|---|
| Overall (40) | 37/40 (92.5%) | 39/40 (97.5%) | 39/40 (97.5%) | 37/40 (92.5%) |
| English (20) | 20/20 (100.0%) | 20/20 (100.0%) | 20/20 (100.0%) | 20/20 (100.0%) |
| Tenglish (14) | 12/14 (85.7%) | 14/14 (100.0%) | 14/14 (100.0%) | 12/14 (85.7%) |
| Telugu (6) | 5/6 (83.3%) | 5/6 (83.3%) | 5/6 (83.3%) | 5/6 (83.3%) |

## Speed and reliability

- Average response time: 19889 ms
- Slowest response: 35777 ms (message 35)
- Messages where the model's first answer was invalid (before retry): 0 (0 invalid answers in total)
- Messages that ended with `needs_review = true` (fallback used): 0
- Requests that failed (HTTP/network error): 0

## Wrong answers

| ID | Lang | Message | Expected (intent / category / urgency) | Got (intent / category / urgency) | Why (fill in) |
|---|---|---|---|---|---|
| 23 | tenglish | Mee technician ninna vachadu kani fan inka tiragatledu. Malli vachi chudandi | complaint / electrical / normal | **status_check** / electrical / normal | TODO |
| 31 | tenglish | Mee carpenter door sarigga fix cheyyaledu, malli open aipotundi. Waste of money | complaint / carpentry / normal | **book_service** / carpentry / normal | TODO |
| 36 | telugu | ఏసీ సర్వీస్ బుకింగ్ ని రేపటికి మార్చండి | reschedule / ac_repair / normal | **cancel** / **none** / **low** | TODO |
