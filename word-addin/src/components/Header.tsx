import React from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Button,
} from '@fluentui/react-components';
import { SignOut24Regular } from '@fluentui/react-icons';
import { User } from '../types/analysis';
import { glassStyles } from '../theme';

const useStyles = makeStyles({
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalM}`,
    background: glassStyles.cardBackground,
    backdropFilter: `blur(${glassStyles.glassBlur})`,
    WebkitBackdropFilter: `blur(${glassStyles.glassBlur})`,
    borderBottom: '1px solid rgba(251, 191, 36, 0.2)',
    boxShadow: glassStyles.shadowMd,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  logoImage: {
    width: '28px',
    height: '28px',
    objectFit: 'contain',
    filter: 'drop-shadow(0 2px 4px rgba(251, 191, 36, 0.3))',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  companyName: {
    fontSize: tokens.fontSizeBase200,
    color: '#78350F',
    opacity: 0.8,
  },
  email: {
    color: '#92400E',
    fontWeight: tokens.fontWeightSemibold,
  },
  logoutButton: {
    color: '#92400E',
    '&:hover': {
      backgroundColor: 'rgba(251, 191, 36, 0.2)',
    },
  },
});

interface HeaderProps {
  user: User | null;
  onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  const styles = useStyles();

  return (
    <header className={styles.header}>
      <div className={styles.logo}>
        <img
          src="/assets/cirilla-logo.svg"
          alt="Cirilla"
          className={styles.logoImage}
        />
        <Text weight="semibold" size={400} style={{ color: '#78350F' }}>
          Cirilla
        </Text>
      </div>

      {user && (
        <div className={styles.userInfo}>
          <div>
            <Text size={200} className={styles.email}>{user.email}</Text>
            <br />
            <Text className={styles.companyName}>{user.company_name}</Text>
          </div>
          <Button
            appearance="transparent"
            icon={<SignOut24Regular />}
            onClick={onLogout}
            title="Sign Out"
            className={styles.logoutButton}
          />
        </div>
      )}
    </header>
  );
};

export default Header;
