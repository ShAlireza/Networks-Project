from typing import List


class FirewallKind:
    WHITE_LIST = "WHITE_LIST"
    BLACK_LSIT = "BLACK_LIST"


class FirewallRulePolicies:
    DROP = 'drop'


class FirewallRule:

    def __init__(self, source_port, destination_port, policy='drop',
                 source_ip='127.0.0.1', destination_ip='127.0.0.1'):
        self.source_ip = source_ip
        self.source_port = source_port
        self.destination_ip = destination_ip
        self.destination_port = destination_port

        self.policy = policy

    def apply(self, packet_transporter):
        getattr(self, self.policy)(packet_transporter)

    def drop(self, packet_transporter):
        pass


class Firewall:
    def __init__(self, kind=FirewallKind.BLACK_LSIT):
        self.kind = kind
        self.rules: List[FirewallRule] = []

    def set_kind(self, kind):
        self.kind = kind

    def add_rule(self, rule):
        self.rules.append(rule)

    def get_rules(self, source_port, source_ip='127.0.0.1'):
        rules = []
        for rule in self.rules:
            if rule.source_ip == source_ip and rule.source_port == source_port:
                rules.append(rule)

        return rules

    def firewall(self, packet_transporter):
        pass
