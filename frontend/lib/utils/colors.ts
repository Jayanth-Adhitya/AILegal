/**
 * Generate a consistent color for a user based on their ID.
 *
 * @param userId - User ID to generate color for
 * @returns Hex color code
 */
export function getUserColor(userId: string): string {
  // Simple hash function to generate color from user ID
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = userId.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Convert to hue value (0-360)
  const hue = Math.abs(hash % 360);

  // Return HSL color with good saturation and lightness for readability
  return `hsl(${hue}, 70%, 50%)`;
}
