"""Shared background-worker helper for the PySide6 UI.

Every long-running UI action follows the same discipline: the work runs on a
QThread-hosted worker, results come back to the GUI thread via signals, the
live thread/worker/bridge refs are held on a stable object until the thread
has finished (so the QThread is never garbage-collected mid-run), and a
same-key job acts as a re-entrancy guard so a second click can't overwrite a
live thread. This module is that discipline in one place so pages don't have
to hand-roll it per button.
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _FnWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.finished.emit(self._fn())
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller's on_error.
            self.failed.emit(str(exc))


class _FnBridge(QObject):
    def __init__(self, owner, key, on_done, on_error, buttons, busy_text):
        super().__init__()
        self._owner = owner
        self._key = key
        self._on_done = on_done
        self._on_error = on_error
        self._buttons = [(b, b.text()) for b in buttons if b is not None]
        for button, _original in self._buttons:
            button.setEnabled(False)
        if busy_text and self._buttons:
            self._buttons[0][0].setText(busy_text)

    def _restore_buttons(self):
        for button, original in self._buttons:
            button.setText(original)
            button.setEnabled(True)

    @Slot(object)
    def on_finished(self, result):
        self._restore_buttons()
        if self._on_done is not None:
            self._on_done(result)

    @Slot(str)
    def on_failed(self, message):
        self._restore_buttons()
        if self._on_error is not None:
            self._on_error(message)

    @Slot()
    def release_refs(self):
        # Clear refs only after the thread has finished, so the QThread is
        # never garbage-collected while still running (that crashes Qt).
        setattr(self._owner, f"{self._key}_thread", None)
        setattr(self._owner, f"{self._key}_worker", None)
        setattr(self._owner, f"{self._key}_bridge", None)


def run_in_worker(owner, fn, *, on_done=None, on_error=None, buttons=(), busy_text=None, key="_async_job"):
    """Run fn() on a background thread and deliver the result to the GUI thread.

    owner: any stable Python object (a widget, the main window) that outlives
        the job; it holds the live refs under attributes derived from key.
    fn: zero-arg callable executed off the GUI thread. Its return value goes to
        on_done(result); an exception's message goes to on_error(message).
        fn must not touch widgets.
    buttons: controls disabled while the job runs and restored after; the first
        one shows busy_text while running.
    key: jobs sharing an owner+key are mutually exclusive — while one is in
        flight, further calls are ignored and return False.
    """
    if getattr(owner, f"{key}_thread", None) is not None:
        return False

    thread = QThread()
    worker = _FnWorker(fn)
    bridge = _FnBridge(owner, key, on_done, on_error, buttons, busy_text)
    worker.moveToThread(thread)

    worker.finished.connect(bridge.on_finished)
    worker.failed.connect(bridge.on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(bridge.release_refs)
    thread.finished.connect(thread.deleteLater)

    setattr(owner, f"{key}_thread", thread)
    setattr(owner, f"{key}_worker", worker)
    setattr(owner, f"{key}_bridge", bridge)
    thread.start()
    return True
