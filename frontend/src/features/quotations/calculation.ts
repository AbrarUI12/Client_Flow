const CENT_SCALE = 100n
const QUANTITY_SCALE = 1000n
const PERCENT_SCALE = 10000n

function parseScaled(value: string, decimalPlaces: number): bigint | null {
  const normalized = value.trim()
  const match = normalized.match(/^(\d+)(?:\.(\d*))?$/)
  if (!match) return null
  const fraction = (match[2] || '').padEnd(decimalPlaces, '0').slice(0, decimalPlaces)
  return BigInt(match[1]) * 10n ** BigInt(decimalPlaces) + BigInt(fraction || '0')
}

function roundDivision(value: bigint, divisor: bigint): bigint {
  return (value + divisor / 2n) / divisor
}

export function centsToDecimal(cents: bigint): string {
  const whole = cents / CENT_SCALE
  const fraction = (cents % CENT_SCALE).toString().padStart(2, '0')
  return `${whole}.${fraction}`
}

export type QuotationPreview = {
  lineTotals: string[]
  subtotal: string
  discountAmount: string
  taxAmount: string
  total: string
  complete: boolean
}

export function calculatePreview(
  items: Array<{ quantity: string; unit_price: string }>,
  discountPercent: string,
  taxPercent: string,
): QuotationPreview {
  let complete = true
  const lineTotalCents = items.map((item) => {
    const quantity = parseScaled(item.quantity, 3)
    const priceCents = parseScaled(item.unit_price, 2)
    if (quantity === null || priceCents === null) {
      complete = false
      return 0n
    }
    return roundDivision(quantity * priceCents, QUANTITY_SCALE)
  })
  const subtotalCents = lineTotalCents.reduce((sum, value) => sum + value, 0n)
  const discount = parseScaled(discountPercent, 2)
  const tax = parseScaled(taxPercent, 2)
  if (discount === null || tax === null) complete = false
  const discountCents = roundDivision(subtotalCents * (discount || 0n), PERCENT_SCALE)
  const discountedCents = subtotalCents - discountCents
  const taxCents = roundDivision(discountedCents * (tax || 0n), PERCENT_SCALE)
  const totalCents = discountedCents + taxCents

  return {
    lineTotals: lineTotalCents.map(centsToDecimal),
    subtotal: centsToDecimal(subtotalCents),
    discountAmount: centsToDecimal(discountCents),
    taxAmount: centsToDecimal(taxCents),
    total: centsToDecimal(totalCents),
    complete,
  }
}
