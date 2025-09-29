## Inya.ai Integration Notes

### 1) Import config
- Upload `inya.config.yaml` into your Inya.ai workspace as the agent configuration.

### 2) Set environment/API endpoints
- Ensure your FastAPI server runs locally on `http://localhost:8000`:
  - Start with: `uvicorn app:app --reload --port 8000`
  - Keep `catalog.json` in the same folder as `app.py`.

### 3) Map intents → actions & slot filling
- Greeting: detect `greet` and respond.
- Qualification: on `qualify_need` and `profile_risk`, prompt to fill slots defined in `slots` section of `inya.config.yaml`.
- Quote: when `request_quote` is triggered and required slots are present, call action `get_quote` (POST `/quote`).
- Negotiation: handle `handle_objection`, `negotiate`, `compare_policies`, `add_rider` to adjust pitch; you may call `get_policies` to fetch catalog context.
- Compliance: after showing recommendations, always surface `disclaimer` from `/quote` response.
- Closing: on `close_sale`, proceed with your checkout flow; on `schedule_callback` or `escalate_human`, call `create_handoff` (POST `/handoff`).

### 4) HTTP action payload bindings
- The `get_quote` action uses templated bindings:
  - All slots feed directly into `/quote` request body.
  - Response key `recommended` returns an array of plans; `disclaimer` is included.

### 5) Testing locally
1. Install deps: `pip install -r requirements.txt`
2. Run server: `uvicorn app:app --reload --port 8000`
3. Open docs: `http://localhost:8000/docs`
4. In Inya.ai, trigger intents and verify action calls and responses.

### 6) Notes on scoring (stub)
- `/quote` computes simple heuristic scores by:
  - Aligning risk tolerance with policy type
  - Rewarding family health and term if dependents > 0
  - Matching vehicle type for motor
  - Matching preferred premium band against the minimum premium
  - Soft age eligibility overlap
- It returns top 3 policies with a short rationale and a standard disclaimer.

### 7) CORS & security
- CORS is enabled for all origins by default for hackathon convenience. Restrict as needed in production.


