def test_shutdown(vault, token, strategy, chain, sushiwhale, xsushi, sushi):
    chain.mine(100)
    before = token.balanceOf(vault)
    assert strategy.estimatedTotalAssets() == 0
    strategy.harvest()
    assert token.balanceOf(vault) == 0
    assert strategy.estimatedTotalAssets() > before * 0.999
    strategy.setEmergencyExit()
    chain.mine(200)
    print(vault.debtOutstanding(strategy))
    print(token.balanceOf(vault))
    print(token.balanceOf(strategy))
    strategy.harvest()
    print(vault.debtOutstanding(strategy))
    print(token.balanceOf(vault))
    print(token.balanceOf(strategy))

    after = token.balanceOf(vault)
    assert after > before * 0.999
    print(f"loss: {(before - after).to('ether')} {after / before - 1:.18%}")
