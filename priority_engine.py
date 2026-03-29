

import heapq


class DisasterPriorityQueue:
    """
    Priority queue for ordering disasters by urgency.

    Priority is determined by:
      1. Emergency flag (critical emergencies go first)
      2. Severity score (1–10, higher is more urgent)
      3. Timestamp (older reports get slight priority if tied)

    Uses min-heap with tuple negation to simulate max-heap behavior.
    Internal tuple format: (-emergency_flag, -severity, timestamp, disaster_id, disaster_obj)
    """

    def __init__(self):
        self._heap = []
        self._entry_finder = {}   
        self._REMOVED = "<REMOVED>"

    def push(self, disaster):
        """
        Add a disaster to the priority queue.
        If disaster with same ID exists, it is marked removed and re-added.
        """
        if disaster.id in self._entry_finder:
            self._mark_removed(disaster.id)

        priority_tuple = self._build_priority(disaster)
        entry = [*priority_tuple, disaster]
        self._entry_finder[disaster.id] = entry
        heapq.heappush(self._heap, entry)

    def pop(self):
        """Remove and return the highest priority disaster."""
        while self._heap:
            *_, disaster = heapq.heappop(self._heap)
            if disaster != self._REMOVED:
                del self._entry_finder[disaster.id]
                return disaster
        raise IndexError("Priority queue is empty.")

    def peek(self):
        """Return the highest priority disaster without removing it."""
        for entry in self._heap:
            *_, disaster = entry
            if disaster != self._REMOVED:
                return disaster
        return None

    def remove(self, disaster_id):
        """Lazy deletion — mark an entry as removed."""
        if disaster_id in self._entry_finder:
            self._mark_removed(disaster_id)

    def _mark_removed(self, disaster_id):
        entry = self._entry_finder.pop(disaster_id)
        entry[-1] = self._REMOVED

    def _build_priority(self, disaster):
        """
        Build sortable priority tuple.
        Negation converts min-heap to max-heap behavior.
        """
        emergency_flag = 1 if disaster.is_emergency else 0
        return (
            -emergency_flag,
            -disaster.severity,
            disaster.timestamp.timestamp(),
            disaster.id
        )

    def get_ordered_list(self):
        """
        Return all active disasters sorted by priority (highest first).
        Does NOT mutate the heap.
        """
        active = []
        for entry in self._heap:
            *_, disaster = entry
            if disaster != self._REMOVED:
                active.append(disaster)

        active.sort(key=lambda d: (
            0 if d.is_emergency else 1,
            -d.severity,
            d.timestamp.timestamp()
        ))

        return active

    def size(self):
        return len(self._entry_finder)

    def __len__(self):
        return self.size()

    def is_empty(self):
        return self.size() == 0
