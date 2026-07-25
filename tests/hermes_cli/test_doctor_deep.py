"""CLI coverage for opt-in deep state database verification."""

import argparse

from hermes_cli.subcommands.doctor import build_doctor_parser


def test_doctor_parser_accepts_deep_flag():
    parser = argparse.ArgumentParser(prog="hermes")
    subparsers = parser.add_subparsers(dest="command")
    build_doctor_parser(subparsers, cmd_doctor=lambda args: args)

    args = parser.parse_args(["doctor", "--deep"])

    assert args.deep is True