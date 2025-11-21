/**
 * Debug script to diagnose Hedera private key issues
 *
 * Run: node debug-key.js
 */

require('dotenv').config();
const { PrivateKey, Client, AccountId, AccountBalanceQuery } = require('@hashgraph/sdk');

const HEDERA_ACCOUNT_ID = process.env.HEDERA_ACCOUNT_ID;
const HEDERA_PRIVATE_KEY = process.env.HEDERA_PRIVATE_KEY;

console.log('🔍 Hedera Private Key Diagnostic\n');
console.log('=' .repeat(60));

// Step 1: Check environment variables
console.log('\n1️⃣  Environment Variables:');
console.log(`   Account ID: ${HEDERA_ACCOUNT_ID || '❌ NOT SET'}`);
console.log(`   Private Key: ${HEDERA_PRIVATE_KEY ? '✅ SET' : '❌ NOT SET'}`);

if (!HEDERA_PRIVATE_KEY) {
  console.error('\n❌ HEDERA_PRIVATE_KEY not found in .env file');
  process.exit(1);
}

// Step 2: Analyze key format
const cleanKey = HEDERA_PRIVATE_KEY.trim().replace(/^0x/, '');
console.log(`   Key length: ${cleanKey.length} characters`);
console.log(`   First 10 chars: ${cleanKey.substring(0, 10)}...`);
console.log(`   Format hint: ${cleanKey.startsWith('302e') ? 'DER format ✅' : 'Unknown format'}`);

// Step 3: Try parsing with different methods
console.log('\n2️⃣  Trying different key formats:\n');

const parsers = [
  {
    name: 'DER format (recommended)',
    fn: () => PrivateKey.fromStringDer(cleanKey)
  },
  {
    name: 'ED25519 raw',
    fn: () => PrivateKey.fromStringED25519(cleanKey)
  },
  {
    name: 'ECDSA',
    fn: () => PrivateKey.fromStringECDSA(cleanKey)
  },
  {
    name: 'Generic parser',
    fn: () => PrivateKey.fromString(cleanKey)
  }
];

let successfulKey = null;
let successfulMethod = null;

for (const parser of parsers) {
  try {
    const key = parser.fn();
    console.log(`   ✅ ${parser.name}: SUCCESS`);
    console.log(`      Public key: ${key.publicKey.toString()}`);

    if (!successfulKey) {
      successfulKey = key;
      successfulMethod = parser.name;
    }
  } catch (error) {
    console.log(`   ❌ ${parser.name}: ${error.message.substring(0, 60)}...`);
  }
}

if (!successfulKey) {
  console.error('\n❌ FAILED: Could not parse private key with any method');
  console.error('\n💡 Solutions:');
  console.error('   1. Copy the FULL private key from Hedera Portal');
  console.error('   2. Make sure it starts with "302e" (DER format)');
  console.error('   3. No spaces or line breaks in the key');
  console.error('   4. Try regenerating key in Hedera Portal if issue persists');
  process.exit(1);
}

console.log(`\n✅ Key parsed successfully using: ${successfulMethod}`);

// Step 4: Test connection to Hedera
console.log('\n3️⃣  Testing Hedera connection:\n');

async function testConnection() {
  try {
    const client = Client.forTestnet();
    const accountId = AccountId.fromString(HEDERA_ACCOUNT_ID);

    client.setOperator(accountId, successfulKey);

    console.log(`   Connecting to Hedera testnet...`);
    const balance = await new AccountBalanceQuery()
      .setAccountId(accountId)
      .execute(client);

    console.log(`   ✅ Connection successful!`);
    console.log(`   💰 Balance: ${balance.hbars.toString()}`);

    client.close();

    // Step 5: Test transaction signature (the issue you're having)
    console.log('\n4️⃣  Testing transaction signature:\n');
    console.log(`   (This is where INVALID_SIGNATURE error occurs)`);

    // Test with a simple transfer to self
    const { TransferTransaction, Hbar } = require('@hashgraph/sdk');
    const testClient = Client.forTestnet();
    testClient.setOperator(accountId, successfulKey);

    try {
      console.log(`   Creating test transaction (0.001 HBAR to self)...`);

      const transaction = new TransferTransaction()
        .addHbarTransfer(accountId, new Hbar(-0.001))
        .addHbarTransfer(accountId, new Hbar(0.001))
        .setTransactionMemo('Test signature')
        .freezeWith(testClient);

      // Sign with the key
      const signedTx = await transaction.sign(successfulKey);

      console.log(`   ✅ Transaction signed successfully!`);
      console.log(`   📝 Transaction ID: ${signedTx.transactionId}`);

      // Try to execute (this will fail if signature is invalid)
      console.log(`   Executing transaction...`);
      const txResponse = await signedTx.execute(testClient);
      const receipt = await txResponse.getReceipt(testClient);

      console.log(`   ✅ Transaction executed successfully!`);
      console.log(`   Status: ${receipt.status}`);
      console.log(`   🔗 HashScan: https://hashscan.io/testnet/transaction/${txResponse.transactionId}`);

      testClient.close();

      console.log('\n' + '='.repeat(60));
      console.log('✅ ALL TESTS PASSED!');
      console.log('='.repeat(60));
      console.log('\n💡 Your key is working correctly. You can now uncomment');
      console.log('   the settlement code in agent.js (line 224-228)');

    } catch (error) {
      console.error(`   ❌ Transaction failed: ${error.message}`);
      console.error('\n💡 This is the INVALID_SIGNATURE error.');
      console.error('   Possible causes:');
      console.error('   1. Private key doesn\'t match account ID');
      console.error('   2. Account doesn\'t have the key as its operator key');
      console.error('   3. Key was copied incorrectly from Portal');
      console.error('\n   Solution: Verify in Hedera Portal that this is the');
      console.error('   correct private key for account ' + HEDERA_ACCOUNT_ID);

      testClient.close();
    }

  } catch (error) {
    console.error(`   ❌ Connection failed: ${error.message}`);
    console.error('\n💡 Check your HEDERA_ACCOUNT_ID and try again');
  }
}

testConnection().catch(console.error);
