# ETH Global Buenos Aires 2025 - Hedera Integration Plan

**Target Prize:** Best Use of Hedera Agent Kit & Google A2A - $4,000

**Time Budget:** 8-10 hours

**Goal:** Create Hedera AI Agent that interacts with existing Polymarket hedge agent via A2A standard

---

## 📋 Execution Plan

### **Phase 0: Preparation (30 min)**
**Branch:** `main` (pre-work)

- [ ] Verify current Polymarket agent works (`python main.py`)
- [ ] Create Hedera testnet account at https://portal.hedera.com
- [ ] Get free testnet HBAR
- [ ] Verify Node.js installed (`node --version`)
- [ ] Install Flask dependencies: `pip install flask flask-cors`
- [ ] Document current repo structure

**Deliverables:**
- Hedera testnet credentials (.env ready)
- Working baseline agent
- Dependencies installed

---

### **Phase 1: Flask API Wrapper (1 hour)**
**Branch:** `phase-1-flask-api`

Tasks:
- [ ] Create `api.py` in root directory
- [ ] Expose POST `/bet` endpoint that calls existing strategy
- [ ] Test with curl: `curl -X POST http://localhost:5000/bet -H "Content-Type: application/json" -d '{"amount_usd": 1000}'`
- [ ] Add `flask` and `flask-cors` to `requirements.txt`
- [ ] Document API in README

**API Contract:**
```
POST /bet
Body: { "market_slug": "...", "amount_usd": 1000 }
Response: { "success": true, "locked_pnl_usd": 62.5, "message": "Hedge executed" }
```

**Deliverables:**
- `api.py` (working Flask server)
- Updated `requirements.txt`
- API documentation

---

### **Phase 2: Hedera Setup (1.5 hours)**
**Branch:** `phase-2-hedera-setup`

Tasks:
- [ ] Create `/hedera-dapp` folder
- [ ] `npm init -y`
- [ ] Install dependencies: `npm install @hashgraph/sdk dotenv axios`
- [ ] Create `.env.example` with required vars
- [ ] Configure `.env` with testnet credentials
- [ ] Create basic `agent.js` that connects to Hedera testnet
- [ ] Test connection with simple account balance query

**Environment Variables:**
```
HEDERA_ACCOUNT_ID=0.0.xxxxx
HEDERA_PRIVATE_KEY=302...
OPENAI_API_KEY=sk-... (optional, can use Groq free)
POLYMARKET_API_URL=http://localhost:5000
```

**Deliverables:**
- `/hedera-dapp` folder structure
- `package.json` with dependencies
- `.env.example` template
- Basic `agent.js` connecting to testnet

---

### **Phase 3: A2A Integration (2 hours)**
**Branch:** `phase-3-a2a-integration`

Tasks:
- [ ] Implement custom tool in `agent.js` to call Polymarket API
- [ ] Add A2A message formatting (can simulate with JSON logs)
- [ ] Integrate HCS (Hedera Consensus Service) for message logging
- [ ] Add HTS (Hedera Token Service) transfer for settlement
- [ ] Create negotiation flow: propose bet → execute → settle

**A2A Flow:**
1. Hedera Agent creates bet proposal
2. Sends A2A message (via HCS or simulated)
3. Calls Polymarket API via custom tool
4. Receives response
5. If profitable, settles 10 HBAR via HTS

**Deliverables:**
- Complete `agent.js` with A2A tools
- HCS topic creation (or simulation)
- HTS settlement logic
- Logs showing A2A negotiation

---

### **Phase 4: Frontend (1.5 hours)**
**Branch:** `phase-4-frontend`

Tasks:
- [ ] Create `/hedera-dapp/public/index.html`
- [ ] Create `/hedera-dapp/public/app.js`
- [ ] Add "Propose Bet" button
- [ ] Display A2A conversation/negotiation
- [ ] Show Hedera transaction links (HashScan testnet)
- [ ] Add simple styling (minimal but clean)

**UI Elements:**
- Button: "Propose Bet on BTC <90k"
- Chat-like display showing A2A messages
- Result display: locked PnL + HBAR settlement tx
- Links to Hedera explorer

**Deliverables:**
- Working frontend (can run locally)
- Visual demo of agent negotiation
- Transaction proof on testnet

---

### **Phase 5: Testing + Demo (2 hours)**
**Branch:** `phase-5-demo`

Tasks:
- [ ] End-to-end test: Frontend → Hedera Agent → Polymarket API
- [ ] Record Loom video (2 minutes max):
  - Show bet proposal
  - A2A negotiation
  - Polymarket hedge execution
  - Hedera settlement transaction
- [ ] Update main README.md with:
  - Project title: "Cross-Chain AI Betting: Hedera negotiates, Polymarket executes"
  - Quick start (3 steps)
  - Architecture diagram
  - Video link
  - Prize qualifications checklist
- [ ] Create `/hedera-dapp/README.md` with setup instructions
- [ ] Final code cleanup
- [ ] Merge all branches to `hedera-hackathon`
- [ ] Push to GitHub
- [ ] Submit to ETHGlobal

**Video Script (2 min):**
1. (0:00-0:20) Intro: "Cross-chain AI agent coordination with Hedera + Polymarket"
2. (0:20-0:40) Show existing Polymarket hedge agent working
3. (0:40-1:20) Demo: Click button → A2A negotiation → API call → settlement
4. (1:20-1:40) Show Hedera explorer transaction
5. (1:40-2:00) Explain how it meets prize requirements

**Deliverables:**
- 2-minute demo video (Loom)
- Updated README files
- Clean, documented code
- GitHub repo ready for judges
- ETHGlobal submission

---

## ✅ Prize Qualification Requirements

- [x] **Multi-agent communication** - Hedera agent ↔ Polymarket agent via A2A
- [x] **Agent Kit integration** - Built with Hedera Agent Kit + adaptors
- [x] **Open-source deliverables** - Public repo + documentation + video
- [x] **BONUS: Multiple Hedera services** - HCS (messaging) + HTS (settlement)
- [x] **BONUS: Advanced features** - Real hedging strategy (not just chat)

---

## 🎯 Architecture Overview

```
┌────────────────────┐     A2A Messages      ┌─────────────────────┐
│  Hedera Agent (JS) │ ──────────────────► │ Polymarket Agent    │
│  - Agent Kit       │ ◄──────────────────── │ (Python/Flask API)  │
│  - HCS messaging   │   HTTP POST /bet      │ - Hedge Strategy    │
│  - HTS settlement  │                        │ - Position Mgmt     │
└────────────────────┘                        └─────────────────────┘
         │                                             │
         │ HCS Topic (logs)                           │
         │ HTS Transfer (settlement)                  │
         ▼                                            ▼
   Hedera Testnet                              Polymarket (Polygon)
```

---

## 🚨 Critical Success Factors

1. **Keep it simple** - Don't over-engineer, judges value working demos over complexity
2. **Video is key** - Clear, concise demonstration of A2A flow
3. **Document everything** - README should allow judges to run it
4. **Show real value** - Your hedge strategy is unique, emphasize it
5. **Test on testnet** - Use Hedera testnet, don't risk mainnet funds

---

## 📚 Resources

- Hedera Agent Kit Docs: https://docs.hedera.com/hedera/open-source-solutions/ai-studio-on-hedera/hedera-ai-agent-kit
- Hedera Testnet Portal: https://portal.hedera.com
- Google A2A Standard: (reference in code comments if spec not fully implemented)
- HashScan Explorer (testnet): https://hashscan.io/testnet
- ETHGlobal Submission: (link when available)

---

## 🔄 Branch Strategy

Each phase = one branch. Merge to `hedera-hackathon` when phase complete.

```
main
 └─ phase-1-flask-api
     └─ phase-2-hedera-setup
         └─ phase-3-a2a-integration
             └─ phase-4-frontend
                 └─ phase-5-demo
                     └─ hedera-hackathon (final merge)
```

**Commands:**
```bash
git checkout -b phase-1-flask-api
# ... work ...
git add . && git commit -m "feat: add Flask API wrapper"
git checkout -b phase-2-hedera-setup
# ... continue ...
```

---

**Last Updated:** 2025-11-21
**Hackathon:** ETH Global Buenos Aires 2025
**Developer:** @devJimenezz22
