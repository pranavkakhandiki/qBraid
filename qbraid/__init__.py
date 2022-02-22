"""This top level module contains the main qBraid public functionality."""

import pkg_resources
import urllib3

from numpy import random
from cirq.testing import random_circuit as cirq_random_circuit
from qiskit.circuit.exceptions import CircuitError as QiskitCircuitError
from qiskit.circuit.random import random_circuit as qiskit_random_circuit

from qbraid import api
from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid._version import __version__
from qbraid.api import get_devices
from qbraid.exceptions import QbraidError, WrapperError
from qbraid.interface import convert_to_contiguous, to_unitary

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # temporary hack


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


transpiler_entrypoints = _get_entrypoints("qbraid.transpiler")
devices_entrypoints = _get_entrypoints("qbraid.devices")


def circuit_wrapper(circuit, **kwargs):
    r"""circuit_wrapper(circuit, input_qubit_mapping=None, **kwargs)
    Load a class :class:`~qbraid.transpiler.CircuitWrapper` and return the instance.

    This function is used to create a qBraid circuit-wrapper object, which can then be transpiled
    to any supported quantum circuit-building package. The input quantum circuit object must be
    an instance of a circuit object derived from a supported package. qBraid comes with support
    for the following input circuit objects and corresponding quantum circuit-building packages:

    * :class:`braket.circuits.circuit.Circuit`: Amazon Braket is a fully
      mamanged AWS service that helps researchers, scientists, and developers get started
      with quantum computing. Amazon Braket provides on-demand access to managed, high-performance
      quantum circuit simulators, as well as different types of quantum computing hardware.

    * :class:`cirq.circuits.circuit.Circuit`: Cirq is a Python library designed by Google
      for writing, manipulating, and optimizing quantum circuits and running them against
      quantum computers and simulators.

    * :class:`qiskit.circuit.quantumcircuit.QuantumCircuit`: Qiskit is an open-source quantum
      software framework designed by IBM. Supported hardware backends include the IBM Quantum
      Experience.

    All circuit-wrapper objects accept an ``input_qubit_mapping`` argument which gives an explicit
    specification for the ordering of qubits. This argument may be needed for transpiling between
    circuit-building packages that do not share equivalent qubit indexing.

    .. code-block:: python

        cirq_circuit = cirq.Circuit()
        q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]
        ...

    Please refer to the documentation of the individual qbraid circuit wrapper objects to see
    any additional arguments that might be supported.

    Args:
        circuit: a supported quantum circuit object

    Keyword Args:
        input_qubit_mapping: dictionary mapping each qubit object to an index

    """
    package = circuit.__module__.split(".")[0]
    ep = package.lower()

    if package in transpiler_entrypoints:
        circuit_wrapper_class = transpiler_entrypoints[ep].load()
        return circuit_wrapper_class(circuit)

    raise WrapperError(f"{package} is not a supported package.")


def device_wrapper(qbraid_device_id: str, **kwargs):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        qbraid_device_id (str): unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.devices.DeviceLikeWrapper`: a qbraid device wrapper object

    Raises:
        WrapperError: If ``qbraid_id`` is not a valid device reference.
    """
    if qbraid_device_id == "ibm_q_least_busy_qpu":
        qbraid_device_id = api.ibmq_least_busy_qpu()

    device_info = api.get("/public/lab/get-devices", params={"qbraid_id": qbraid_device_id})

    if isinstance(device_info, list):
        if len(device_info) == 0:
            raise WrapperError(f"{qbraid_device_id} is not a valid device ID.")
        device_info = device_info[0]

    if device_info is None:
        raise WrapperError(f"{qbraid_device_id} is not a valid device ID.")

    del device_info["_id"]  # unecessary for sdk
    del device_info["statusRefresh"]
    vendor = device_info["vendor"].lower()
    code = device_info.pop("_code")
    spec = ".local" if code == 0 else ".remote"
    ep = vendor + spec
    device_wrapper_class = devices_entrypoints[ep].load()
    return device_wrapper_class(device_info, **kwargs)


def retrieve_job(qbraid_job_id):
    """Retrieve a job from qBraid API using job ID and return job wrapper object."""
    qbraid_device = device_wrapper(qbraid_job_id.split("-")[0])
    vendor = qbraid_device.vendor.lower()
    if vendor == "google":
        raise ValueError(f"API job retrieval not supported for {qbraid_device.id}")
    ep = vendor + ".job"
    job_wrapper_class = devices_entrypoints[ep].load()
    return job_wrapper_class(qbraid_job_id, device=qbraid_device)


def random_circuit(package, num_qubits=None, depth=None, measure=False):
    """Generate random circuit of arbitrary size and form. If not provided, num_qubits
    and depth are randomly selected in range [2, 4].

    Args:
        package (str): qbraid supported software package
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)
        measure (bool): if True, measure all qubits at the end

    Returns:
        qbraid.transpiler.CircuitWrapper: qbraid circuit wrapper object

    Raises:
        ValueError: when invalid options given

    """
    num_qubits = num_qubits if num_qubits else random.randint(1, 4)
    depth = depth if depth else random.randint(1, 4)
    seed = random.randint(1, 11)
    if package == "qiskit":
        try:
            return qiskit_random_circuit(num_qubits, depth, measure=measure)
        except QiskitCircuitError as err:
            raise ValueError from err
    try:
        random_circuit = cirq_random_circuit(
            num_qubits, n_moments=depth, op_density=1, random_state=seed
        )
    except ValueError as err:
        raise ValueError from err
    if package == "cirq":
        return random_circuit
    elif package == "braket":
        return circuit_wrapper(random_circuit).transpile("braket")
    else:
        raise ValueError(
            f"{package} is not a supported package. \n"
            "Supported packages include qiskit, cirq, braket. "
        )
