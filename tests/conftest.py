import json
import pytest


with open("configurations.json") as f:
    configurations = json.load(f)


@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture(scope="module", params=configurations["vaults"])
def config(request):
    return {**configurations["common"], **request.param}


@pytest.fixture
def vault(config, Vault, gov, rewards, guardian, token, whale):
    vault = Vault.deploy(
        config["want"],
        gov,
        rewards,
        config["name"],
        config["symbol"],
        {"from": guardian},
    )
    vault.setManagementFee(0, {"from": gov})
    deposit = token.balanceOf(whale) / 2
    token.approve(vault, token.balanceOf(whale), {"from": whale})
    vault.deposit(deposit, {"from": whale})
    assert token.balanceOf(vault) == vault.balanceOf(whale) == deposit
    assert vault.totalDebt() == 0  # No connected strategies yet
    return vault


@pytest.fixture
def strategy(config, StrategySushiswapPair, vault, strategist, token, keeper, gov):
    strategy = StrategySushiswapPair.deploy(
        vault, config["pid"], {"from": strategist}
    )
    strategy.setKeeper(keeper, {"from": strategist})
    vault.addStrategy(
        strategy,
        token.totalSupply() / 2,  # Debt limit of 50% total supply
        token.totalSupply() // 1000,  # Rate limt of 0.1% of token supply per block
        50,  # 0.5% performance fee for Strategist
        {"from": gov},
    )
    return strategy


@pytest.fixture
def succ_strategy(config, StrategySushiswapPair, vault, strategist, keeper):
    strategy = StrategySushiswapPair.deploy(
        vault, config["pid"], {"from": strategist}
    )
    strategy.setKeeper(keeper, {"from": strategist})
    return strategy


@pytest.fixture
def token(config, whale, sushiswap, interface, weth, chain):
    weth.approve(sushiswap, 2 ** 256 - 1, {"from": whale})
    pair = interface.SushiswapPair(config["want"])
    tokens = [interface.ERC20(token) for token in [pair.token0(), pair.token1()]]
    amount_in = "500 ether"
    # obtain 1000 eth worth of liquidity
    for token in tokens:
        if token.allowance(whale, sushiswap) == 0:
            token.approve(sushiswap, 2 ** 256 - 1, {"from": whale})

        if token != weth:
            sushiswap.swapExactTokensForTokens(
                amount_in,
                0,
                [weth, token],
                whale,
                chain[-1].timestamp + 1200,
                {"from": whale},
            )

    # obtain want token by adding liquidity
    sushiswap.addLiquidity(
        tokens[0],
        tokens[1],
        tokens[0].balanceOf(whale) if tokens[0] != weth else amount_in,
        tokens[1].balanceOf(whale) if tokens[1] != weth else amount_in,
        0,
        0,
        whale,
        chain[-1].timestamp + 1200,
        {"from": whale},
    )
    return pair

@pytest.fixture
def gov(accounts):
    return accounts[1]


@pytest.fixture
def rewards(gov):
    return gov


@pytest.fixture
def guardian(accounts):
    return accounts[2]


@pytest.fixture
def strategist(accounts):
    return accounts[3]


@pytest.fixture
def keeper(accounts):
    return accounts[4]


@pytest.fixture
def whale(accounts):
    # makerdao eth-a join adapter, this address has a ton of weth
    return accounts.at("0x2F0b23f53734252Bda2277357e97e1517d6B042A", force=True)


@pytest.fixture
def weth(interface):
    return interface.ERC20("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def sushiswap(interface, weth, whale):
    return interface.SushiswapRouter("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")

@pytest.fixture
def chef(interface):
    return interface.SushiChef("0xc2EdaD668740f1aA35E4D8f227fB8E17dcA888Cd")
