.PHONY: test api web up
test:    ; cd backend && python -m pytest -q
api:     ; cd backend && ALLOW_LOCAL_REPOS=true uvicorn app.main:app --reload
web:     ; cd frontend && npm run dev
up:      ; docker compose up --build
bench:   ; cd backend && python ../benchmarks/run.py
