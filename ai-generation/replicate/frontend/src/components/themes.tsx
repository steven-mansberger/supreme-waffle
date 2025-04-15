import { createTheme } from '@mui/material/styles';

// Nord Theme
const nordTheme = createTheme({
  palette: {
    background: {
      default: '#2E3440', // nord0
      paper: '#3B4252', // nord1
    },
    text: {
      primary: '#ECEFF4', // nord6
      secondary: '#D8DEE9', // nord4
    },
    primary: {
      main: '#88C0D0', // nord8
    },
    secondary: {
      main: '#BF616A', // nord11
    },
    // Add more color definitions as needed from the Nord palette
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          '&.MuiButton-containedPrimary': {
            backgroundColor: '#88C0D0',
            color: '#2E3440',
          },
          '&.MuiButton-outlinedPrimary': {
            color: '#88C0D0',
            borderColor: '#88C0D0',
          },
          '&.MuiButton-outlinedSecondary': {
            color: '#BF616A',
            borderColor: '#BF616A',
          },
        },
      },
    },
    // Override other components as needed...
  },
});

// Material Dark Theme
const materialDarkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#BB86FC', // A lighter purple for contrast
    },
    secondary: {
      main: '#03DAC5', // A teal color for secondary actions
    },
    background: {
      default: '#121212', // Dark background color
      paper: '#1E1E1E',   // Slightly lighter for cards, etc.
    },
    text: {
      primary: '#FFFFFF', // White for most text
      secondary: 'rgba(255, 255, 255, 0.7)', // Slightly transparent white for secondary text
      disabled: 'rgba(255, 255, 255, 0.5)', // Even more transparent for disabled states
    },
    error: {
      main: '#CF6679',
    },
    warning: {
      main: '#FB8C00',
    },
    info: {
      main: '#3F51B5',
    },
    success: {
      main: '#4CAF50',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E1E1E',
        },
      },
    },
    MuiGrid2: {
      defaultProps: {
        sx: {
          display: 'flex',
          alignItems: 'center',
        }
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            backgroundColor: '#2B2B2B', // Dark for inputs
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        select: {
          backgroundColor: '#2B2B2B',
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          color: '#BB86FC', // Match with primary color for consistency
        },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: {
          color: '#BB86FC', // Primary color for checkboxes
          '&.Mui-checked': {
            color: '#BB86FC',
          },
        },
      },
    },
  },
});

export { nordTheme, materialDarkTheme };