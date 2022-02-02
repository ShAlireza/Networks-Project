from typing import List, Dict


class FirewallKind:
    WHITE_LIST = "WHITE_LIST"
    BLACK_LSIT = "BLACK_LIST"


class FirewallRulePolicies:
    DROP = 'drop'
    IGNORE = 'ignore'


class FirewallRule:

    def __init__(self, source_port, destination_port, policy='drop',
                 source_ip='127.0.0.1', destination_ip='127.0.0.1'):
        self.source_ip = source_ip
        self.source_port = source_port
        self.destination_ip = destination_ip
        self.destination_port = destination_port

        self.policy = policy

    def apply(self, data):
        getattr(self, self.policy)(data)

    def drop(self, data):
        return ""

    def ignore(self, data):
        return data


class Firewall:
    def __init__(self, kind=FirewallKind.BLACK_LSIT):
        self.kind = kind
        self.rules: Dict[str, FirewallRule] = {}

    def set_kind(self, kind):
        self.kind = kind

    def set_rule(self, src_ip, src_port, rule):
        self.rules[f'{src_ip}:{src_port}'] = rule

    def get_rule(self, source_port, source_ip='127.0.0.1'):
        return self.rules.get(f'{source_ip}:{source_port}')

    def apply(self, data, source_port, source_ip='127.0.0.1'):
        rule = self.get_rule(
            source_port=source_port,
            source_ip=source_ip
        )

        return rule.apply(data)

    def open_port(self, src_ip, src_port, des_ip, des_port):
        rule = FirewallRule(
            source_ip=src_ip,
            source_port=src_port,
            destination_ip=des_ip,
            destination_port=des_port,
            policy='ignore'
        )

        self.set_rule(src_ip, src_port, rule)

    def close_port(self, src_ip, src_port, des_ip, des_port):
        rule = FirewallRule(
            source_ip=src_ip,
            source_port=src_port,
            destination_ip=des_ip,
            destination_port=des_port,
            policy='drop'
        )

        self.set_rule(src_ip, src_port, rule)

    def status(self):

        status = f"Firewall Kind: {self.kind}\n"
        for source, rule in self.rules.items():
            status += f"{source} --> " \
                f"{rule.destination_ip}:{rule.destination_port}" \
                f"\tpolicy: {rule.policy}\n"

        return status


sar_firewall = Firewall()
