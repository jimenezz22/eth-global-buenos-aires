/**
 * Hedera AI Agent for Polymarket Betting
 *
 * Connects to Hedera testnet and integrates with Polymarket hedge agent via API.
 * Implements A2A (Agent-to-Agent) communication protocol.
 */

require('dotenv').config();
const {
  Client,
  PrivateKey,
  AccountId,
  AccountBalanceQuery,
  TransferTransaction,
  Hbar,
  TopicCreateTransaction,
  TopicMessageSubmitTransaction
} = require('@hashgraph/sdk');
const axios = require('axios');
const { parsePrivateKey } = require('./utils');

// Configuration
const HEDERA_ACCOUNT_ID = process.env.HEDERA_ACCOUNT_ID;
const HEDERA_PRIVATE_KEY = process.env.HEDERA_PRIVATE_KEY;
const POLYMARKET_API_URL = process.env.POLYMARKET_API_URL || 'http://localhost:5001';
const HEDERA_NETWORK = process.env.HEDERA_NETWORK || 'testnet';

class HederaPolymarketAgent {
  constructor() {
    this.client = null;
    this.accountId = null;
    this.topicId = null; // HCS topic for A2A messages
  }

  /**
   * Initialize Hedera client and verify connection
   */
  async initialize() {
    console.log('🚀 Initializing Hedera Agent...');

    if (!HEDERA_ACCOUNT_ID || !HEDERA_PRIVATE_KEY) {
      throw new Error('Missing Hedera credentials. Check .env file.');
    }

    // Create Hedera client
    this.client = HEDERA_NETWORK === 'mainnet'
      ? Client.forMainnet()
      : Client.forTestnet();

    this.accountId = AccountId.fromString(HEDERA_ACCOUNT_ID);

    // Parse private key (supports DER, ED25519, ECDSA formats)
    const privateKey = parsePrivateKey(HEDERA_PRIVATE_KEY);

    this.client.setOperator(this.accountId, privateKey);

    // Verify connection
    const balance = await new AccountBalanceQuery()
      .setAccountId(this.accountId)
      .execute(this.client);

    console.log(`✅ Connected to Hedera ${HEDERA_NETWORK}`);
    console.log(`📍 Account ID: ${this.accountId}`);
    console.log(`💰 Balance: ${balance.hbars.toString()}`);

    return true;
  }

  /**
   * Create HCS topic for A2A messages
   */
  async createA2ATopic() {
    console.log('\n📡 Creating HCS topic for A2A messages...');

    const transaction = new TopicCreateTransaction()
      .setSubmitKey(this.client.operatorPublicKey)
      .setTopicMemo('Polymarket-Hedera A2A Betting Channel');

    const txResponse = await transaction.execute(this.client);
    const receipt = await txResponse.getReceipt(this.client);
    this.topicId = receipt.topicId;

    console.log(`✅ Topic created: ${this.topicId}`);
    return this.topicId;
  }

  /**
   * Send A2A message via HCS
   */
  async sendA2AMessage(message) {
    if (!this.topicId) {
      throw new Error('Topic not created. Call createA2ATopic() first.');
    }

    const messageStr = JSON.stringify(message);
    console.log(`\n📤 Sending A2A message to topic ${this.topicId}...`);
    console.log(`   Message: ${messageStr.substring(0, 100)}...`);

    const transaction = new TopicMessageSubmitTransaction()
      .setTopicId(this.topicId)
      .setMessage(messageStr);

    const txResponse = await transaction.execute(this.client);
    const receipt = await txResponse.getReceipt(this.client);

    console.log(`✅ A2A message sent (sequence: ${receipt.topicSequenceNumber})`);
    return receipt;
  }

  /**
   * Call Polymarket agent API
   */
  async callPolymarketAgent(action, params = {}) {
    console.log(`\n🎯 Calling Polymarket Agent: ${action}`);

    try {
      const response = await axios.post(`${POLYMARKET_API_URL}/bet`, {
        action,
        ...params
      });

      console.log(`✅ Polymarket response: ${response.data.action}`);
      return response.data;
    } catch (error) {
      console.error(`❌ Polymarket API error: ${error.message}`);
      if (error.response) {
        console.error(`   Status: ${error.response.status}`);
        console.error(`   Error: ${error.response.data.error}`);
      }
      throw error;
    }
  }

  /**
   * Settle payment on Hedera (transfer HBAR)
   */
  async settlePayment(recipientId, amount, memo) {
    console.log(`\n💸 Settling payment on Hedera...`);
    console.log(`   To: ${recipientId}`);
    console.log(`   Amount: ${amount} HBAR`);
    console.log(`   Memo: ${memo}`);

    const transaction = new TransferTransaction()
      .addHbarTransfer(this.accountId, new Hbar(-amount))
      .addHbarTransfer(recipientId, new Hbar(amount))
      .setTransactionMemo(memo);

    const txResponse = await transaction.execute(this.client);
    const receipt = await txResponse.getReceipt(this.client);

    console.log(`✅ Payment settled (status: ${receipt.status})`);
    console.log(`   Transaction ID: ${txResponse.transactionId}`);
    console.log(`   🔗 HashScan: https://hashscan.io/${HEDERA_NETWORK}/transaction/${txResponse.transactionId}`);

    return {
      transactionId: txResponse.transactionId.toString(),
      status: receipt.status.toString(),
      explorerUrl: `https://hashscan.io/${HEDERA_NETWORK}/transaction/${txResponse.transactionId}`
    };
  }

  /**
   * Execute full A2A betting flow
   *
   * 1. Send A2A bet proposal via HCS
   * 2. Call Polymarket agent API
   * 3. If hedge successful, settle payment on Hedera
   */
  async executeBettingFlow(betProposal) {
    console.log('\n' + '='.repeat(60));
    console.log('🤖 Starting A2A Betting Flow');
    console.log('='.repeat(60));

    const {
      action,
      amount_usd,
      current_prob,
      yes_price,
      no_price
    } = betProposal;

    // Step 1: Send A2A proposal via HCS
    const a2aMessage = {
      type: 'bet_proposal',
      from: this.accountId.toString(),
      timestamp: new Date().toISOString(),
      proposal: betProposal
    };

    if (this.topicId) {
      await this.sendA2AMessage(a2aMessage);
    } else {
      console.log('⚠️  HCS topic not created - skipping A2A message (demo mode)');
    }

    // Step 2: Call Polymarket agent
    const polymarketResponse = await this.callPolymarketAgent(action, {
      amount_usd,
      current_prob,
      yes_price,
      no_price
    });

    // Step 3: Settle on Hedera if hedge was successful
    if (polymarketResponse.success &&
        (polymarketResponse.action === 'HEDGE' || polymarketResponse.action === 'ENTRY')) {

      const settlementAmount = polymarketResponse.locked_pnl_usd
        ? Math.abs(polymarketResponse.locked_pnl_usd) / 100  // Convert to HBAR (demo rate)
        : 10; // Default 10 HBAR for demo

      console.log(`\n💰 Settlement ready: ${settlementAmount} HBAR`);
      console.log(`   (Skipping actual transfer for demo - would settle via HTS/HBAR)`);

      // TODO: Uncomment when private key format is verified
      // const settlementResult = await this.settlePayment(
      //   this.accountId,  // Demo: send to self
      //   settlementAmount,
      //   `Polymarket ${polymarketResponse.action} settlement`
      // );

      return {
        success: true,
        polymarket: polymarketResponse,
        settlement: {
          amount: settlementAmount,
          status: 'SIMULATED',
          note: 'Settlement ready - execute with verified private key'
        },
        a2a_message: a2aMessage
      };
    }

    return {
      success: polymarketResponse.success,
      polymarket: polymarketResponse,
      a2a_message: a2aMessage
    };
  }

  /**
   * Cleanup
   */
  async close() {
    if (this.client) {
      this.client.close();
      console.log('\n👋 Hedera client closed');
    }
  }
}

// Demo execution
async function main() {
  const agent = new HederaPolymarketAgent();

  try {
    // Initialize
    await agent.initialize();

    // Create HCS topic (optional - comment out for faster demo)
    // await agent.createA2ATopic();

    // Demo Flow 1: Enter position
    console.log('\n' + '━'.repeat(60));
    console.log('DEMO 1: Enter Position at 80%');
    console.log('━'.repeat(60));

    const result1 = await agent.executeBettingFlow({
      action: 'enter',
      amount_usd: 1000,
      current_prob: 0.80,
      yes_price: 0.80,
      no_price: 0.20
    });

    console.log('\n📊 Result 1:', JSON.stringify(result1, null, 2));

    // Demo Flow 2: Evaluate at 86%
    console.log('\n' + '━'.repeat(60));
    console.log('DEMO 2: Evaluate Position at 86%');
    console.log('━'.repeat(60));

    const result2 = await agent.executeBettingFlow({
      action: 'evaluate',
      current_prob: 0.86,
      yes_price: 0.86,
      no_price: 0.14
    });

    console.log('\n📊 Result 2:', JSON.stringify(result2, null, 2));

    // Demo Flow 3: Execute hedge if recommended
    if (result2.polymarket.action === 'TAKE_PROFIT') {
      console.log('\n' + '━'.repeat(60));
      console.log('DEMO 3: Execute Hedge (Take Profit)');
      console.log('━'.repeat(60));

      const result3 = await agent.executeBettingFlow({
        action: 'hedge',
        current_prob: 0.86,
        yes_price: 0.86,
        no_price: 0.14
      });

      console.log('\n📊 Result 3:', JSON.stringify(result3, null, 2));
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ Demo Complete!');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.error(error.stack);
  } finally {
    await agent.close();
  }
}

// Export for use as module
module.exports = { HederaPolymarketAgent };

// Run demo if executed directly
if (require.main === module) {
  main();
}
