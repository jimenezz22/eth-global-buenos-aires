# Phase 0: Preparation Checklist

**Branch:** `phase-0-preparation`
**Time:** 30 minutes
**Status:** In Progress

---

## ✅ Completed

- [x] Branch created: `phase-0-preparation`
- [x] Node.js verified: v23.6.0
- [x] Python verified: Python 3.9.6
- [x] Flask installed: `flask==3.1.2`
- [x] Flask-CORS installed: `flask-cors==6.0.1`
- [x] Identified project structure

---

## 📁 Project Structure

```
polymarket-agent/
├── my_agent/
│   ├── __init__.py
│   ├── ai_advisor.py
│   ├── pnl_calculator.py
│   ├── position.py
│   └── strategy.py
├── requirements.txt (175 dependencies)
├── HACKATHON_PLAN.md
└── PHASE_0_CHECKLIST.md (this file)
```

---

## 📝 Pending Tasks

- [ ] Verify current agent runs: `python3 main.py`
- [ ] Create Hedera testnet account (https://portal.hedera.com)
- [ ] Document Hedera credentials in `.env.hedera` (don't commit!)
- [ ] Add Flask to `requirements.txt`
- [ ] Create `.env.example` template
- [ ] Test basic imports from `my_agent` module

---

## 🔐 Hedera Testnet Setup (TO DO)

1. Go to https://portal.hedera.com
2. Create account
3. Get free testnet HBAR
4. Save credentials:
   ```
   HEDERA_ACCOUNT_ID=0.0.xxxxx
   HEDERA_PRIVATE_KEY=302e...
   ```

---

## 🎯 Next Phase

Once all tasks complete → Move to **Phase 1: Flask API Wrapper**

Branch: `phase-1-flask-api`
