// Standardized JSON response helpers

export function ok(res, data) {
  return res.json({ success: true, data });
}

export function created(res, data) {
  return res.status(201).json({ success: true, data });
}

export function error(res, message, status = 500) {
  return res.status(status).json({ success: false, error: message });
}
