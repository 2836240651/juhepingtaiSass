export function normalizeSearchText(value) {
  return String(value ?? '').trim().toLowerCase()
}

export function fuzzyMatchRow(row, keyword, fields = []) {
  const q = normalizeSearchText(keyword)
  if (!q) return true
  return fields.some((field) => normalizeSearchText(row?.[field]).includes(q))
}

export function fuzzyMatchAny(row, keyword, resolver) {
  const q = normalizeSearchText(keyword)
  if (!q) return true
  const haystack = normalizeSearchText(resolver(row))
  return haystack.includes(q)
}
