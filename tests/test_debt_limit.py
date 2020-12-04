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

@pytest.fixture
def vault2(config, Vault, gov, rewards, guardian, token, whale):
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
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    balanceOfWhale = token.balanceOf(whale)
    amount = balanceOfWhale // 4

    strategy = StrategySushiswapPair.deploy(vault, config["pid"], {"from": strategist})
    vault.addStrategy(strategy, amount, 2 ** 256 - 1, 0, {"from": gov})
    vault.deposit(amount, {"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() >= amount

    vault.deposit(amount, {"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() >= amount

    # Let's just increase it a bit, and make sure it works.
    vault.updateStrategyDebtLimit(strategy, amount * 2, {"from": gov})
    strategy.harvest({"from": gov})
    assert strategy.estimatedTotalAssets() >= amount * 2


# def test_decrease_debt_limit(
#     StrategySushiswapPair, vault2, config, token, gov, whale, strategist
# ):
#     token.approve(vault2, 2 ** 256 - 1, {"from": whale})
#     balanceOfWhale = token.balanceOf(whale)
#     amount = balanceOfWhale // 2

#     strategy = StrategySushiswapPair.deploy(vault2, config["pid"], {"from": strategist})
#     vault2.addStrategy(strategy, amount, 2 ** 256 - 1, 0, {"from": gov})
#     vault2.deposit(amount-1, {"from": whale})
#     strategy.harvest({"from": strategist})
#     assert strategy.estimatedTotalAssets() >= amount-1

#     vault2.updateStrategyDebtLimit(strategy, amount // 2, {"from": gov})
#     assert vault2.debtOutstanding(strategy) >= ((amount // 2) - 1)
#     strategy.harvest({"from": strategist})

#     assert strategy.estimatedTotalAssets() >= amount // 2
#     assert token.balanceOf(vault2) >= amount // 2 