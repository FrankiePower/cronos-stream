import { Facilitator, CronosNetwork, PaymentRequirements } from '@crypto.com/facilitator-client';
import { handleX402Payment } from '../lib/middlewares/require.middleware.js';

const NETWORK = (process.env.NETWORK ?? 'cronos-testnet') as CronosNetwork;

/**
 * Service layer for entitlement-gated resources and X402 payment settlement.
 *
 * Responsibilities:
 * - Configure and manage the Facilitator SDK client.
 * - Settle X402 payments and store resulting entitlements.
 * - Produce payloads for entitled (paid) resources.
 *
 * @remarks
 * The Cronos network is resolved from `process.env.NETWORK` and defaults to
 * `"cronos-testnet"`. Ensure this value matches a supported
 * {@link CronosNetwork} at runtime.
 */
export class ResourceService {
  /**
   * Facilitator SDK client configured for the selected Cronos network.
   *
   * @privateRemarks
   * Instantiated eagerly. For improved testability, this may be injected
   * via the constructor instead.
   */
  private facilitator = new Facilitator({ network: NETWORK });

  /**
   * Returns the payload for an entitled user.
   *
   * This method does not perform entitlement checks itself; it assumes
   * payment verification has already been completed upstream.
   *
   * @returns An object representing the unlocked/paid content response.
   */
  getSecretPayload() {
    return { ok: true, response: 'paid content unlocked' };
  }

  /**
   * Settles an X402 payment using the Facilitator SDK.
   *
   * This delegates verification and settlement to the shared
   * {@link handleX402Payment} helper.
   *
   * @param params - Payment settlement parameters.
   * @param params.paymentId - Unique identifier for the payment.
   * @param params.paymentHeader - Encoded payment header provided by the client.
   * @param params.paymentRequirements - Requirements returned by a prior 402 challenge.
   * @returns The settlement result as returned by {@link handleX402Payment}.
   * @throws Re-throws any error raised by the underlying settlement helper or SDK.
   */
  async settlePayment(params: { paymentId: string; paymentHeader: string; paymentRequirements: PaymentRequirements }) {
    return handleX402Payment({
      facilitator: this.facilitator,
      paymentId: params.paymentId,
      paymentHeader: params.paymentHeader,
      paymentRequirements: params.paymentRequirements,
    });
  }

  /**
   * Settles a streaming (voucher-based) payment via the CronosStream Sequencer.
   *
   * This method validates and settles the voucher off-chain, enabling
   * high-frequency micropayments without on-chain transactions.
   *
   * @param params - Voucher settlement parameters.
   * @returns The settlement result from the Sequencer.
   */
  async settleVoucher(params: {
    paymentId: string;
    channelId: string;
    amount: string;
    receiver: string;
    sequenceNumber: number;
    timestamp: number;
    userSignature: string;
  }) {
    // Dynamic import to avoid circular dependencies
    const { settleVoucher: sequencerSettle } = await import('../lib/sequencer.client.js');

    const result = await sequencerSettle({
      channelId: params.channelId,
      amount: params.amount,
      receiver: params.receiver,
      sequenceNumber: params.sequenceNumber,
      timestamp: params.timestamp,
      userSignature: params.userSignature,
    });

    if (result.ok) {
      // Record entitlement for this paymentId
      const { handleVoucherPayment } = await import('../lib/middlewares/require.middleware.js');
      handleVoucherPayment(params.paymentId);
    }

    return result;
  }
}
