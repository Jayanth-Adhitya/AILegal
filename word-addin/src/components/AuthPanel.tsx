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
import { glassStyles } from '../theme';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: tokens.spacingHorizontalL,
  },
  logoContainer: {
    width: '80px',
    height: '80px',
    padding: '16px',
    borderRadius: '24px',
    background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(254, 240, 138, 0.3))',
    boxShadow: '0 12px 48px 0 rgba(251, 191, 36, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.6)',
    marginBottom: tokens.spacingVerticalL,
  },
  logoImage: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    filter: 'drop-shadow(0 4px 6px rgba(251, 191, 36, 0.4))',
  },
  card: {
    width: '100%',
    maxWidth: '400px',
    background: glassStyles.cardBackground,
    backdropFilter: `blur(${glassStyles.glassBlur})`,
    WebkitBackdropFilter: `blur(${glassStyles.glassBlur})`,
    boxShadow: glassStyles.shadowMd,
    borderRadius: tokens.borderRadiusXLarge,
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  cardTitle: {
    color: '#78350F',
    fontWeight: tokens.fontWeightBold,
  },
  cardDescription: {
    color: '#92400E',
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
    color: '#78350F',
  },
  input: {
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
    border: '1px solid rgba(251, 191, 36, 0.3)',
    '&:focus': {
      borderColor: '#F59E0B',
    },
  },
  button: {
    marginTop: tokens.spacingVerticalS,
    background: 'linear-gradient(to bottom, #FCD34D, #FBBF24)',
    border: 'none',
    color: '#78350F',
    fontWeight: tokens.fontWeightSemibold,
    boxShadow: 'inset 0 1px 0 rgba(254, 243, 199, 0.5), ' + glassStyles.shadowMd,
    '&:hover': {
      background: 'linear-gradient(to bottom, #FDE68A, #FCD34D)',
      boxShadow: 'inset 0 1px 0 rgba(254, 243, 199, 0.5), ' + glassStyles.shadowLg,
    },
    '&:disabled': {
      opacity: 0.6,
    },
  },
  error: {
    color: '#DC2626',
    fontSize: tokens.fontSizeBase200,
    backgroundColor: 'rgba(254, 226, 226, 0.5)',
    padding: tokens.spacingVerticalXS,
    borderRadius: tokens.borderRadiusMedium,
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
      <div className={styles.logoContainer}>
        <img
          src="/assets/cirilla-logo.svg"
          alt="Cirilla Logo"
          className={styles.logoImage}
        />
      </div>

      <Card className={styles.card}>
        <CardHeader
          header={
            <Text weight="semibold" size={500} className={styles.cardTitle}>
              Welcome back
            </Text>
          }
          description={
            <Text className={styles.cardDescription}>
              Sign in to access contract analysis features
            </Text>
          }
        />

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <Text className={styles.label}>Email</Text>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              contentBefore={<Person24Regular style={{ color: '#F59E0B' }} />}
              placeholder="you@company.com"
              required
              disabled={isLoading}
              className={styles.input}
            />
          </div>

          <div className={styles.inputGroup}>
            <Text className={styles.label}>Password</Text>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              contentBefore={<LockClosed24Regular style={{ color: '#F59E0B' }} />}
              placeholder="••••••••"
              required
              disabled={isLoading}
              className={styles.input}
            />
          </div>

          {loginError && <Text className={styles.error}>{loginError}</Text>}

          <Button
            className={styles.button}
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
