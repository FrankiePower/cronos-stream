import assert from "node:assert/strict";
import { describe, it, beforeEach } from "node:test";
import { network } from "hardhat";
import { parseUnits, getAddress } from "viem";

describe("TUSDC", async function () {
  const { viem } = await network.connect();
  const [owner, user1, user2] = await viem.getWalletClients();

  const INITIAL_SUPPLY = parseUnits("1000000", 6); // 1M TUSDC

  let tusdc: Awaited<ReturnType<typeof viem.deployContract>>;

  beforeEach(async () => {
    tusdc = await viem.deployContract("TUSDC", [owner.account.address, INITIAL_SUPPLY]);
  });

  describe("Deployment", () => {
    it("Should set correct name and symbol", async () => {
      const name = await tusdc.read.name();
      const symbol = await tusdc.read.symbol();
      assert.equal(name, "TUSDC");
      assert.equal(symbol, "TUSDC");
    });

    it("Should have 6 decimals like USDC", async () => {
      const decimals = await tusdc.read.decimals();
      assert.equal(decimals, 6);
    });

    it("Should mint initial supply to recipient", async () => {
      const balance = await tusdc.read.balanceOf([owner.account.address]);
      assert.equal(balance, INITIAL_SUPPLY);
    });

    it("Should set deployer as owner", async () => {
      const contractOwner = await tusdc.read.owner();
      assert.equal(getAddress(contractOwner), getAddress(owner.account.address));
    });
  });

  describe("Minting", () => {
    it("Should allow owner to mint tokens", async () => {
      const mintAmount = parseUnits("1000", 6);

      await tusdc.write.mint([user1.account.address, mintAmount], {
        account: owner.account,
      });

      const balance = await tusdc.read.balanceOf([user1.account.address]);
      assert.equal(balance, mintAmount);
    });

    it("Should reject minting from non-owner", async () => {
      const mintAmount = parseUnits("1000", 6);

      await assert.rejects(
        tusdc.write.mint([user1.account.address, mintAmount], {
          account: user1.account,
        }),
        /OwnableUnauthorizedAccount/
      );
    });
  });

  describe("Transfers", () => {
    it("Should transfer tokens between accounts", async () => {
      const transferAmount = parseUnits("100", 6);

      await tusdc.write.transfer([user1.account.address, transferAmount], {
        account: owner.account,
      });

      const balance = await tusdc.read.balanceOf([user1.account.address]);
      assert.equal(balance, transferAmount);
    });

    it("Should handle approve and transferFrom", async () => {
      const approveAmount = parseUnits("500", 6);
      const transferAmount = parseUnits("200", 6);

      // Owner approves user1
      await tusdc.write.approve([user1.account.address, approveAmount], {
        account: owner.account,
      });

      // Check allowance
      const allowance = await tusdc.read.allowance([
        owner.account.address,
        user1.account.address,
      ]);
      assert.equal(allowance, approveAmount);

      // user1 transfers from owner to user2
      await tusdc.write.transferFrom(
        [owner.account.address, user2.account.address, transferAmount],
        { account: user1.account }
      );

      const balance = await tusdc.read.balanceOf([user2.account.address]);
      assert.equal(balance, transferAmount);
    });
  });

  describe("Zero Initial Supply", () => {
    it("Should deploy with zero initial supply", async () => {
      const zeroSupplyToken = await viem.deployContract("TUSDC", [
        owner.account.address,
        0n,
      ]);

      const totalSupply = await zeroSupplyToken.read.totalSupply();
      assert.equal(totalSupply, 0n);
    });
  });
});
