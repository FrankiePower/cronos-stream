import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
import { configVariable, defineConfig } from "hardhat/config";

export default defineConfig({
  plugins: [hardhatToolboxViemPlugin],
  solidity: {
    profiles: {
      default: {
        version: "0.8.28",
      },
      production: {
        version: "0.8.28",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
        },
      },
    },
  },
  networks: {
    hardhatMainnet: {
      type: "edr-simulated",
      chainType: "l1",
    },
    hardhatOp: {
      type: "edr-simulated",
      chainType: "op",
    },
    sepolia: {
      type: "http",
      chainType: "l1",
      url: configVariable("SEPOLIA_RPC_URL"),
      accounts: [configVariable("SEPOLIA_PRIVATE_KEY")],
    },
    cronosTestnet: {
      type: "http",
      chainType: "l1",
      chainId: 338,
      url: "https://evm-t3.cronos.org/",
      accounts: [configVariable("CRONOS_PRIVATE_KEY")],
      gasPrice: 5000000000000,
    },
    cronosMainnet: {
      type: "http",
      chainType: "l1",
      chainId: 25,
      url: "https://evm.cronos.org/",
      accounts: [configVariable("CRONOS_PRIVATE_KEY")],
      gasPrice: 5000000000000,
    },
  },
  etherscan: {
    apiKey: {
      cronosTestnet: configVariable("CRONOS_EXPLORER_API_KEY"),
      cronosMainnet: configVariable("CRONOS_EXPLORER_API_KEY"),
    },
    customChains: [
      {
        network: "cronosTestnet",
        chainId: 338,
        urls: {
          apiURL: "https://explorer-api.cronos.org/testnet/api/v1/hardhat/contract",
          browserURL: "https://explorer.cronos.org/testnet",
        },
      },
      {
        network: "cronosMainnet",
        chainId: 25,
        urls: {
          apiURL: "https://explorer-api.cronos.org/mainnet/api/v1/hardhat/contract",
          browserURL: "https://explorer.cronos.org",
        },
      },
    ],
  },
});
