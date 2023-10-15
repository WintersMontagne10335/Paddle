# Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.
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

from __future__ import annotations

from typing import TYPE_CHECKING

import paddle

from ..profiler import EventGuard
from ..utils import (
    Cache,
    CodeStatus,
    GraphLogger,
    Singleton,
    StepInfoManager,
    log_do,
)
from .interpreter import compile_sir

if TYPE_CHECKING:
    from .symbolic_context import SymbolicTraceContext


def clear_eager_tensor_name(output_tensors):
    for output_tensor in output_tensors:
        output_tensor.name = ""


class FallbackWrapper:
    """
    Used to store and call static graph methods generated by paddle.jit.to_static
    """

    def __init__(self, compiled_fn, SIR):
        self.compiled_fn = compiled_fn
        self.partial_program = None
        self.concrete_program = None
        self.SIR = SIR  # for debug

    def __call__(self, *args, **kwargs):
        with EventGuard(f"FallbackWrapper: {self.SIR.name}"):
            if StepInfoManager().need_back_trace:
                CodeStatus().trace_back_frames()

            log_do(
                2,
                lambda: print("[FallbackWrapper] start run SIR: \n", self.SIR),
            )
            log_do(
                4,
                lambda: print(
                    self.compiled_fn.get_concrete_program(*args, **kwargs)[
                        1
                    ].train_program
                ),
            )
            if self.partial_program is None:
                with EventGuard("FallbackWrapper: call compiled_fn"):
                    outputs = self.compiled_fn(*args, **kwargs)
                    (
                        self.concrete_program,
                        self.partial_program,
                    ) = self.compiled_fn.get_concrete_program(*args, **kwargs)
            else:
                # Speed up Resnet from 0.0068 --> 0.0057
                with EventGuard("FallbackWrapper: call partial_program"):
                    outputs = self.partial_program(*args, **kwargs)

            clear_eager_tensor_name(outputs)
            log_do(
                1,
                lambda: GraphLogger().add_subgraph(
                    self.concrete_program.main_program
                ),
            )
            log_do(
                4,
                lambda: print("[CompileCache] run sir forward success."),
            )
            return outputs


@Singleton
class CompileSIRCache(Cache):
    """
    Cache the compiled function of SIR
    """

    def __init__(self):
        super().__init__(weak=False)

    def key_fn(self, context: SymbolicTraceContext, sir_name: str, **kwargs):
        """
        generate a hash key for a SIR

        Args:
            context: The context to compile
            sir_name: The name of the sir to compile
            build_strategy: The build strategy to compile

        Returns:
            The hash key of the SIR
        """
        sir = context.get_sir(sir_name)
        # NOTE(dev): Is str(sir) a heavy opearation ?
        hash_key = hash(str(sir))
        return hash_key

    def value_fn(self, context: SymbolicTraceContext, sir_name: str, **kwargs):
        """
        Generate static graph function

        Args:
            context: The context to compile
            sir_name: The name of the sir to compile
            build_strategy: The build strategy to compile

        Returns:
            The static graph function
        """
        build_strategy = kwargs.get("build_strategy", None)
        backend = kwargs.get("backend", None)
        return FallbackWrapper(
            paddle.jit.to_static(
                compile_sir(context, sir_name),
                build_strategy=build_strategy,
                backend=backend,
                enable_fallback=False,
            ),
            context.get_sir(sir_name),
        )
