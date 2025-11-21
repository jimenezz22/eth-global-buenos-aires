/**
 * Utility functions for Hedera key parsing
 */

const { PrivateKey } = require('@hashgraph/sdk');

/**
 * Parse Hedera private key from multiple formats
 *
 * Supports:
 * - DER format (302e020100300506032b6570...)
 * - ED25519 raw hex (64 chars)
 * - ECDSA format
 *
 * @param {string} keyString - Private key string from Hedera Portal
 * @returns {PrivateKey} - Parsed private key
 */
function parsePrivateKey(keyString) {
  if (!keyString) {
    throw new Error('Private key is required');
  }

  // Remove whitespace and 0x prefix if present
  const cleanKey = keyString.trim().replace(/^0x/, '');

  // Try different formats in order
  const parsers = [
    // 1. Try DER format (starts with 302e)
    () => {
      if (cleanKey.startsWith('302e')) {
        return PrivateKey.fromStringDer(cleanKey);
      }
      throw new Error('Not DER format');
    },

    // 2. Try ED25519 raw (64 hex chars = 32 bytes)
    () => {
      if (cleanKey.length === 64) {
        return PrivateKey.fromStringED25519(cleanKey);
      }
      throw new Error('Not ED25519 raw format');
    },

    // 3. Try ECDSA
    () => PrivateKey.fromStringECDSA(cleanKey),

    // 4. Try generic parser (last resort)
    () => PrivateKey.fromString(cleanKey)
  ];

  // Try each parser until one works
  let lastError;
  for (const parser of parsers) {
    try {
      const key = parser();
      console.log(`✅ Private key parsed successfully`);
      return key;
    } catch (error) {
      lastError = error;
      continue;
    }
  }

  // If all parsers failed
  throw new Error(
    `Failed to parse private key. Tried multiple formats. ` +
    `Key length: ${cleanKey.length} chars. ` +
    `Last error: ${lastError.message}. ` +
    `\n\nMake sure you copied the FULL private key from Hedera Portal ` +
    `(should start with 302e for DER format or be 64 hex chars for ED25519).`
  );
}

/**
 * Validate that the private key matches the account ID
 *
 * @param {Client} client - Hedera client
 * @param {AccountId} accountId - Expected account ID
 * @param {PrivateKey} privateKey - Private key to validate
 * @returns {boolean} - True if valid
 */
async function validateKeyPair(client, accountId, privateKey) {
  try {
    const publicKey = privateKey.publicKey;
    console.log(`🔑 Public key: ${publicKey.toString()}`);

    // Try a simple query to verify the key works
    const { AccountInfoQuery } = require('@hashgraph/sdk');
    const info = await new AccountInfoQuery()
      .setAccountId(accountId)
      .execute(client);

    console.log(`✅ Key validated for account ${accountId}`);
    return true;
  } catch (error) {
    console.error(`❌ Key validation failed: ${error.message}`);
    return false;
  }
}

module.exports = {
  parsePrivateKey,
  validateKeyPair
};
