import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("StreamChannelModule", (m) => {
  // Get parameters with defaults for testnet
  const sequencerAddress = m.getParameter("sequencerAddress");
  const initialTokenRecipient = m.getParameter("initialTokenRecipient");
  const initialTokenSupply = m.getParameter("initialTokenSupply", 1_000_000_000_000n); // 1M TUSDC (6 decimals)

  // Deploy TUSDC test token
  const tusdc = m.contract("TUSDC", [initialTokenRecipient, initialTokenSupply]);

  // Deploy StreamChannel with TUSDC and sequencer
  const streamChannel = m.contract("StreamChannel", [tusdc, sequencerAddress]);

  return { tusdc, streamChannel };
});
