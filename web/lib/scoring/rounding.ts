// Rounding that matches Python exactly. JavaScript's Math.round sends
// every .5 up; Python and numpy send it to the even neighbour, and pandas
// rounds by multiplying first. Using the wrong one changes scores by 0.1.

// Round to a whole number, sending an exact .5 to the even neighbour
// (Python's round(x), numpy's rint): 12.5 -> 12, 13.5 -> 14, -2.5 -> -2.
export function roundHalfEven(x: number): number {
  const floor = Math.floor(x);
  const diff = x - floor;
  if (diff > 0.5) return floor + 1;
  if (diff < 0.5) return floor;
  return floor % 2 === 0 ? floor : floor + 1;
}

// pandas/numpy Series.round(decimals): multiply by 10^decimals, round half
// to even, divide. So 0.35 -> 0.4 (0.35 * 10 is exactly 3.5) while 92.45
// -> 92.4.
export function npRound(x: number, decimals: number): number {
  const factor = 10 ** decimals;
  return roundHalfEven(x * factor) / factor;
}

// pandas Series.quantile(q, interpolation="nearest"): the sorted value at
// position q * (n - 1), with an exact .5 position sent to the even index.
export function quantileNearest(values: number[], q: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[roundHalfEven(q * (sorted.length - 1))];
}
