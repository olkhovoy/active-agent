
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { ActiveAgentToken } from "../src/ActiveAgentToken.sol";

contract DeployActiveAgentToken is Script {
    function run() external returns (address) {
        vm.startBroadcast();
        ActiveAgentToken token = new ActiveAgentToken(msg.sender);
        vm.stopBroadcast();
        return address(token);
    }
} 