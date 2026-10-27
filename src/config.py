import json
import yaml


def load_rules(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_declarations(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
