"""
All default values used in tfutils
"""

from tfutils.utils import frozendict
import tensorflow as tf

BRANCH_QUEUE_NAME = 'master_w_queue'

DEFAULT_HOST = '/cpu:0'
DEFAULT_DEVICES = ['/gpu:0', '/gpu:1', '/gpu:2', '/gpu:3']

DEFAULT_MODEL_SEED = 0
DEFAULT_LOOP_PARAMS = frozendict()
DEFAULT_DONT_RUN = False
DEFAULT_SKIP_CHECK = False
DEFAULT_LOG_DEVICE_PLACEMENT = False
DEFAULT_TRAIN_THRES_LOSS = 100

DEFAULT_LOAD_PARAMS = frozendict(
        {'do_restore': True, 
         'from_ckpt': None, 
         'to_restore': None, 
         'load_param_dict': None})

DEFAULT_LEARNING_RATE_PARAMS = frozendict({'func': tf.train.exponential_decay})

DEFAULT_LOSS_PARAMS = frozendict(
        {'pred_targets': ['labels'],
         'loss_func': tf.nn.sparse_softmax_cross_entropy_with_logits,
         'agg_func': tf.reduce_mean})

DEFAULT_OPTIMIZER_PARAMS = frozendict(
        {'optimizer_class': tf.train.MomentumOptimizer,
         'momentum': 0.9})

DEFAULT_SAVE_PARAMS = frozendict({'save_metrics_freq': 100,
                                  'save_valid_freq': 3000,
                                  'cache_max_num': 6,
                                  'cache_filters_freq': 3000,
                                  'save_filters_freq': 30000,
                                  'save_initial_filters': True,
                                  'save_to_gfs': (),
                                  'do_save': True})

DEFAULT_PARAMS = frozendict({
    'dont_run': DEFAULT_DONT_RUN,
    'skip_check': DEFAULT_SKIP_CHECK,
    'model_params': frozendict(),
    'train_params': frozendict(),
    'validation_params': frozendict(),
    'log_device_placement': DEFAULT_LOG_DEVICE_PLACEMENT,
    'save_params': frozendict(DEFAULT_SAVE_PARAMS),
    'load_params': frozendict(DEFAULT_LOAD_PARAMS),
    'loss_params': frozendict(DEFAULT_LOSS_PARAMS),
    'optimizer_params': frozendict(DEFAULT_OPTIMIZER_PARAMS),
    'learning_rate_params': frozendict(DEFAULT_LEARNING_RATE_PARAMS),
})


def train_loop(sess, train_targets, num_minibatches=1, **loop_params):
    """Define default minibatch training loop.

    A training loop that performs minibatching with ``num_minibatches``
    minibatches.

    Args:
        sess (tf.Session): Current tensorflow session.
        train_targets (dict): Target operations to be evaluated by ``sess.run``.
            By default, ``base.train_from_params`` inserts the following
            targets to facilitate minibatching:
            * ``__grads__`` (tf.Operation): Accumulates and stores gradients.
            * ``optimizer`` (tf.Operation): Applies and zeros gradients.
        num_minibatches (int): number of minibatches to use.
        **loop_params (mapping): additional, user-defined kwargs to
            be used in the training loop.

    Returns:
        dict: A dictionary containing train targets evaluated by the session.

    """
    assert all([required in targets for targets in train_targets
                for required in ['__grads__', 'optimizer']])

    # Perform minibatching
    range_len = (int)(num_minibatches)
    for minibatch in range(range_len - 1):
        # Accumulate gradient for each minibatch
        sess.run([target['__grads__'] for target in train_targets])

    # Compute final targets (includes zeroing gradient accumulator variable)
    return sess.run(train_targets)
