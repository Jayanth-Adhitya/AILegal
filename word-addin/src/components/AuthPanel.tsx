import React, { useState } from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Input,
  Button,
  Spinner,
  Card,
  CardHeader,
} from '@fluentui/react-components';
import { Person24Regular, LockClosed24Regular } from '@fluentui/react-icons';
import { backendAPI } from '../services/backend-api';
import { User } from '../types/analysis';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: tokens.spacingHorizontalL,
  },
  card: {
    width: '100%',
    maxWidth: '400px',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalM,
    padding: tokens.spacingHorizontalM,
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  label: {
    fontWeight: tokens.fontWeightSemibold,
  },
  button: {
    marginTop: tokens.spacingVerticalS,
  },
  error: {
    color: tokens.colorPaletteRedForeground1,
    fontSize: tokens.fontSizeBase200,
  },
});

interface AuthPanelProps {
  onLogin: (user: User) => void;
  onError: (error: string) => void;
}

const AuthPanel: React.FC<AuthPanelProps> = ({ onLogin, onError }) => {
  const styles = useStyles();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setIsLoading(true);

    try {
      const response = await backendAPI.login(email, password);

      if (response.success && response.user) {
        onLogin(response.user);
      } else {
        setLoginError(response.error || 'Login failed. Please check your credentials.');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Network error';
      setLoginError(message);
      onError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <Card className={styles.card}>
        <CardHeader
          header={
            <Text weight="semibold" size={500}>
              Sign In
            </Text>
          }
          description="Sign in to access contract analysis features"
        />

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <Text className={styles.label}>Email</Text>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              contentBefore={<Person24Regular />}
              placeholder="your@email.com"
              required
              disabled={isLoading}
            />
          </div>

          <div className={styles.inputGroup}>
            <Text className={styles.label}>Password</Text>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              contentBefore={<LockClosed24Regular />}
              placeholder="••••••••"
              required
              disabled={isLoading}
            />
          </div>

          {loginError && <Text className={styles.error}>{loginError}</Text>}

          <Button
            className={styles.button}
            appearance="primary"
            type="submit"
            disabled={isLoading || !email || !password}
          >
            {isLoading ? <Spinner size="tiny" /> : 'Sign In'}
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default AuthPanel;
