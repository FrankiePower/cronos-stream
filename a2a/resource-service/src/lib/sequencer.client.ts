/**
 * Sequencer Client - HTTP client for CronosStream Sequencer API
 *
 * The Sequencer handles off-chain voucher validation and settlement,
 * enabling high-frequency micropayments without on-chain transactions.
 */

const SEQUENCER_URL = process.env.SEQUENCER_URL ?? 'http://localhost:3000';

export interface VoucherPayload {
  channelId: string;
  amount: string;
  receiver: string;
  sequenceNumber: number;
  timestamp: number;
  userSignature: string;
  purpose?: string;
}

export interface SettleResponse {
  channel: {
    channelId: string;
    owner: string;
    balance: string;
    expiryTimestamp: number;
    sequenceNumber: number;
    userSignature: string;
    sequencerSignature: string;
    signatureTimestamp: number;
    recipients: Array<{ recipientAddress: string; balance: string }>;
  };
}

export interface ChannelState {
  channelId: string;
  owner: string;
  balance: string;
  expiryTimestamp: number;
  sequenceNumber: number;
  recipients: Array<{ recipientAddress: string; balance: string }>;
}

/**
 * Validate a voucher with the Sequencer (read-only check)
 */
export async function validateVoucher(voucher: VoucherPayload): Promise<{ ok: boolean; error?: string }> {
  try {
    const response = await fetch(`${SEQUENCER_URL}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(voucher),
    });

    if (!response.ok) {
      const error = await response.json();
      return { ok: false, error: error.error ?? 'Validation failed' };
    }

    return { ok: true };
  } catch (e) {
    return { ok: false, error: `Sequencer unreachable: ${e}` };
  }
}

/**
 * Settle a voucher with the Sequencer (updates state, co-signs)
 */
export async function settleVoucher(voucher: VoucherPayload): Promise<{ ok: boolean; data?: SettleResponse; error?: string }> {
  try {
    const response = await fetch(`${SEQUENCER_URL}/settle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(voucher),
    });

    if (!response.ok) {
      const error = await response.json();
      return { ok: false, error: error.error ?? 'Settlement failed' };
    }

    const data = await response.json();
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: `Sequencer unreachable: ${e}` };
  }
}

/**
 * Get current channel state from the Sequencer
 */
export async function getChannel(channelId: string): Promise<{ ok: boolean; data?: ChannelState; error?: string }> {
  try {
    const response = await fetch(`${SEQUENCER_URL}/channel/${channelId}`);

    if (!response.ok) {
      const error = await response.json();
      return { ok: false, error: error.error ?? 'Channel not found' };
    }

    const data = await response.json();
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: `Sequencer unreachable: ${e}` };
  }
}

/**
 * Seed (register) a new channel with the Sequencer
 */
export async function seedChannel(params: {
  channelId: string;
  owner: string;
  balance: string;
  expiryTimestamp: number;
}): Promise<{ ok: boolean; data?: ChannelState; error?: string }> {
  try {
    const response = await fetch(`${SEQUENCER_URL}/channel/seed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const error = await response.json();
      return { ok: false, error: error.error ?? 'Seed failed' };
    }

    const data = await response.json();
    return { ok: true, data };
  } catch (e) {
    return { ok: false, error: `Sequencer unreachable: ${e}` };
  }
}
