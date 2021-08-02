from setuptools import setup, find_packages

with open("qbraid/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(
    name="qbraid",
    version=version,
    description="Platform for accessing quantum computers",
    url="https://github.com/qBraid/qBraid",
    author="qBraid Development Team",
    author_email="noreply@qBraid.com",
    license="Restricted",
    packages=find_packages(exclude=["test*"]),
    entry_points={
        "qbraid.transpiler": [
            "braket = qbraid.transpiler.braket:BraketCircuitWrapper",
            "cirq = qbraid.transpiler.cirq:CirqCircuitWrapper",
            "qiskit = qbraid.transpiler.qiskit:QiskitCircuitWrapper",
            "qbraid = qbraid.transpiler.qbraid:QbraidCircuitWrapper"
        ],
        "qbraid.devices": [
            "AWS = qbraid.devices.aws:BraketDeviceWrapper",
            "Google = qbraid.devices.google:CirqSamplerWrapper",
            "IBM = qbraid.devices.ibm:QiskitBackendWrapper"
        ]
    },
    zip_safe=False,
)
