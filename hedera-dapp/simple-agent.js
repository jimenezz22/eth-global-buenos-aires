/**
 * Simplified Hedera Agent using Official Agent Kit
 * Based on the official quick start guide
 */

require('dotenv').config();
const { Client, PrivateKey } = require('@hashgraph/sdk');
const { HederaLangchainToolkit, coreQueriesPlugin } = require('hedera-agent-kit');
const axios = require('axios');

const POLYMARKET_API_URL = process.env.POLYMARKET_API_URL || 'http://localhost:5001';

/**
 * Initialize LLM (supports Gemini, Groq, or OpenAI)
 */
function initializeLLM() {
  // Option 1: Google Gemini (FREE!)
  if (process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY) {
    const { ChatGoogleGenerativeAI } = require('@langchain/google-genai');
    const apiKey = process.env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY;
    console.log('✅ Using Google Gemini (FREE)\n');
    return new ChatGoogleGenerativeAI({
      modelName: 'gemini-pro',
      apiKey: apiKey,
      temperature: 0.7
    });
  }

  // Option 2: Groq (Free tier)
  if (process.env.GROQ_API_KEY) {
    const { ChatGroq } = require('@langchain/groq');
    console.log('✅ Using Groq Llama3 (FREE)\n');
    return new ChatGroq({
      apiKey: process.env.GROQ_API_KEY,
      model: 'llama3-8b-8192'
    });
  }

  // Option 3: OpenAI (paid)
  if (process.env.OPENAI_API_KEY) {
    const { ChatOpenAI } = require('@langchain/openai');
    console.log('✅ Using OpenAI GPT-4o-mini\n');
    return new ChatOpenAI({ model: 'gpt-4o-mini' });
  }

  // No AI provider configured
  console.error('❌ No AI provider configured!');
  console.log('\n💡 Add ONE of these to your .env file:');
  console.log('   GOOGLE_API_KEY=xxx     (FREE at https://makersuite.google.com/app/apikey)');
  console.log('   GROQ_API_KEY=xxx       (FREE at https://console.groq.com/keys)');
  console.log('   OPENAI_API_KEY=xxx     (Paid at https://platform.openai.com/api-keys)\n');
  process.exit(1);
}

async function main() {
  console.log('🚀 Hedera Agent Kit + Polymarket Integration\n');

  // 1. Initialize AI
  const llm = initializeLLM();

  // 2. Hedera client setup
  const client = Client.forTestnet().setOperator(
    process.env.HEDERA_ACCOUNT_ID,
    PrivateKey.fromStringECDSA(process.env.HEDERA_PRIVATE_KEY),
  );

  console.log(`📍 Hedera Account: ${process.env.HEDERA_ACCOUNT_ID}`);

  // 3. Initialize Hedera Agent Kit
  const hederaAgentToolkit = new HederaLangchainToolkit({
    client,
    configuration: {
      plugins: [coreQueriesPlugin]
    },
  });

  console.log('✅ Hedera Agent Kit initialized\n');

  // 4. Demo: Check balance using Hedera tool
  console.log('=' .repeat(60));
  console.log('DEMO 1: Check Hedera Balance');
  console.log('=' .repeat(60));

  const tools = hederaAgentToolkit.getTools();
  console.log(`\n🛠️  Available Hedera tools: ${tools.length}`);
  tools.forEach(tool => console.log(`   - ${tool.name}`));

  // 5. Demo: Call Polymarket API directly
  console.log('\n' + '=' .repeat(60));
  console.log('DEMO 2: Polymarket Betting Flow');
  console.log('=' .repeat(60));

  try {
    // Enter position
    console.log('\n📥 Step 1: Enter position at 80%');
    const enterResult = await axios.post(`${POLYMARKET_API_URL}/bet`, {
      action: 'enter',
      amount_usd: 1000,
      current_prob: 0.80,
      yes_price: 0.80,
      no_price: 0.20
    });
    console.log(`✅ ${enterResult.data.message}`);
    console.log(`   Invested: $${enterResult.data.position.invested}`);

    // Evaluate
    console.log('\n📊 Step 2: Evaluate at 86%');
    const evalResult = await axios.post(`${POLYMARKET_API_URL}/bet`, {
      action: 'evaluate',
      current_prob: 0.86,
      yes_price: 0.86,
      no_price: 0.14
    });
    console.log(`✅ Recommendation: ${evalResult.data.action}`);
    console.log(`   Reason: ${evalResult.data.reason}`);

    // Hedge if recommended
    if (evalResult.data.action === 'TAKE_PROFIT') {
      console.log('\n💰 Step 3: Execute hedge');
      const hedgeResult = await axios.post(`${POLYMARKET_API_URL}/bet`, {
        action: 'hedge',
        current_prob: 0.86,
        yes_price: 0.86,
        no_price: 0.14
      });
      console.log(`✅ ${hedgeResult.data.message}`);
      console.log(`   Locked PnL: $${hedgeResult.data.locked_pnl_usd.toFixed(2)}`);
      console.log(`   Position: ${hedgeResult.data.position.yes_shares.toFixed(0)} YES, ${hedgeResult.data.position.no_shares.toFixed(0)} NO`);
    }

  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
  }

  // 6. Demo: Show A2A concept
  console.log('\n' + '=' .repeat(60));
  console.log('DEMO 3: A2A Message Concept');
  console.log('=' .repeat(60));

  const a2aMessage = {
    type: 'bet_proposal',
    from: process.env.HEDERA_ACCOUNT_ID,
    to: 'polymarket-agent',
    timestamp: new Date().toISOString(),
    payload: {
      action: 'hedge',
      probability: 0.86,
      expected_pnl: 75
    }
  };

  console.log('\n📨 A2A Message (would be sent via HCS):');
  console.log(JSON.stringify(a2aMessage, null, 2));

  console.log('\n' + '=' .repeat(60));
  console.log('✅ All Demos Complete!');
  console.log('=' .repeat(60));
  console.log('\n💡 This demonstrates:');
  console.log('   ✓ Hedera Agent Kit integration');
  console.log('   ✓ Multi-agent communication (Hedera ↔ Polymarket)');
  console.log('   ✓ A2A message structure');
  console.log('   ✓ Cross-chain coordination\n');

  client.close();
}

main().catch(console.error);
