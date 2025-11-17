import React, { useState } from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Button,
  Card,
  Badge,
  Checkbox,
} from '@fluentui/react-components';
import {
  Navigation24Regular,
  Comment24Regular,
  ArrowSwap24Regular,
  ChevronDown24Regular,
  ChevronUp24Regular,
} from '@fluentui/react-icons';
import { ClauseAnalysis } from '../types/analysis';

const useStyles = makeStyles({
  card: {
    padding: tokens.spacingHorizontalS,
    marginBottom: tokens.spacingVerticalXS,
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: tokens.spacingHorizontalS,
    marginBottom: tokens.spacingVerticalXS,
  },
  clauseInfo: {
    flex: 1,
  },
  clauseType: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  riskBadge: {
    marginLeft: 'auto',
  },
  clauseText: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground2,
    marginBottom: tokens.spacingVerticalS,
    maxHeight: '60px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'pre-wrap',
  },
  expandedText: {
    maxHeight: 'none',
  },
  issuesList: {
    marginBottom: tokens.spacingVerticalS,
  },
  issue: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorPaletteRedForeground1,
    marginBottom: tokens.spacingVerticalXXS,
  },
  actions: {
    display: 'flex',
    gap: tokens.spacingHorizontalXS,
    flexWrap: 'wrap',
  },
  expandButton: {
    width: '100%',
    marginTop: tokens.spacingVerticalXS,
  },
  suggestion: {
    backgroundColor: tokens.colorNeutralBackground3,
    padding: tokens.spacingHorizontalS,
    borderRadius: tokens.borderRadiusMedium,
    marginBottom: tokens.spacingVerticalS,
    fontSize: tokens.fontSizeBase200,
  },
  suggestionLabel: {
    fontWeight: tokens.fontWeightSemibold,
    marginBottom: tokens.spacingVerticalXXS,
  },
  compactCard: {
    padding: tokens.spacingHorizontalXS,
  },
});

interface ClauseCardProps {
  clause: ClauseAnalysis;
  selected?: boolean;
  compact?: boolean;
  onSelect?: (selected: boolean) => void;
  onNavigate?: () => void;
  onAddComment?: () => void;
  onApplySuggestion?: () => void;
}

const ClauseCard: React.FC<ClauseCardProps> = ({
  clause,
  selected = false,
  compact = false,
  onSelect,
  onNavigate,
  onAddComment,
  onApplySuggestion,
}) => {
  const styles = useStyles();
  const [expanded, setExpanded] = useState(false);

  const getRiskColor = (risk: string): 'danger' | 'warning' | 'success' | 'informative' => {
    switch (risk) {
      case 'Critical':
        return 'danger';
      case 'High':
        return 'danger';
      case 'Medium':
        return 'warning';
      case 'Low':
        return 'success';
      default:
        return 'informative';
    }
  };

  if (compact) {
    return (
      <Card className={styles.compactCard}>
        <div className={styles.header}>
          <Text weight="semibold" size={300}>
            Clause #{clause.clause_number}
          </Text>
          <Text className={styles.clauseType}>{clause.clause_type}</Text>
          <Badge
            appearance="outline"
            color="success"
            size="small"
            className={styles.riskBadge}
          >
            Compliant
          </Badge>
          {onNavigate && (
            <Button
              appearance="transparent"
              icon={<Navigation24Regular />}
              onClick={onNavigate}
              size="small"
              title="Go to clause"
            />
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card className={styles.card}>
      <div className={styles.header}>
        {onSelect && (
          <Checkbox
            checked={selected}
            onChange={(_, data) => onSelect(!!data.checked)}
          />
        )}
        <div className={styles.clauseInfo}>
          <Text weight="semibold" size={400}>
            Clause #{clause.clause_number}
          </Text>
          <br />
          <Text className={styles.clauseType}>{clause.clause_type}</Text>
        </div>
        <Badge
          appearance="filled"
          color={getRiskColor(clause.risk_level)}
          className={styles.riskBadge}
        >
          {clause.risk_level}
        </Badge>
      </div>

      <div className={`${styles.clauseText} ${expanded ? styles.expandedText : ''}`}>
        {clause.clause_text.substring(0, expanded ? undefined : 150)}
        {!expanded && clause.clause_text.length > 150 && '...'}
      </div>

      {clause.issues.length > 0 && (
        <div className={styles.issuesList}>
          <Text weight="semibold" size={200}>
            Issues:
          </Text>
          {clause.issues.slice(0, expanded ? undefined : 2).map((issue, i) => (
            <div key={i} className={styles.issue}>
              • {issue}
            </div>
          ))}
          {!expanded && clause.issues.length > 2 && (
            <Text size={200} style={{ color: tokens.colorNeutralForeground3 }}>
              ... and {clause.issues.length - 2} more
            </Text>
          )}
        </div>
      )}

      {expanded && clause.suggested_text && (
        <div className={styles.suggestion}>
          <div className={styles.suggestionLabel}>AI Suggested Text:</div>
          {clause.suggested_text.substring(0, 300)}
          {clause.suggested_text.length > 300 && '...'}
        </div>
      )}

      <div className={styles.actions}>
        {onNavigate && (
          <Button
            appearance="subtle"
            icon={<Navigation24Regular />}
            onClick={onNavigate}
            size="small"
          >
            Go to
          </Button>
        )}
        {onAddComment && (
          <Button
            appearance="subtle"
            icon={<Comment24Regular />}
            onClick={onAddComment}
            size="small"
          >
            Comment
          </Button>
        )}
        {onApplySuggestion && clause.suggested_text && (
          <Button
            appearance="primary"
            icon={<ArrowSwap24Regular />}
            onClick={onApplySuggestion}
            size="small"
          >
            Apply Fix
          </Button>
        )}
      </div>

      <Button
        className={styles.expandButton}
        appearance="transparent"
        icon={expanded ? <ChevronUp24Regular /> : <ChevronDown24Regular />}
        onClick={() => setExpanded(!expanded)}
        size="small"
      >
        {expanded ? 'Show Less' : 'Show More'}
      </Button>
    </Card>
  );
};

export default ClauseCard;
