import pytest
import brownie

from brownie import Wei


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
    assert token.balanceOf(vault) == 0
    assert vault.totalDebt() == 0
    yield vault


def test_increasing_debt_limit(
    StrategySushiswapPair, vault, config, token, gov, whale, strategist
):
    # Just to make sure we are getting the empty vault
    assert token.balanceOf(vault) == 0

    strategy = StrategySushiswapPair.deploy(vault, config["pid"], {"from": strategist})
    balanceOfWhale = token.balanceOf(whale)
    amount1 = balanceOfWhale // 2
    amount2 = balanceOfWhale // 4

    # Limit the debt to amount1
    vault.addStrategy(strategy, amount1, 2 ** 256 - 1, 0, {"from": gov})
    token.approve(vault, 2 ** 256 - 1, {"from": whale})

    # Deposit amount1 which should be invested immediately
    vault.deposit(amount1, {"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() >= token.balanceOf(strategy)

    # Deposit all that's left and half of it should stay at the vault
    vault.deposit({"from": whale})
    strategy.harvest({"from": strategist})
    # it shold be around amount1 + vault.strategies(strategy).dict()['totalReturns']
    # but there is a rounding error. As long as there is something, we are ok!
    assert token.balanceOf(vault) > 0

    # only gov can increase the limit
    with brownie.reverts():
        vault.updateStrategyDebtLimit(strategy, amount1 + amount2)

    # Let's just increase it a bit, and make sure it works.
    vault.updateStrategyDebtLimit(strategy, amount1 + amount2, {"from": gov})
    strategy.harvest({"from": strategist})
    # 1/4 stays in the vault, but let's do > 0
    assert token.balanceOf(vault) > 0

    # Once we update to 100% of the balance, everything should be invested
    vault.updateStrategyDebtLimit(strategy, balanceOfWhale, {"from": gov})
    strategy.harvest({"from": gov})
    assert (
        token.balanceOf(vault) - vault.strategies(strategy).dict()["totalReturns"] == 0
    )


def test_decrease_debt_limit(
    StrategySushiswapPair, vault, config, token, gov, whale, strategist
):
    # Just to make sure we are getting the empty vault
    assert token.balanceOf(vault) == 0

    strategy = StrategySushiswapPair.deploy(vault, config["pid"], {"from": strategist})
    balanceOfWhale = token.balanceOf(whale)
    amount1 = balanceOfWhale // 2
    amount2 = balanceOfWhale // 4

    # Start by depositing all
    vault.addStrategy(strategy, balanceOfWhale, 2 ** 256 - 1, 0, {"from": gov})
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit({"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() >= token.balanceOf(strategy)

    # Reduce the debt to 75% and some of the tokens should have returned to the vault
    vault.updateStrategyDebtLimit(strategy, amount1 + amount2, {"from": gov})
    #    chain.sleep(10)
    t = strategy.harvest({"from": strategist})
    assert (
        token.balanceOf(vault) - vault.strategies(strategy).dict()["totalReturns"] > 0
    )

    # Update the debt to 50%
    vault.updateStrategyDebtLimit(strategy, amount1, {"from": gov})
    strategy.harvest({"from": strategist})

    # Half should be at the vault and half should be invested
    # Adding 1% for the rounding error
    assert (
        token.balanceOf(vault) - vault.strategies(strategy).dict()["totalReturns"]
        < amount1 * 1.01
    )
    assert strategy.estimatedTotalAssets() == amount1
