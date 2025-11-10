"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileCheck, AlertCircle, CheckCircle2, TrendingUp } from "lucide-react";
import { AnalysisSummary } from "@/lib/types";
import { getRiskLevelColor } from "@/lib/utils";

interface StatisticsDashboardProps {
  summary: AnalysisSummary;
}

export function StatisticsDashboard({ summary }: StatisticsDashboardProps) {
  const stats = [
    {
      title: "Total Clauses",
      value: summary.total_clauses,
      icon: FileCheck,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "Compliant",
      value: summary.compliant_clauses,
      icon: CheckCircle2,
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      title: "Non-Compliant",
      value: summary.non_compliant_clauses,
      icon: AlertCircle,
      color: "text-red-600",
      bgColor: "bg-red-100",
    },
    {
      title: "Needs Review",
      value: summary.needs_review_clauses,
      icon: TrendingUp,
      color: "text-yellow-600",
      bgColor: "bg-yellow-100",
    },
  ];

  const riskStats = [
    { label: "Critical", value: summary.critical_issues, color: "bg-red-600" },
    { label: "High", value: summary.high_risk_issues, color: "bg-orange-500" },
    { label: "Medium", value: summary.medium_risk_issues, color: "bg-yellow-500" },
    { label: "Low", value: summary.low_risk_issues, color: "bg-green-500" },
  ];

  return (
    <div className="space-y-6">
      {/* Main Statistics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {stat.title}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className={`rounded-lg p-3 ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Compliance Rate & Risk Overview */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Compliance Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-end gap-2">
                <span className="text-5xl font-bold text-gray-900">
                  {(summary.compliance_rate || 0).toFixed(1)}%
                </span>
                <span className="mb-2 text-sm text-gray-600">compliant</span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-green-500 to-green-600 transition-all"
                  style={{ width: `${summary.compliance_rate || 0}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {summary.compliant_clauses || 0} out of {summary.total_clauses || 0} clauses are compliant with your policies
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Risk Overview</span>
              <Badge className={getRiskLevelColor(summary.overall_risk)}>
                {summary.overall_risk} Risk
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {riskStats.map((risk) => (
                <div key={risk.label} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`h-3 w-3 rounded-full ${risk.color}`} />
                    <span className="text-sm font-medium text-gray-900">
                      {risk.label} Risk
                    </span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">
                    {risk.value}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-lg bg-gray-50 p-3">
              <p className="text-xs text-gray-600">
                Overall risk level is determined by the highest risk issues found in the contract.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
