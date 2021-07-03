"""Job abstract interface."""

from abc import ABC
from abc import abstractmethod
from typing import Union

from braket.devices.device import Device as BraketDevice
from cirq.devices.device import Device as CirqDevice
from qiskit.providers.backend import Backend as QiskitDevice
from qbraid.devices.device import Device

from typing import Callable, Optional
import time

from qiskit.providers.jobstatus import JobStatus, JOB_FINAL_STATES
from qiskit.providers.exceptions import JobTimeoutError

SupportedDevice = Union[BraketDevice, CirqDevice, QiskitDevice]


class AbstractJob(ABC):
    """Class to handle jobs."""

    _async = True

    def __init__(self, device: Device, job_id: str, **kwargs) -> None:
        """Initializes the asynchronous job.
        Args:
            device: the device used to run the job.
            job_id: a unique id in the context of the backend used to run the job.
            kwargs: Any key value metadata to associate with this job.
        """
        self._job_id = job_id
        self._device = device
        self.metadata = kwargs

    def job_id(self) -> str:
        """Return a unique id identifying the job."""
        return self._job_id

    def device(self) -> SupportedDevice:
        """Return the backend where this job was executed."""
        return self._device

    def done(self) -> bool:
        """Return whether the job has successfully run."""
        return self.status() == JobStatus.DONE

    def running(self) -> bool:
        """Return whether the job is actively running."""
        return self.status() == JobStatus.RUNNING

    def cancelled(self) -> bool:
        """Return whether the job has been cancelled."""
        return self.status() == JobStatus.CANCELLED

    def in_final_state(self) -> bool:
        """Return whether the job is in a final job state such as ``DONE`` or ``ERROR``."""
        return self.status() in JOB_FINAL_STATES

    def wait_for_final_state(
        self, timeout: Optional[float] = None, wait: float = 5, callback: Optional[Callable] = None
    ) -> None:
        """Poll the job status until it progresses to a final state such as ``DONE`` or ``ERROR``.
        Args:
            timeout: Seconds to wait for the job. If ``None``, wait indefinitely.
            wait: Seconds between queries.
            callback: Callback function invoked after each query.
                The following positional arguments are provided to the callback function:
                * job_id: Job ID
                * job_status: Status of the job from the last query
                * job: This BaseJob instance
                Note: different subclass might provide different arguments to
                the callback function.
        Raises:
            JobTimeoutError: If the job does not reach a final state before the
                specified timeout.
        """
        if not self._async:
            return
        start_time = time.time()
        status = self.status()
        while status not in JOB_FINAL_STATES:
            elapsed_time = time.time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                raise JobTimeoutError(f"Timeout while waiting for job {self.job_id()}.")
            if callback:
                callback(self.job_id(), status, self)
            time.sleep(wait)
            status = self.status()
        return

    @abstractmethod
    def submit(self):
        """Submit the job to the backend for execution."""
        pass

    @abstractmethod
    def result(self):
        """Return the results of the job."""
        pass

    def cancel(self):
        """Attempt to cancel the job."""
        raise NotImplementedError

    @abstractmethod
    def status(self):
        """Return the status of the job, among the values of ``JobStatus``."""
        pass