import React from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Button,
} from '@fluentui/react-components';
import { SignOut24Regular } from '@fluentui/react-icons';
import { User } from '../types/analysis';

const useStyles = makeStyles({
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${tokens.spacingVerticalS} ${tokens.spacingHorizontalM}`,
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    borderBottom: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
  },
  companyName: {
    fontSize: tokens.fontSizeBase200,
    opacity: 0.9,
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
        <Text weight="semibold" size={400}>
          AI Legal Assistant
        </Text>
      </div>

      {user && (
        <div className={styles.userInfo}>
          <div>
            <Text size={200}>{user.email}</Text>
            <br />
            <Text className={styles.companyName}>{user.company_name}</Text>
          </div>
          <Button
            appearance="transparent"
            icon={<SignOut24Regular />}
            onClick={onLogout}
            title="Sign Out"
          />
        </div>
      )}
    </header>
  );
};

export default Header;
