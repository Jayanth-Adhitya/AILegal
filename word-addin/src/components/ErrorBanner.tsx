import React from 'react';
import {
  MessageBar,
  MessageBarBody,
  MessageBarTitle,
  Button,
} from '@fluentui/react-components';
import { Dismiss24Regular } from '@fluentui/react-icons';

interface ErrorBannerProps {
  message: string;
  onDismiss: () => void;
}

const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onDismiss }) => {
  return (
    <MessageBar intent="error">
      <MessageBarBody>
        <MessageBarTitle>Error</MessageBarTitle>
        {message}
      </MessageBarBody>
      <Button
        appearance="transparent"
        icon={<Dismiss24Regular />}
        onClick={onDismiss}
      />
    </MessageBar>
  );
};

export default ErrorBanner;
