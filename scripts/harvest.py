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
    deployer = accounts.load(input("deployer account: "))

    strategy = StrategySushiswapPair.at(get_address("strat"))

    balance = strategy.estimatedTotalAssets().to("ether")

    strategy.harvest({"from": deployer, "gas_price": Wei("50 gwei")})

    secho(
        f"Total Assets: {balance} SLP\nstrategy: {strategy}\n",
        fg="green",
    )