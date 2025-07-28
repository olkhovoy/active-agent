
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ActiveAgentToken
 * @author Alexander Olkhovoy & Gemini 1.5 Pro
 * @notice The core token for the Active Agent Protocol.
 * This is the initial version, a standard ERC20 token.
 * The Proof-of-Coherence (PoC) minting logic will be added in a future version.
 */
contract ActiveAgentToken is ERC20, Ownable {
    // The total supply is 1 billion tokens with 18 decimal places.
    uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * (10 ** 18);

    constructor(address initialOwner) ERC20("Active Agent Token", "AA") Ownable(initialOwner) {
        _mint(initialOwner, INITIAL_SUPPLY);
    }

    /**
     * @notice Allows the owner to mint new tokens.
     * @dev This is a temporary function for initial setup and testing.
     * In the final version, this will be replaced by the Proof-of-Coherence (PoC) minting mechanism.
     * @param to The address to mint tokens to.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @notice Allows any user to burn their own tokens, reducing the total supply.
     * @param amount The amount of tokens to burn.
     */
    function burn(uint256 amount) public {
        _burn(msg.sender, amount);
    }
} 