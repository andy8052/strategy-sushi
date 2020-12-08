import json

from brownie import StrategySushiswapPair, Vault, accounts, rpc, web3, Wei
from click import secho
from eth_utils import is_checksum_address


def get_address(label):
    addr = input(f"{label}: ")
    if is_checksum_address(addr):
        return addr
    resolved = web3.ens.address(addr)
    if resolved:
        print(f"{addr} -> {resolved}")
        return resolved
    raise ValueError("invalid address or ens")


def main():
    guest = "0xcB16133a37Ef19F90C570B426292BDcca185BF47"
    gov = "0x9b5f6921302cc0560fE2eE72E8fcED9D5D26123d"
    rewards = "0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde"
    configurations = json.load(open("configurations.json"))
    for i, config in enumerate(configurations["vaults"]):
        print(f"[{i}] {config['name']}")
    config = configurations["vaults"][int(input("choose configuration to deploy: "))]
    deployer = accounts.load(input("deployer account: "))

    if input("deploy vault? y/n: ") == "y":
        # gov = get_address("gov")
        # rewards = get_address("rewards")
        vault = Vault.deploy(
            config["want"],
            gov,
            rewards,
            config["name"],
            config["symbol"],
            {"from": deployer, "gas_price": Wei("25 gwei")},
        )
    else:
        vault = Vault.at(get_address("vault"))

    strategy = StrategySushiswapPair.deploy(vault, config["pid"], {"from": deployer, "gas_price": Wei("25 gwei")})

    deposit_limit = Wei('10 ether')
    vault.setDepositLimit(deposit_limit, {"from": deployer, "gas_price": Wei("25 gwei")})
    vault.addStrategy(strategy, deposit_limit, deposit_limit, 1000, {"from": deployer, "gas_price": Wei("25 gwei")})

    gov = "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52"

    vault.setGovernance(gov, {"from": deployer, "gas_price": Wei("25 gwei")})

    secho(
        f"deployed {config['symbol']}\nvault: {vault}\nstrategy: {strategy}\n",
        fg="green",
    )


def migrate():
    assert rpc.is_active()
    vault = Vault.at(get_address("vault"))
    gov = accounts.at(vault.governance(), force=True)
    old_strategy = StrategySushiswapPair.at(get_address("old strategy"))
    new_strategy = StrategySushiswapPair.deploy(
        vault, old_strategy.pid(), {"from": gov}
    )
    print("pricePerShare", vault.pricePerShare().to("ether"))
    print("estimatedTotalAssets", old_strategy.estimatedTotalAssets().to("ether"))
    vault.migrateStrategy(old_strategy, new_strategy, {"from": gov})
    print("pricePerShare", vault.pricePerShare().to("ether"))
    print("estimatedTotalAssets", new_strategy.estimatedTotalAssets().to("ether"))
    keeper = accounts.at(new_strategy.keeper(), force=True)
    for i in range(2):
        new_strategy.harvest({"from": keeper})
        print("pricePerShare", vault.pricePerShare().to("ether"))
        print("estimatedTotalAssets", new_strategy.estimatedTotalAssets().to("ether"))
