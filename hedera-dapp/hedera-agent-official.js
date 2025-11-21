/**
 * Hedera Agent using Official Agent Kit
 *
 * Uses hedera-agent-kit with LangChain to create an AI agent
 * that can interact with Hedera network and Polymarket API.
 */

require('dotenv').config();
const { ChatPromptTemplate } = require('@langchain/core/prompts');
const { Client, PrivateKey } = require('@hashgraph/sdk');
const { HederaLangchainToolkit, coreQueriesPlugin, coreConsensusPlugin } = require('hedera-agent-kit');
const { ChatOpenAI } = require('@langchain/openai');
const axios = require('axios');
const { DynamicStructuredTool } = require('@langchain/core/tools');
const { z } = require('zod');

const POLYMARKET_API_URL = process.env.POLYMARKET_API_URL || 'http://localhost:5001';

/**
 * Create custom Polymarket tool for the agent
 */
function createPolymarketTool() {
  return new DynamicStructuredTool({
    name: 'polymarket_bet',
    description: `
      Execute betting operations on Polymarket prediction markets.

      Actions:
      - enter: Open initial position
      - evaluate: Get recommendation (TAKE_PROFIT, STOP_LOSS, HOLD)
      - hedge: Execute take-profit hedge strategy
      - exit: Execute stop-loss exit

      The agent uses an advanced hedging strategy that locks profit
      by selling YES shares and buying NO shares when probability rises.
    `,
    schema: z.object({
      action: z.enum(['enter', 'evaluate', 'hedge', 'exit'])
        .describe('The betting action to perform'),
      amount_usd: z.number().optional().default(1000)
        .describe('Investment amount in USD (for entry)'),
      current_prob: z.number().min(0).max(1)
        .describe('Current market probability (0.0-1.0)'),
      yes_price: z.number().min(0).max(1).optional()
        .describe('YES share price (defaults to current_prob)'),
      no_price: z.number().min(0).max(1).optional()
        .describe('NO share price (defaults to 1-current_prob)'),
    }),
    func: async ({ action, amount_usd, current_prob, yes_price, no_price }) => {
      try {
        const response = await axios.post(`${POLYMARKET_API_URL}/bet`, {
          action,
          amount_usd,
          current_prob,
          yes_price: yes_price || current_prob,
          no_price: no_price || (1 - current_prob)
        });

        const result = response.data;

        // Format response for AI
        if (result.success) {
          switch (result.action) {
            case 'ENTRY':
              return `Successfully entered position: ${result.message}. Invested $${result.position.invested}.`;

            case 'TAKE_PROFIT':
              return `Recommendation: TAKE PROFIT. ${result.reason}. Current position: ${result.position.yes_shares.toFixed(0)} YES shares.`;

            case 'HEDGE':
              return `Hedge executed successfully! Locked PnL: $${result.locked_pnl_usd.toFixed(2)}. ${result.message}`;

            case 'STOP_LOSS':
              return `Stop-loss executed. Final PnL: $${result.final_pnl_usd.toFixed(2)}. ${result.message}`;

            case 'HOLD':
              return `Recommendation: HOLD. ${result.reason}. Unrealized PnL: $${result.unrealized_pnl_usd?.toFixed(2) || 0}`;

            default:
              return JSON.stringify(result);
          }
        } else {
          return `Error: ${result.error}`;
        }
      } catch (error) {
        return `Failed to execute Polymarket action: ${error.message}`;
      }
    },
  });
}

/**
 * Main agent function
 */
async function createHederaPolymarketAgent() {
  console.log('🚀 Initializing Hedera Agent with Official Agent Kit...\n');

  // 1. Initialize AI model (OpenAI or Groq)
  let llm;
  if (process.env.OPENAI_API_KEY) {
    llm = new ChatOpenAI({
      model: 'gpt-4o-mini',
      temperature: 0.7
    });
    console.log('✅ Using OpenAI GPT-4o-mini');
  } else if (process.env.GROQ_API_KEY) {
    const { ChatGroq } = require('@langchain/groq');
    llm = new ChatGroq({ model: 'llama3-8b-8192' });
    console.log('✅ Using Groq Llama3');
  } else {
    console.error('❌ No AI provider configured. Set OPENAI_API_KEY or GROQ_API_KEY in .env');
    process.exit(1);
  }

  // 2. Setup Hedera client
  const client = Client.forTestnet().setOperator(
    process.env.HEDERA_ACCOUNT_ID,
    PrivateKey.fromStringECDSA(process.env.HEDERA_PRIVATE_KEY)
  );

  console.log(`📍 Hedera Account: ${process.env.HEDERA_ACCOUNT_ID}`);

  // 3. Initialize Hedera Agent Kit
  const hederaAgentToolkit = new HederaLangchainToolkit({
    client,
    configuration: {
      plugins: [
        coreQueriesPlugin,    // Account balance, transaction info
        coreConsensusPlugin   // HCS topics for A2A messages
      ]
    },
  });

  console.log('✅ Hedera Agent Kit initialized\n');

  // 4. Get Hedera tools + custom Polymarket tool
  const hederaTools = hederaAgentToolkit.getTools();
  const polymarketTool = createPolymarketTool();
  const allTools = [...hederaTools, polymarketTool];

  console.log(`🛠️  Available tools: ${allTools.length}`);
  console.log(`   - Hedera tools: ${hederaTools.length}`);
  console.log(`   - Polymarket tool: 1\n`);

  // 5. Create agent prompt
  const prompt = ChatPromptTemplate.fromMessages([
    [
      'system',
      `You are a cross-chain AI betting agent that coordinates between Hedera network and Polymarket prediction markets.

Your capabilities:
1. Check Hedera account balance and network info
2. Send A2A (Agent-to-Agent) messages via Hedera Consensus Service
3. Execute betting strategies on Polymarket:
   - Enter positions at specific probabilities
   - Evaluate current positions for profit-taking
   - Execute hedges to lock in profits
   - Exit positions when needed

Strategy:
- Enter YES positions when probability is attractive (e.g., 80%)
- When probability rises (e.g., 86%), recommend TAKE_PROFIT
- Execute hedge: sell YES shares, buy NO shares to lock profit
- This guarantees profit regardless of final outcome

Always explain your reasoning and the expected outcomes.`
    ],
    ['placeholder', '{chat_history}'],
    ['human', '{input}'],
    ['placeholder', '{agent_scratchpad}'],
  ]);

  // 6. Create the agent
  const agent = createToolCallingAgent({
    llm,
    tools: allTools,
    prompt,
  });

  // 7. Wrap in executor
  const agentExecutor = new AgentExecutor({
    agent,
    tools: allTools,
    verbose: true, // Show agent reasoning
  });

  return agentExecutor;
}

/**
 * Demo: Run agent with example queries
 */
async function runDemo() {
  const agent = await createHederaPolymarketAgent();

  console.log('=' .repeat(80));
  console.log('🤖 HEDERA-POLYMARKET AI AGENT DEMO');
  console.log('=' .repeat(80));
  console.log('');

  // Demo queries
  const queries = [
    {
      title: 'Query 1: Check Hedera Balance',
      input: "What's my HBAR balance?",
    },
    {
      title: 'Query 2: Enter Polymarket Position',
      input: "Enter a $1000 bet on a market at 80% probability. Use the polymarket_bet tool with action='enter', amount_usd=1000, current_prob=0.80",
    },
    {
      title: 'Query 3: Evaluate at Higher Probability',
      input: "The market probability just rose to 86%. Should we take profit? Use polymarket_bet with action='evaluate' and current_prob=0.86",
    },
    {
      title: 'Query 4: Execute Hedge',
      input: "Execute the hedge strategy to lock profits. Use polymarket_bet with action='hedge' and current_prob=0.86",
    }
  ];

  for (const { title, input } of queries) {
    console.log('\n' + '─'.repeat(80));
    console.log(`📋 ${title}`);
    console.log('─'.repeat(80));
    console.log(`💬 User: ${input}\n`);

    try {
      const response = await agent.invoke({ input });
      console.log(`\n🤖 Agent: ${response.output}\n`);
    } catch (error) {
      console.error(`❌ Error: ${error.message}\n`);
    }

    // Pause between queries
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  console.log('=' .repeat(80));
  console.log('✅ Demo Complete!');
  console.log('=' .repeat(80));
}

/**
 * Interactive mode
 */
async function interactiveMode() {
  const agent = await createHederaPolymarketAgent();
  const readline = require('readline');

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('\n🤖 Interactive mode. Type your queries (or "exit" to quit):\n');

  const askQuestion = () => {
    rl.question('You: ', async (input) => {
      if (input.toLowerCase() === 'exit') {
        console.log('👋 Goodbye!');
        rl.close();
        return;
      }

      try {
        const response = await agent.invoke({ input });
        console.log(`\nAgent: ${response.output}\n`);
      } catch (error) {
        console.error(`Error: ${error.message}\n`);
      }

      askQuestion();
    });
  };

  askQuestion();
}

// Run demo or interactive mode
if (require.main === module) {
  const mode = process.argv[2];

  if (mode === 'interactive') {
    interactiveMode().catch(console.error);
  } else {
    runDemo().catch(console.error);
  }
}

module.exports = { createHederaPolymarketAgent, createPolymarketTool };
