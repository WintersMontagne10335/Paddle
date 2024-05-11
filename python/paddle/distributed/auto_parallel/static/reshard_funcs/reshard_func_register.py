# Copyright (c) 2024 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .base_reshard_func import register_reshard_func
from .p_to_r_reshard_func import (
    PToRReshardFunction,
    PToRReshardFunctionCrossMesh,
)
from .r_to_s_reshard_func import (
    RToSReshardFunction,
    RToSReshardFunctionCrossMesh,
)
from .s_to_r_reshard_func import (
    SToRReshardFunction,
    SToRReshardFunctionCrossMesh,
)
from .same_status_reshard_func import SameStatusReshardFunction


def register_reshard_funcs():
    register_reshard_func(PToRReshardFunction())
    register_reshard_func(PToRReshardFunctionCrossMesh())
    register_reshard_func(RToSReshardFunction())
    register_reshard_func(RToSReshardFunctionCrossMesh())
    register_reshard_func(SameStatusReshardFunction())
    register_reshard_func(SToRReshardFunction())
    register_reshard_func(SToRReshardFunctionCrossMesh())


register_reshard_funcs()
