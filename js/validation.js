/**
 * Data validation for Compact Gantt tasks.
 * Ported from compact_gantt validators.
 */
const DataValidator = {
  validateTask(task, usedIds) {
    const errors = [];
    const id = this._num(task.id);
    const row = this._num(task.row);
    const lane = this._num(task.lane);

    if (id == null || id <= 0) {
      errors.push("Task ID must be positive");
    }
    if (id != null && id > 0 && usedIds.has(id)) {
      errors.push("Task ID must be unique");
    }

    const name = task.name != null ? String(task.name).trim() : "";
    if (name === "") {
      errors.push("Task name cannot be empty");
    }

    if (!this.isValidDate(task.start)) {
      errors.push("Invalid start date format (should be YYYY-MM-DD)");
    }
    if (!this.isValidDate(task.end)) {
      errors.push("Invalid end date format (should be YYYY-MM-DD)");
    }

    if (this.isValidDate(task.start) && this.isValidDate(task.end)) {
      if (new Date(task.end) < new Date(task.start)) {
        errors.push("End date must be on or after start date");
      }
    }

    if (row == null || row <= 0) {
      errors.push("Row number must be positive");
    }

    if (lane == null || lane <= 0) {
      errors.push("Lane number must be positive");
    }

    return errors;
  },

  validateAll(tasks) {
    const usedIds = new Set();
    const results = [];

    tasks.forEach((task, index) => {
      const errors = this.validateTask(task, usedIds);
      if (errors.length > 0) {
        results.push({ index: index + 1, task, errors });
      }
      const id = this._num(task.id);
      if (id != null && id > 0) usedIds.add(id);
    });

    return results;
  },

  isValidDate(dateString) {
    if (dateString == null || dateString === "") return false;
    const s = String(dateString).trim();
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(s)) return false;
    const date = new Date(s);
    return !isNaN(date.getTime());
  },

  _num(v) {
    if (v == null || v === "") return null;
    const n = Number(v);
    return isNaN(n) ? null : n;
  }
};
