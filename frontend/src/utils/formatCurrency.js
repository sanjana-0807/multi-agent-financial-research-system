export function formatCurrency(value) {
  if (value === null || value === undefined) {
    return 'N/A'
  }
  return new Intl.NumberFormat('en-US').format(value)
}
