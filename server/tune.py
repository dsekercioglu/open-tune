import copy
import json
from typing import Dict, List, Union
from common.spsa import Param, SpsaParam, SpsaTest, SpsaTuner
from common.utils import GameRequest, SpsaInfo, TestRequest
import random
from dacite import from_dict

TUNES: Dict[str, SpsaTuner] = {}


def push_test_json(json_str: str) -> str:
    config = json.loads(json_str)
    test_request = from_dict(data_class=TestRequest, data=config)
    push_test(test_request)


def push_result_json(json_str: str):
    config = json.loads(json_str)
    spsa_info = from_dict(data_class=SpsaInfo, data=config)
    push_result(spsa_info)


def push_test(config: SpsaTest, spsa_params: SpsaParam, params: dict[str, Param]):
    global TUNES
    if config.test_id in TUNES:
        return
    param_history = {}
    for name in params:
        param_history[name] = []

    TUNES[config.test_id] = SpsaTuner(
        config, spsa_params, params, 1, [], param_history,
    )


def push_result(info: SpsaInfo):
    global TUNES
    if info.test_id not in TUNES:
        return
    test = TUNES[info.test_id]

    grad = info.l - info.w
    test.t += info.w + info.l + info.d

    a_t = test.spsa_params.a / (test.t + test.spsa_params.A) ** test.spsa_params.alpha
    c_t = test.spsa_params.c / (test.t ** test.spsa_params.gamma)

    gradients = {}
    for name, delta in info.delta.items():
        delta = -1 if delta < 0 else 1
        gradients[name] = grad / (2.0 * delta * c_t)

    for name, param in test.engine_params.items():
        step = gradients[name] * a_t * param.step
        param.value = min(max(param.value - step, param.lowest), param.highest)

        test.hist[name].append(param.value)
    test.iters.append(test.t)


def get_test() -> Union[GameRequest, None]:
    if len(TUNES) == 0:
        return None
    test = TUNES[random.choice(list(TUNES.keys()))]

    c_t = test.spsa_params.c / (test.t ** test.spsa_params.gamma)

    delta = {}
    params = {}

    for name, param in test.engine_params.items():
        delta[name] = (random.randint(0, 1) * 2 - 1) * param.step * c_t
        params[name] = copy.copy(param)

    config = test.config
    return GameRequest(
        config.test_id,
        config.engine,
        config.branch,
        config.book,
        config.hash_size,
        params,
        delta,
        config.tc,
    )


def get_current_test_ids() -> List[str]:
    return list(TUNES.keys())


def get_test_by_id(key: str) -> Union[Dict[str, float], None]:
    if key not in TUNES:
        return None
    params = TUNES[key].engine_params
    return {key: params[key].value for key in params.keys()}
