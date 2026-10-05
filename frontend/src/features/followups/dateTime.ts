function partsInTimeZone(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  return Object.fromEntries(parts.map((part) => [part.type, part.value]))
}

export function zonedLocalToIso(localValue: string, timeZone: string): string {
  const [datePart, timePart] = localValue.split('T')
  const [year, month, day] = datePart.split('-').map(Number)
  const [hour, minute] = timePart.split(':').map(Number)
  const wallTimeAsUtc = Date.UTC(year, month - 1, day, hour, minute)
  let guess = wallTimeAsUtc

  for (let attempt = 0; attempt < 2; attempt += 1) {
    const parts = partsInTimeZone(new Date(guess), timeZone)
    const renderedAsUtc = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second),
    )
    guess = wallTimeAsUtc - (renderedAsUtc - guess)
  }

  return new Date(guess).toISOString()
}

export function isoToLocalInput(value: string, timeZone: string): string {
  const parts = partsInTimeZone(new Date(value), timeZone)
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`
}

export function defaultFollowUpLocal(timeZone: string): string {
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000)
  const parts = partsInTimeZone(tomorrow, timeZone)
  return `${parts.year}-${parts.month}-${parts.day}T10:00`
}

export function formatFollowUpDate(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat(undefined, {
    timeZone,
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
