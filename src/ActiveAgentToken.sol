// ... existing code ...
contract ActiveAgentToken is ERC20, Ownable {
    // The total supply is 1 billion tokens with 18 decimal places.
    uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * (10 ** 18);

    constructor(address initialOwner) ERC20("Active Agent Token", "AA") Ownable(initialOwner) {
        _mint(initialOwner, INITIAL_SUPPLY);
    }

    /**
     * @notice Allows the owner to mint new tokens.
     * @param to The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }

    /**
     * @notice Allows the owner to burn tokens.
     * @param amount The amount of tokens to burn.
     */
    function burn(uint256 amount) public onlyOwner {
        _burn(_msgSender(), amount);
    }

    /**
     * @notice Allows the owner to transfer tokens.
     * @param to The address that will receive the transferred tokens.
     * @param amount The amount of tokens to transfer.
     */
    function transfer(address to, uint256 amount) public onlyOwner {
        _transfer(_msgSender(), to, amount);
    }
}
// ... existing code ...