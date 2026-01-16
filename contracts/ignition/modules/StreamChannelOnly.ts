import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

/**
 * Deployment module for StreamChannel using an existing ERC20 token (e.g., devUSDC)
 */
export default buildModule("StreamChannelOnlyModule", (m) => {
  // Existing token address (e.g., devUSDC on Cronos testnet)
  const tokenAddress = m.getParameter("tokenAddress");

  // Sequencer address for co-signing vouchers
  const sequencerAddress = m.getParameter("sequencerAddress");

  // Deploy StreamChannel with existing token
  const streamChannel = m.contract("StreamChannel", [tokenAddress, sequencerAddress]);

  return { streamChannel };
});
