/**
 * Centralized number formatting utility for OmniForecast.
 * Adjusting these values will update number resolution across the entire frontend.
 */

export interface FormatOptions {
  decimals?: number
  mode?: 'auto' | 'fixed' | 'percent' | 'scientific'
  prefix?: string
  suffix?: string
  showPlus?: boolean
}

/**
 * Formats a number consistently across the application.
 *
 * @param val - The number to format
 * @param options - Formatting configuration
 * @returns A formatted string
 */
export function formatNumber (
  val: number | undefined | null,
  options: FormatOptions = {},
): string {
  // Handle empty or invalid values
  if (val === undefined || val === null || !Number.isFinite(val)) {
    return '—'
  }

  const {
    decimals = 2,
    mode = 'auto',
    prefix = '',
    suffix = '',
    showPlus = false,
  } = options

  let formatted = ''

  // 1. Percentage Mode
  if (mode === 'percent') {
    formatted = `${val.toFixed(decimals)}%`
  } else if (mode === 'scientific' || (mode === 'auto' && Math.abs(val) > 0 && Math.abs(val) < 0.001)) {
    formatted = val.toExponential(Math.max(2, decimals))
  } else {
    // If it's an integer and we're in auto mode, don't force decimals unless requested
    const minDecimals = mode === 'fixed' ? decimals : (Number.isInteger(val) ? 0 : decimals)

    formatted = val.toLocaleString(undefined, {
      minimumFractionDigits: minDecimals,
      maximumFractionDigits: decimals,
    })
  }

  const sign = showPlus && val > 0 ? '+' : ''
  return `${prefix}${sign}${formatted}${suffix}`
}

/**
 * Specialized formatter for metrics like MAE/RMSE
 */
export function formatMetric (val: number | undefined | null, name?: string): string {
  if (name === 'MAPE') {
    return formatNumber(val, { decimals: 1, mode: 'percent' })
  }
  if (name === 'R²') {
    return formatNumber((val ?? 0) * 100, { decimals: 0, suffix: '%' })
  }
  if (name === 'MAE') {
    return formatNumber(val, { decimals: 2, prefix: '±' })
  }

  // Default metric formatting
  return formatNumber(val, { decimals: 2 })
}

/**
 * Formats file sizes for display
 */
export function formatFileSize (bytes: number): string {
  if (bytes === 0) {
    return '0 Bytes'
  }
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
