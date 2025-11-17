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
    backgroundColor: tokens.colorNeutralBackground1,
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
          <Spinner size="large" />
          <Text>Initializing AI Legal Assistant...</Text>
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
