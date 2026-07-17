const ACTIVITY_KEY = "activity_days_v1";

function toLocalDateStr(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function getActiveDays(): Set<string> {
  try {
    const raw = localStorage.getItem(ACTIVITY_KEY);
    if (raw) return new Set(JSON.parse(raw) as string[]);
  } catch {}
  return new Set();
}

// Records today as an active day. Cheap and idempotent — safe to call on
// every app load / navigation.
export function recordActiveToday(): void {
  try {
    const today = toLocalDateStr(new Date());
    const days = getActiveDays();
    if (days.has(today)) return;
    days.add(today);
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify([...days]));
  } catch {}
}
