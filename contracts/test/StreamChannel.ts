import assert from "node:assert/strict";
import { describe, it, beforeEach } from "node:test";
import { network } from "hardhat";
import {
  parseUnits,
  encodePacked,
  keccak256,
  getAddress,
  type Address,
  type WalletClient,
  type PublicClient,
} from "viem";

describe("StreamChannel", async function () {
  const { viem } = await network.connect();
  const publicClient = await viem.getPublicClient();
  const [owner, sequencer, recipient1, recipient2] = await viem.getWalletClients();

  const INITIAL_SUPPLY = parseUnits("1000000", 6); // 1M TUSDC
  const CHANNEL_AMOUNT = parseUnits("1000", 6); // 1000 TUSDC
  const ONE_DAY = 86400n;

  let tusdc: Awaited<ReturnType<typeof viem.deployContract>>;
  let streamChannel: Awaited<ReturnType<typeof viem.deployContract>>;

  async function getBlockTimestamp(): Promise<bigint> {
    const block = await publicClient.getBlock();
    return block.timestamp;
  }

  async function signChannelData(
    signer: WalletClient,
    channelId: `0x${string}`,
    sequenceNumber: bigint,
    timestamp: bigint,
    recipients: Address[],
    amounts: bigint[],
    contractAddress: Address
  ): Promise<`0x${string}`> {
    const domain = {
      name: "StreamChannel",
      version: "1",
      chainId: await publicClient.getChainId(),
      verifyingContract: contractAddress,
    };

    const types = {
      ChannelData: [
        { name: "channelId", type: "bytes32" },
        { name: "sequenceNumber", type: "uint256" },
        { name: "timestamp", type: "uint256" },
        { name: "recipients", type: "address[]" },
        { name: "amounts", type: "uint256[]" },
      ],
    };

    const message = {
      channelId,
      sequenceNumber,
      timestamp,
      recipients,
      amounts,
    };

    return signer.signTypedData({
      domain,
      types,
      primaryType: "ChannelData",
      message,
    });
  }

  beforeEach(async () => {
    // Deploy TUSDC
    tusdc = await viem.deployContract("TUSDC", [owner.account.address, INITIAL_SUPPLY]);

    // Deploy StreamChannel
    streamChannel = await viem.deployContract("StreamChannel", [
      tusdc.address,
      sequencer.account.address,
    ]);

    // Approve StreamChannel to spend owner's tokens
    await tusdc.write.approve([streamChannel.address, INITIAL_SUPPLY], {
      account: owner.account,
    });
  });

  describe("Deployment", () => {
    it("Should set the correct token address", async () => {
      const tokenAddress = await streamChannel.read.token();
      assert.equal(getAddress(tokenAddress), getAddress(tusdc.address));
    });

    it("Should set the correct sequencer address", async () => {
      const sequencerAddress = await streamChannel.read.sequencer();
      assert.equal(getAddress(sequencerAddress), getAddress(sequencer.account.address));
    });
  });

  describe("Open Channel", () => {
    it("Should open a channel with valid signature", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp + ONE_DAY;

      // Get the channel ID first
      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      // Sign the channel opening
      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      // Open the channel
      await streamChannel.write.openChannel(
        [CHANNEL_AMOUNT, expiryTime, timestamp, signature],
        { account: owner.account }
      );

      // Verify channel was created
      const channel = await streamChannel.read.channels([channelId]);
      assert.equal(getAddress(channel[0]), getAddress(owner.account.address)); // owner
      assert.equal(channel[1], CHANNEL_AMOUNT); // balance
      assert.equal(channel[2], expiryTime); // expiryTime
    });

    it("Should emit FundsBlocked event when channel opens", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp + ONE_DAY;

      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await viem.assertions.emitWithArgs(
        streamChannel.write.openChannel(
          [CHANNEL_AMOUNT, expiryTime, timestamp, signature],
          { account: owner.account }
        ),
        streamChannel,
        "FundsBlocked",
        [getAddress(owner.account.address), CHANNEL_AMOUNT, channelId]
      );
    });

    it("Should transfer tokens to contract when channel opens", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp + ONE_DAY;

      const balanceBefore = await tusdc.read.balanceOf([owner.account.address]);

      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await streamChannel.write.openChannel(
        [CHANNEL_AMOUNT, expiryTime, timestamp, signature],
        { account: owner.account }
      );

      const balanceAfter = await tusdc.read.balanceOf([owner.account.address]);
      assert.equal(balanceBefore - balanceAfter, CHANNEL_AMOUNT);
    });

    it("Should reject zero amount", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp + ONE_DAY;

      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        0n,
      ]);

      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await assert.rejects(
        streamChannel.write.openChannel([0n, expiryTime, timestamp, signature], {
          account: owner.account,
        }),
        /Amount must be greater than zero/
      );
    });

    it("Should reject expiry time in the past", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp - 1n;

      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await assert.rejects(
        streamChannel.write.openChannel(
          [CHANNEL_AMOUNT, expiryTime, timestamp, signature],
          { account: owner.account }
        ),
        /Expiry time must be in the future/
      );
    });
  });

  describe("Close Channel by Sequencer", () => {
    let channelId: `0x${string}`;
    let expiryTime: bigint;

    beforeEach(async () => {
      const timestamp = await getBlockTimestamp();
      expiryTime = timestamp + ONE_DAY;

      channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      const signature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await streamChannel.write.openChannel(
        [CHANNEL_AMOUNT, expiryTime, timestamp, signature],
        { account: owner.account }
      );
    });

    it("Should close channel and distribute funds", async () => {
      const timestamp = await getBlockTimestamp();
      const paymentAmount = parseUnits("100", 6);

      const recipients = [recipient1.account.address] as Address[];
      const amounts = [paymentAmount];

      const userSignature = await signChannelData(
        owner,
        channelId,
        1n,
        timestamp,
        recipients,
        amounts,
        streamChannel.address
      );

      const recipient1BalanceBefore = await tusdc.read.balanceOf([recipient1.account.address]);

      await streamChannel.write.finalCloseBySequencer(
        [channelId, 1n, timestamp, recipients, amounts, userSignature],
        { account: sequencer.account }
      );

      const recipient1BalanceAfter = await tusdc.read.balanceOf([recipient1.account.address]);
      assert.equal(recipient1BalanceAfter - recipient1BalanceBefore, paymentAmount);
    });

    it("Should return remaining balance to owner", async () => {
      const timestamp = await getBlockTimestamp();
      const paymentAmount = parseUnits("100", 6);

      const recipients = [recipient1.account.address] as Address[];
      const amounts = [paymentAmount];

      const userSignature = await signChannelData(
        owner,
        channelId,
        1n,
        timestamp,
        recipients,
        amounts,
        streamChannel.address
      );

      const ownerBalanceBefore = await tusdc.read.balanceOf([owner.account.address]);

      await streamChannel.write.finalCloseBySequencer(
        [channelId, 1n, timestamp, recipients, amounts, userSignature],
        { account: sequencer.account }
      );

      const ownerBalanceAfter = await tusdc.read.balanceOf([owner.account.address]);
      const expectedReturn = CHANNEL_AMOUNT - paymentAmount;
      assert.equal(ownerBalanceAfter - ownerBalanceBefore, expectedReturn);
    });

    it("Should reject close from non-sequencer", async () => {
      const timestamp = await getBlockTimestamp();

      const userSignature = await signChannelData(
        owner,
        channelId,
        1n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await assert.rejects(
        streamChannel.write.finalCloseBySequencer(
          [channelId, 1n, timestamp, [], [], userSignature],
          { account: owner.account }
        ),
        /Only sequencer can close the channel/
      );
    });

    it("Should distribute to multiple recipients", async () => {
      const timestamp = await getBlockTimestamp();
      const amount1 = parseUnits("100", 6);
      const amount2 = parseUnits("200", 6);

      const recipients = [recipient1.account.address, recipient2.account.address] as Address[];
      const amounts = [amount1, amount2];

      const userSignature = await signChannelData(
        owner,
        channelId,
        1n,
        timestamp,
        recipients,
        amounts,
        streamChannel.address
      );

      await streamChannel.write.finalCloseBySequencer(
        [channelId, 1n, timestamp, recipients, amounts, userSignature],
        { account: sequencer.account }
      );

      const balance1 = await tusdc.read.balanceOf([recipient1.account.address]);
      const balance2 = await tusdc.read.balanceOf([recipient2.account.address]);

      assert.equal(balance1, amount1);
      assert.equal(balance2, amount2);
    });
  });

  describe("Validate User Signature", () => {
    it("Should validate correct user signature", async () => {
      const timestamp = await getBlockTimestamp();
      const expiryTime = timestamp + ONE_DAY;

      const channelId = await streamChannel.read.getChannelId([
        owner.account.address,
        expiryTime,
        CHANNEL_AMOUNT,
      ]);

      const openSignature = await signChannelData(
        owner,
        channelId,
        0n,
        timestamp,
        [],
        [],
        streamChannel.address
      );

      await streamChannel.write.openChannel(
        [CHANNEL_AMOUNT, expiryTime, timestamp, openSignature],
        { account: owner.account }
      );

      const recipients = [recipient1.account.address] as Address[];
      const amounts = [parseUnits("50", 6)];

      const paymentSignature = await signChannelData(
        owner,
        channelId,
        1n,
        timestamp,
        recipients,
        amounts,
        streamChannel.address
      );

      const isValid = await streamChannel.read.validateUserSignature([
        channelId,
        1n,
        timestamp,
        recipients,
        amounts,
        paymentSignature,
      ]);

      assert.equal(isValid, true);
    });
  });
});
