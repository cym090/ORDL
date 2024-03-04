import logging
import sys
import json
# import wandb

cache = {}


def setup_logging(filename):
    stream_handler = logging.StreamHandler(sys.stdout)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(filename=filename,
                        filemode='a',
                        level=logging.INFO,
                        format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%d-%m-%y %H:%M:%S')
    stream_handler.setFormatter(logging.Formatter('%(levelname)s %(asctime)s: %(message)s', '%d-%m-%y %H:%M:%S'))
    logging.getLogger().addHandler(stream_handler)


def setup_logging_stream_only():
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s %(asctime)s: %(message)s',
                        datefmt='%d-%m-%y %H:%M:%S')

def record_history(stage, stats, logdir):
        train_history = []
        test_history = []
        if stage == 'train':
            history = train_history
        else:
            history = test_history

        # if self.wandb:
        #     wandb_log({f'{stage}/{k}': v for k, v in stats.items()})

        history.append(stats)
        json.dump(history,
                  open(f'{logdir}/{stage}_history.json', 'w+'),
                  indent=True)
# def wandb_log(data):
#     global cache
#     cache.update(data)


# def wandb_commit():
#     global cache

#     wandb.log(cache, commit=True)
#     cache = {}