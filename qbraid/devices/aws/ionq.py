# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""
Module defining Utility functions to be able to run IonQ device from AWS
"""
import pytket
from braket.circuits import Circuit
from pytket._tket.circuit._library import _TK1_to_RzRx  # type: ignore
from pytket.passes import RebaseCustom
from pytket.predicates import (
    CompilationUnit,
    GateSetPredicate,
    MaxNQubitsPredicate,
    NoClassicalControlPredicate,
    NoFastFeedforwardPredicate,
    NoMidMeasurePredicate,
    NoSymbolsPredicate,
)

import qbraid

HARMONY_MAX_QUBITS = 11

ionq_gates = {
    pytket.circuit.OpType.X,
    pytket.circuit.OpType.Y,
    pytket.circuit.OpType.Z,
    pytket.circuit.OpType.Rx,
    pytket.circuit.OpType.Ry,
    pytket.circuit.OpType.Rz,
    pytket.circuit.OpType.H,
    pytket.circuit.OpType.S,
    pytket.circuit.OpType.Sdg,
    pytket.circuit.OpType.T,
    pytket.circuit.OpType.Tdg,
    pytket.circuit.OpType.V,
    pytket.circuit.OpType.Vdg,
    pytket.circuit.OpType.Measure,
    pytket.circuit.OpType.noop,
    pytket.circuit.OpType.SWAP,
    pytket.circuit.OpType.CX,
    pytket.circuit.OpType.ZZPhase,
    pytket.circuit.OpType.XXPhase,
    pytket.circuit.OpType.YYPhase,
    pytket.circuit.OpType.ZZMax,
    pytket.circuit.OpType.Barrier,
}

preds = [
    NoClassicalControlPredicate(),
    NoFastFeedforwardPredicate(),
    NoMidMeasurePredicate(),
    NoSymbolsPredicate(),
    GateSetPredicate(ionq_gates),
    MaxNQubitsPredicate(HARMONY_MAX_QUBITS),
]

ionq_rebase_pass = RebaseCustom(
    ionq_gates,
    pytket.Circuit(),  # cx_replacement (irrelevant)
    _TK1_to_RzRx,
)  # tk1_replacement


def braket_ionq_compilation(circuit: Circuit) -> Circuit:
    """
    Compiles a Braket circuit to a Braket circuit that can run on IonQ Harmony.

    Args:
        circuit (Circuit): The input Braket circuit to be compiled.

    Returns:
        Circuit: The compiled Braket circuit that can run on IonQ Harmony.
    """
    tk_circuit = qbraid.circuit_wrapper(circuit).transpile("pytket")
    cu = CompilationUnit(tk_circuit, preds)
    ionq_rebase_pass.apply(cu)
    assert cu.check_all_predicates()
    return qbraid.circuit_wrapper(tk_circuit).transpile("braket")
