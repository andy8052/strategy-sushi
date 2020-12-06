def test_migration(chain, vault, strategy, succ_strategy, gov, sushiwhale, xsushi, sushi):
    strategy.harvest()
    chain.mine(100)
    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    strategy.harvest()
    staking = strategy.staking()
    assert staking > 0
    before = strategy.estimatedTotalAssets().to("ether")
    print("estimatedTotalAssets before", before)
    print("pricePerShare", vault.pricePerShare().to("ether"))
    vault.migrateStrategy(strategy, succ_strategy, {"from": gov})
    assert strategy.estimatedTotalAssets().to("ether") == 0
    assert succ_strategy.estimatedTotalAssets().to("ether") >= (before-staking)
    print(
        "estimatedTotalAssets migrate", succ_strategy.estimatedTotalAssets().to("ether")
    )
    print("pricePerShare", vault.pricePerShare().to("ether"))
    sushi.transfer(xsushi, 5000000000000000000000, {"from": sushiwhale})
    succ_strategy.harvest()
    print(
        "estimatedTotalAssets harvest", succ_strategy.estimatedTotalAssets().to("ether")
    )
    print("pricePerShare", vault.pricePerShare().to("ether"))
    assert xsushi.balanceOf(gov) > 0
    assert vault.pricePerShare() < "1.5 ether"
    assert succ_strategy.estimatedTotalAssets() >= before
