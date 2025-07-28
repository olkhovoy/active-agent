
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/ActiveAgentToken.sol";

contract ActiveAgentTokenTest is Test {
    ActiveAgentToken public token;
    address public owner;
    uint256 public initialSupply = 1_000_000_000 * (10 ** 18);

    function setUp() public {
        owner = msg.sender;
        token = new ActiveAgentToken(owner);
    }

    function test_InitialSupply() public {
        assertEq(token.totalSupply(), initialSupply, "Initial supply should be 1 billion tokens");
        assertEq(token.balanceOf(owner), initialSupply, "Owner should have the initial supply");
    }

    function test_NameAndSymbol() public {
        assertEq(token.name(), "Active Agent Token", "Token name should be correct");
        assertEq(token.symbol(), "AA", "Token symbol should be correct");
    }

    function test_Mint() public {
        address recipient = address(0x2);
        uint256 amount = 100 * (10 ** 18);
        
        vm.prank(owner);
        token.mint(recipient, amount);

        assertEq(token.balanceOf(recipient), amount, "Recipient balance should be updated after minting");
        assertEq(token.totalSupply(), initialSupply + amount, "Total supply should be updated after minting");
    }

    function test_Burn() public {
        uint256 amount = 50 * (10 ** 18);
        
        vm.prank(owner);
        token.burn(amount);

        assertEq(token.balanceOf(owner), initialSupply - amount, "Owner balance should be updated after burning");
        assertEq(token.totalSupply(), initialSupply - amount, "Total supply should be updated after burning");
    }

    function test_Fail_MintNotOwner() public {
        address notOwner = address(0x3);
        uint256 amount = 100 * (10 ** 18);

        vm.prank(notOwner);
        vm.expectRevert();
        token.mint(notOwner, amount);
    }
} 