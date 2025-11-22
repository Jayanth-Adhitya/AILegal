import React, { useState, useEffect } from 'react';
import {
  Spinner,
  Text,
  makeStyles,
  tokens,
} from '@fluentui/react-components';
import { backendAPI } from './services/backend-api';
import { AppState, User, AnalysisResult } from './types/analysis';
import AuthPanel from './components/AuthPanel';
import AnalysisPanel from './components/AnalysisPanel';
import Header from './components/Header';
import ErrorBanner from './components/ErrorBanner';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(to bottom right, #FFFAEB, #FEF3C7, #FDE68A)',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: tokens.spacingHorizontalM,
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: tokens.spacingVerticalM,
  },
  loadingLogo: {
    width: '80px',
    height: '80px',
    padding: '16px',
    borderRadius: '24px',
    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(254, 240, 138, 0.3))',
    boxShadow: '0 12px 48px 0 rgba(251, 191, 36, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.6)',
  },
  loadingLogoImage: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    filter: 'drop-shadow(0 4px 6px rgba(251, 191, 36, 0.4))',
  },
  loadingText: {
    color: '#78350F',
    fontWeight: tokens.fontWeightSemibold,
  },
});

const App: React.FC = () => {
  const styles = useStyles();

  const [state, setState] = useState<AppState>({
    isAuthenticated: false,
    user: null,
    isAnalyzing: false,
    analysisResult: null,
    selectedClause: null,
    error: null,
  });

  const [isLoading, setIsLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await backendAPI.checkSession();
        if (user) {
          setState((prev) => ({
            ...prev,
            isAuthenticated: true,
            user,
          }));
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogin = (user: User) => {
    setState((prev) => ({
      ...prev,
      isAuthenticated: true,
      user,
      error: null,
    }));
  };

  const handleLogout = async () => {
    try {
      await backendAPI.logout();
    } finally {
      setState({
        isAuthenticated: false,
        user: null,
        isAnalyzing: false,
        analysisResult: null,
        selectedClause: null,
        error: null,
      });
    }
  };

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setState((prev) => ({
      ...prev,
      analysisResult: result,
      isAnalyzing: false,
      error: null,
    }));
  };

  const handleAnalysisStart = () => {
    setState((prev) => ({
      ...prev,
      isAnalyzing: true,
      error: null,
    }));
  };

  const handleError = (error: string) => {
    setState((prev) => ({
      ...prev,
      error,
      isAnalyzing: false,
    }));
  };

  const clearError = () => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingLogo}>
            <img
              src="/assets/cirilla-logo.svg"
              alt="Cirilla Logo"
              className={styles.loadingLogoImage}
            />
          </div>
          <Text className={styles.loadingText}>Initializing Cirilla AI...</Text>
          <Spinner size="large" style={{ color: '#F59E0B' }} />
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <Header user={state.user} onLogout={handleLogout} />

      {state.error && <ErrorBanner message={state.error} onDismiss={clearError} />}

      <div className={styles.content}>
        {!state.isAuthenticated ? (
          <AuthPanel onLogin={handleLogin} onError={handleError} />
        ) : (
          <AnalysisPanel
            user={state.user!}
            analysisResult={state.analysisResult}
            isAnalyzing={state.isAnalyzing}
            onAnalysisStart={handleAnalysisStart}
            onAnalysisComplete={handleAnalysisComplete}
            onError={handleError}
          />
        )}
      </div>
    </div>
  );
};

export default App;
