/**
 * Test your specific key format
 */

const { PrivateKey, Client, AccountId, TransferTransaction, Hbar } = require('@hashgraph/sdk');

// Your key from Hedera Portal
const YOUR_KEY = '0x0154df165b8f49d1c6697090554f41048922bcb2fd838b2919d3599c5b22677d';
const YOUR_ACCOUNT = '0.0.7303451';

console.log('Testing your specific key...\n');

async function testKey() {
  // Remove 0x prefix
  const cleanKey = YOUR_KEY.replace(/^0x/, '');
  console.log(`Clean key: ${cleanKey}`);
  console.log(`Length: ${cleanKey.length} chars (should be 64 for ED25519 raw)\n`);

  // Parse as ED25519 (32-byte raw key)
  const privateKey = PrivateKey.fromStringED25519(cleanKey);
  console.log(`✅ Key parsed as ED25519`);
  console.log(`Public key: ${privateKey.publicKey.toString()}\n`);

  // Test connection
  const client = Client.forTestnet();
  const accountId = AccountId.fromString(YOUR_ACCOUNT);
  client.setOperator(accountId, privateKey);

  try {
    console.log('Testing transaction signature...');

    // Minimal transaction to self
    const tx = await new TransferTransaction()
      .addHbarTransfer(accountId, new Hbar(-0.001))
      .addHbarTransfer(accountId, new Hbar(0.001))
      .setTransactionMemo('Key test')
      .execute(client);

    const receipt = await tx.getReceipt(client);

    console.log(`✅ SUCCESS! Transaction executed`);
    console.log(`Status: ${receipt.status}`);
    console.log(`TX ID: ${tx.transactionId}`);
    console.log(`🔗 https://hashscan.io/testnet/transaction/${tx.transactionId}\n`);
    console.log('Your key is working! Update agent.js to use it.');

  } catch (error) {
    console.error(`❌ FAILED: ${error.message}\n`);

    if (error.message.includes('INVALID_SIGNATURE')) {
      console.log('This private key does NOT match account ' + YOUR_ACCOUNT);
      console.log('\nPossible solutions:');
      console.log('1. In Hedera Portal, go to your account');
      console.log('2. Check if there are MULTIPLE keys listed');
      console.log('3. You might need to use a DIFFERENT private key');
      console.log('4. Or verify this is the correct account ID');
    }
  } finally {
    client.close();
  }
}

testKey();
