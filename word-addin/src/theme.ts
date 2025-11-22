import { createLightTheme, Theme } from '@fluentui/react-components';

// Custom Cirilla brand colors matching the website
const cirillaColors = {
  10: '#FFFAEB',   // yellow-50 - lightest
  20: '#FEF3C7',   // yellow-100
  30: '#FDE68A',   // yellow-200
  40: '#FCD34D',   // yellow-300 - primary
  50: '#FBBF24',   // yellow-400
  60: '#F59E0B',   // yellow-500
  70: '#D97706',   // yellow-600
  80: '#B45309',   // yellow-700
  90: '#92400E',   // yellow-800
  100: '#78350F',  // yellow-900 - darkest
  110: '#451A03',  // yellow-950
  120: '#292524',  // dark
  130: '#FEF3C7',  // accent
  140: '#FCD34D',  // accent strong
  150: '#F59E0B',  // accent stronger
  160: '#D97706',  // accent strongest
};

// Create custom Cirilla theme
export const cirillaTheme: Theme = createLightTheme({
  10: cirillaColors[10],
  20: cirillaColors[20],
  30: cirillaColors[30],
  40: cirillaColors[40],
  50: cirillaColors[50],
  60: cirillaColors[60],
  70: cirillaColors[70],
  80: cirillaColors[80],
  90: cirillaColors[90],
  100: cirillaColors[100],
  110: cirillaColors[110],
  120: cirillaColors[120],
  130: cirillaColors[130],
  140: cirillaColors[140],
  150: cirillaColors[150],
  160: cirillaColors[160],
});

// Custom CSS variables for glassmorphism matching website
export const glassStyles = {
  glassBackground: 'rgba(254, 243, 199, 0.7)', // yellow-100 with opacity
  glassBlur: '10px',
  cardBackground: 'rgba(254, 243, 199, 0.7)',
  panelBackground: 'rgba(255, 250, 235, 0.8)',
  shadowMd: '0 -2px 4px rgba(254, 243, 199, 0.5), 0 4px 8px rgba(217, 119, 6, 0.12)',
  shadowLg: '0 -4px 8px rgba(254, 243, 199, 0.5), 0 8px 16px rgba(217, 119, 6, 0.15)',
  gradientBg: 'linear-gradient(to bottom right, #FFFAEB, #FEF3C7, #FDE68A)',
};
