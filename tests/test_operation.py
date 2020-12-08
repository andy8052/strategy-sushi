blocks_per_year = 6525 * 365
seconds_per_block = (86400 * 365) / blocks_per_year
sample = 200


def sleep(chain):
    chain.mine(sample)
    chain.sleep(int(sample * seconds_per_block))


def test_vault_deposit(vault, token, whale):
    token.approve(vault, token.balanceOf(whale), {"from": whale})
    before = vault.balanceOf(whale)
    deposit = token.balanceOf(whale)
    vault.deposit(deposit, {"from": whale})
    assert vault.balanceOf(whale) == before + deposit
    assert token.balanceOf(vault) == before + deposit
    assert vault.totalDebt() == 0
    assert vault.pricePerShare() == 10 ** token.decimals()  # 1:1 price


def test_vault_withdraw(vault, token, whale):
    balance = token.balanceOf(whale) + vault.balanceOf(whale)
    vault.withdraw(vault.balanceOf(whale), {"from": whale})
    assert vault.totalSupply() == token.balanceOf(vault) == 0
    assert vault.totalDebt() == 0
    assert token.balanceOf(whale) == balance


def test_strategy_harvest(strategy, vault, token, whale, chain, chef, xsushi, sushiswap, sushimaker, sushiwhale, sushi, weth):
    print("vault:", vault.name())
    user_before = token.balanceOf(whale) + vault.balanceOf(whale)
    token.approve(vault, token.balanceOf(whale), {"from": whale})
    vault.deposit(token.balanceOf(whale), {"from": whale})
    sleep(chain)
    print("share price before:", vault.pricePerShare().to("ether"))
    assert vault.creditAvailable(strategy) > 0
    # give the strategy some debt
    strategy.harvest()
    assert weth.balanceOf(strategy) < 1000000000000
    before = strategy.estimatedTotalAssets()
    print("Est total assets:", before)
    print("Sushi Chef balance:", chef.userInfo(strategy.pid(), strategy))
    # run strategy for some time
    sleep(chain)
    print("Sushi Chef pending:", chef.pendingSushi(strategy.pid(), strategy))
    print("xSushi balance:", xsushi.balanceOf(strategy))
    print("Want balance|strategy:", token.balanceOf(strategy))
    print("Want balance|vault:", token.balanceOf(vault))
    print("debt outstanding:", vault.debtOutstanding())

    # We need to simulate sushi trading to earn some fees. We skip this by sending sushi to the sushi bar
    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    assert weth.balanceOf(strategy) < 1000000000000

    print("Sushi Chef balance:", chef.userInfo(strategy.pid(), strategy))
    sleep(chain)
    print("Sushi Chef pending:", chef.pendingSushi(strategy.pid(), strategy))
    print("xSushi balance:", xsushi.balanceOf(strategy))
    print("Want balance|strategy:", token.balanceOf(strategy))
    print("Want balance|vault:", token.balanceOf(vault))
    print("debt outstanding:", vault.debtOutstanding())

    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    assert weth.balanceOf(strategy) < 1000000000000

    print("Sushi Chef balance:", chef.userInfo(strategy.pid(), strategy))
    sleep(chain)
    print("Sushi Chef pending:", chef.pendingSushi(strategy.pid(), strategy))
    print("xSushi balance:", xsushi.balanceOf(strategy))
    print("Want balance|strategy:", token.balanceOf(strategy))
    print("Want balance|vault:", token.balanceOf(vault))
    print("debt outstanding:", vault.debtOutstanding())

    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    assert weth.balanceOf(strategy) < 1000000000000 

    print("Sushi Chef balance:", chef.userInfo(strategy.pid(), strategy))
    print("Sushi Chef pending:", chef.pendingSushi(strategy.pid(), strategy))
    print("xSushi balance:", xsushi.balanceOf(strategy))
    print("Want balance|strategy:", token.balanceOf(strategy))
    print("Want balance|vault:", token.balanceOf(vault))
    print("debt outstanding:", vault.debtOutstanding())
    after = strategy.estimatedTotalAssets()
    assert after > before
    print("share price after: ", vault.pricePerShare().to("ether"))
    # print(f"implied apy: {(after / before - 1) / (sample / blocks_per_year):.5%}")
    # user withdraws all funds
    vault.withdraw(vault.balanceOf(whale), {"from": whale})
    assert token.balanceOf(whale) >= user_before


def test_strategy_withdraw(strategy, vault, token, whale, gov, chain, sushiwhale, xsushi, sushi):
    user_before = token.balanceOf(whale) + vault.balanceOf(whale)
    token.approve(vault, token.balanceOf(whale), {"from": whale})
    vault.deposit(token.balanceOf(whale), {"from": whale})
    # first harvest adds initial deposits
    sleep(chain)
    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    initial_deposits = strategy.estimatedTotalAssets().to("ether")
    # second harvest secures some profits
    sleep(chain)
    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    sleep(chain)
    strategy.harvest()
    deposits_after_savings = strategy.estimatedTotalAssets().to("ether")
    assert deposits_after_savings > initial_deposits
    # user withdraws funds
    vault.withdraw(vault.balanceOf(whale), {"from": whale})
    assert token.balanceOf(whale) >= user_before
