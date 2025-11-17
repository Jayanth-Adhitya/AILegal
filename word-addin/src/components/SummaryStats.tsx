import React from 'react';
import {
  makeStyles,
  tokens,
  Text,
  Badge,
  Card,
} from '@fluentui/react-components';
import { AnalysisSummary } from '../types/analysis';

const useStyles = makeStyles({
  card: {
    padding: tokens.spacingHorizontalM,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: tokens.spacingVerticalS,
    marginTop: tokens.spacingVerticalS,
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    gap: tokens.spacingVerticalXS,
  },
  statLabel: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
  },
  statValue: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
  },
  complianceRate: {
    marginTop: tokens.spacingVerticalS,
    textAlign: 'center',
  },
  rateValue: {
    fontSize: tokens.fontSizeHero800,
    fontWeight: tokens.fontWeightBold,
  },
  riskBadge: {
    marginTop: tokens.spacingVerticalS,
    textAlign: 'center',
  },
});

interface SummaryStatsProps {
  summary: AnalysisSummary;
}

const SummaryStats: React.FC<SummaryStatsProps> = ({ summary }) => {
  const styles = useStyles();

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

  const getComplianceColor = (rate: number): string => {
    if (rate >= 90) return tokens.colorPaletteGreenForeground1;
    if (rate >= 70) return tokens.colorPaletteYellowForeground2;
    return tokens.colorPaletteRedForeground1;
  };

  return (
    <Card className={styles.card}>
      <Text weight="semibold" size={400}>
        Analysis Summary
      </Text>

      <div className={styles.complianceRate}>
        <Text className={styles.statLabel}>Compliance Rate</Text>
        <br />
        <Text
          className={styles.rateValue}
          style={{ color: getComplianceColor(summary.compliance_rate) }}
        >
          {summary.compliance_rate.toFixed(1)}%
        </Text>
      </div>

      <div className={styles.riskBadge}>
        <Badge
          appearance="filled"
          color={getRiskColor(summary.overall_risk)}
          size="large"
        >
          Overall Risk: {summary.overall_risk}
        </Badge>
      </div>

      <div className={styles.grid}>
        <div className={styles.stat}>
          <Text className={styles.statLabel}>Total Clauses</Text>
          <Text className={styles.statValue}>{summary.total_clauses}</Text>
        </div>

        <div className={styles.stat}>
          <Text className={styles.statLabel}>Compliant</Text>
          <Text className={styles.statValue} style={{ color: tokens.colorPaletteGreenForeground1 }}>
            {summary.compliant_clauses}
          </Text>
        </div>

        <div className={styles.stat}>
          <Text className={styles.statLabel}>Non-Compliant</Text>
          <Text className={styles.statValue} style={{ color: tokens.colorPaletteRedForeground1 }}>
            {summary.non_compliant_clauses}
          </Text>
        </div>

        <div className={styles.stat}>
          <Text className={styles.statLabel}>Critical Issues</Text>
          <Text className={styles.statValue}>{summary.critical_issues}</Text>
        </div>
      </div>
    </Card>
  );
};

export default SummaryStats;
