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

    vault = Vault.at(get_address("vault"))

    deposit_limit = Wei('2000 ether')
    vault.setDepositLimit(deposit_limit, {"from": deployer})

    balance = vault.setPerformanceFee(1000, {"from": deployer})

    newGov = get_address("gov")

    vault.setGovernance(newGov, {"from": deployer})