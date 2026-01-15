// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract TUSDC is ERC20, Ownable {
    uint8 private constant DECIMALS = 6;

    constructor(address initialRecipient, uint256 initialSupply) ERC20("TUSDC", "TUSDC") Ownable(msg.sender) {
        if (initialSupply > 0) {
            _mint(initialRecipient, initialSupply);
        }
    }

    function decimals() public pure override returns (uint8) {
        return DECIMALS;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}