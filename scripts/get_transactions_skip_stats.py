#!/usr/bin/env python3
#
import sys
import os
import argparse
import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import Libraries.arguments as ar
import Classes.AppConfig as AppConfig
import Classes.TonIndexer as TonIndexer

def run():
    description = 'Performs analysis of transactions skip reason using ton indexer service.'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                    description = description)
    ar.set_standard_args(parser)
    ar.set_config_args(parser)
    ar.set_perf_args(parser)
    ar.set_blockchain_base_args(parser)
    ar.set_period_args(parser, 60)
    ar.set_transactions_filter_args(parser)

    parser.add_argument('-M', '--metric',
                        required=True,
                        type=str,
                        default=None,
                        dest='metric',
                        action='store',
                        help='Metric to collect, matches to compute_skip_reason field  - REQUIRED')

    parser.add_argument('-i', '--info',
                        required=True,
                        type=str,
                        default=None,
                        dest='info',
                        action='store',
                        help='Information to output [rate|count|percentage] - REQUIRED')

    cfg = AppConfig.AppConfig(parser.parse_args())
    ti = TonIndexer.TonIndexer(cfg.config["indexer"], cfg.log)

    start_time = datetime.datetime.now()

    data = ti.get_transactions(cfg.args.workchain, cfg.args.shard, cfg.args.period, cfg)
    data = ti.filter_transactions(data, cfg.args.filters, cfg.config["params"])

    dataset = []
    for element in data:
        if cfg.args.metric == element["compute_skip_reason"]:
            dataset.append(element)

    runtime = (datetime.datetime.now() - start_time)
    if cfg.args.get_time:
        print(runtime.microseconds / 1000)
    elif len(dataset) == 0:
        print(0)
    elif cfg.args.info == "rate":
        print(len(dataset) / cfg.args.period)
    elif cfg.args.info == "count":
        print(len(dataset))
    elif cfg.args.info == "percentage":
        print(len(dataset) / (len(data) / 100))
    else:
        cfg.log.log(os.path.basename(__file__), 1, "Unknown info requested")
        sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    run()
